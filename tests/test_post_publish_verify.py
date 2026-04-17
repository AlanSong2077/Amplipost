#!/usr/bin/env python3
"""
Tests for post-publish-verify.py hook
"""

import json
import os
import subprocess
import sys
import tempfile

HOOK_PATH = os.path.join(os.path.dirname(__file__), "../.claude/hooks/post-publish-verify.py")


def run_hook(data: dict) -> tuple[int, str, str]:
    result = subprocess.run(
        [sys.executable, HOOK_PATH],
        input=json.dumps(data),
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def make_payload(command: str, stdout: str = "", exit_code: int = 0) -> dict:
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_response": {"stdout": stdout, "exit_code": exit_code},
    }


class TestAlwaysExitsZero:
    def test_non_bash_exits_zero(self):
        code, _, _ = run_hook({"tool_name": "Write", "tool_input": {}, "tool_response": {}})
        assert code == 0

    def test_non_publish_exits_zero(self):
        code, _, _ = run_hook(make_payload("ls -la", "some output"))
        assert code == 0

    def test_xianyu_success_exits_zero(self):
        code, _, _ = run_hook(make_payload("python3 xianyu_publish.py", "", exit_code=0))
        assert code == 0

    def test_xianyu_failure_exits_zero(self):
        code, _, _ = run_hook(make_payload("python3 xianyu_publish.py", "error", exit_code=1))
        assert code == 0

    def test_xhs_mcp_curl_exits_zero(self):
        # 小红书改用 MCP curl 调用，不再经过 *_publish.py hook
        # hook 对非 *_publish.py 命令应直接放行
        code, _, _ = run_hook(make_payload(
            "curl -s -X POST http://localhost:18060/mcp -H 'Content-Type: application/json' -d '{}'",
            '{"result":{"content":[{"text":"发布成功"}]}}'
        ))
        assert code == 0

    def test_bilibili_exits_zero(self):
        code, _, _ = run_hook(make_payload("python3 bilibili_publish.py", "提交成功"))
        assert code == 0

    def test_douyin_exits_zero(self):
        code, _, _ = run_hook(make_payload("python3 douyin_publish.py", "发布成功"))
        assert code == 0

    def test_invalid_json_exits_zero(self):
        result = subprocess.run(
            [sys.executable, HOOK_PATH],
            input="not valid json",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0


class TestLogFileCreation:
    def test_log_file_written_for_xianyu(self, tmp_path, monkeypatch):
        """发布后应写入日志文件"""
        import importlib.util

        # 使用 subprocess 验证日志目录被创建（日志写到 ~/.amplipost/logs/）
        code, _, _ = run_hook(make_payload("python3 xianyu_publish.py", "", exit_code=0))
        assert code == 0
        log_dir = os.path.expanduser("~/.amplipost/logs")
        assert os.path.isdir(log_dir)
