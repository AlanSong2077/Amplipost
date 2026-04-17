#!/usr/bin/env python3
"""
Tests for pre-publish-check.py hook
"""

import json
import subprocess
import sys
import os

HOOK_PATH = os.path.join(os.path.dirname(__file__), "../.claude/hooks/pre-publish-check.py")


def run_hook(data: dict) -> tuple[int, str, str]:
    """Run the hook with given JSON input, return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, HOOK_PATH],
        input=json.dumps(data),
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


class TestNonBashTool:
    def test_non_bash_tool_passes(self):
        code, out, err = run_hook({"tool_name": "Write", "tool_input": {"content": "高仿商品"}})
        assert code == 0


class TestNonPublishCommand:
    def test_non_publish_command_passes(self):
        code, out, err = run_hook({"tool_name": "Bash", "tool_input": {"command": "ls -la"}})
        assert code == 0


class TestXianyuBannedWords:
    def test_blocks_gaofang(self):
        code, out, err = run_hook({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 xianyu_publish.py --title '高仿耐克'"},
        })
        assert code == 2
        assert "高仿" in err

    def test_blocks_a_huo(self):
        code, out, err = run_hook({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 xianyu_publish.py --desc 'A货包包'"},
        })
        assert code == 2
        assert "A货" in err

    def test_blocks_quanwang_zuidi(self):
        code, out, err = run_hook({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 xianyu_publish.py --desc '全网最低价'"},
        })
        assert code == 2
        assert "全网最低" in err

    def test_blocks_jiahuo(self):
        code, out, err = run_hook({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 xianyu_publish.py --desc '假货'"},
        })
        assert code == 2

    def test_blocks_fangpin(self):
        code, out, err = run_hook({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 xianyu_publish.py --desc '仿品手表'"},
        })
        assert code == 2

    def test_clean_xianyu_passes(self):
        code, out, err = run_hook({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 xianyu_publish.py --title 'iPhone 15 二手出售'"},
        })
        assert code == 0


class TestBilibiliEmojiBlock:
    def test_blocks_emoji_in_bilibili(self):
        code, out, err = run_hook({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 bilibili_publish.py --title '好文章\U0001F600'"},
        })
        assert code == 2
        assert "emoji" in err

    def test_clean_bilibili_passes(self):
        code, out, err = run_hook({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 bilibili_publish.py --title '好文章'"},
        })
        assert code == 0


class TestDouyinEmojiBlock:
    def test_blocks_emoji_in_douyin(self):
        code, out, err = run_hook({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 douyin_publish.py --title '热门内容\u2764'"},
        })
        assert code == 2

    def test_clean_douyin_passes(self):
        code, out, err = run_hook({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 douyin_publish.py --title '热门内容'"},
        })
        assert code == 0


class TestExtremeWords:
    def test_extreme_word_warning_not_blocked(self):
        # 小红书改用 MCP，此处改用闲鱼命令测试极限词检测（极限词检测是通用的）
        code, out, err = run_hook({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 xianyu_publish.py --title '全网最好的产品'"},
        })
        assert code == 0
        data = json.loads(out)
        assert data["continue"] is True
        assert "全网最好" in data["hookSpecificOutput"]["additionalContext"]

    def test_quanwang_diyiming_warning(self):
        # 小红书改用 MCP，此处改用抖音命令测试极限词检测
        code, out, err = run_hook({
            "tool_name": "Bash",
            "tool_input": {"command": "python3 douyin_publish.py --title '全网第一品牌'"},
        })
        assert code == 0

    def test_invalid_json_input_passes(self):
        result = subprocess.run(
            [sys.executable, HOOK_PATH],
            input="not valid json",
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
