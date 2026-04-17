---
name: xhs-publisher
description: 小红书（RED/XHS）自动发布助手。基于 xiaohongshu-mcp MCP Server，通过 HTTP API 调用实现发布、搜索、互动等功能。底层使用 go-rod + CDP 直连 Chromium，反风控能力强，已验证稳定运行一年无封号。触发词：发布小红书、发小红书笔记、发XHS、发布到小红书、小红书自动发布、xhs publisher。
---

# 小红书发布 Skill（xiaohongshu-mcp 版）

## 架构说明

本 Skill 不再使用 Playwright Python 脚本，改为调用 **xiaohongshu-mcp MCP Server**（Go + go-rod + CDP）。

```
content-coordinator Agent
        │
        │  HTTP POST http://localhost:18060/mcp
        ▼
xiaohongshu-mcp MCP Server（本地 Go 进程，端口 18060）
        │
        │  Chrome DevTools Protocol
        ▼
Chromium 浏览器（无头模式）
        │
        ▼
小红书网页端
```

**为什么换掉 Playwright：**
- Playwright 走 WebDriver 协议，`navigator.webdriver=true` 特征被小红书风控识别
- xiaohongshu-mcp 走 CDP 直连，无 WebDriver 特征，行为模拟更接近真人
- 原作者自用一年无封号，已有大量用户验证

---

## 前置：启动 xiaohongshu-mcp 服务

### 首次登录（只需一次）

```bash
# macOS Apple Silicon
cd $XHS_MCP_DIR
./xiaohongshu-login-darwin-arm64

# 或从源码运行
go run cmd/login/main.go
```

扫码登录后，Cookie 自动保存到 `cookies.json`，后续无需重复登录。

### 启动 MCP 服务

```bash
cd $XHS_MCP_DIR

# 无头模式（生产推荐）
go run .

# 有界面模式（调试用）
go run . -headless=false
```

服务启动后监听 `http://localhost:18060`，保持运行。

### 验证服务状态

```bash
curl -s -X POST http://localhost:18060/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"check_login_status","arguments":{}},"id":1}'
```

---

## MCP 工具完整列表（共 13 个）

| 工具名 | 说明 | 必填参数 |
|--------|------|---------|
| `check_login_status` | 检查登录状态 | 无 |
| `get_login_qrcode` | 获取登录二维码（Base64） | 无 |
| `delete_cookies` | 重置登录状态 | 无 |
| `publish_content` | 发布图文笔记 | title, content, images |
| `publish_with_video` | 发布视频笔记 | title, content, video |
| `list_feeds` | 获取首页推荐列表 | 无 |
| `search_feeds` | 搜索笔记 | keyword |
| `get_feed_detail` | 获取笔记详情+评论 | feed_id, xsec_token |
| `post_comment_to_feed` | 发表评论 | feed_id, xsec_token, content |
| `reply_comment_in_feed` | 回复评论 | feed_id, xsec_token, content |
| `like_feed` | 点赞/取消点赞 | feed_id, xsec_token |
| `favorite_feed` | 收藏/取消收藏 | feed_id, xsec_token |
| `user_profile` | 获取用户主页 | user_id, xsec_token |

---

## 发布图文（核心调用）

### HTTP 直接调用

```bash
curl -s -X POST http://localhost:18060/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "publish_content",
      "arguments": {
        "title": "笔记标题（≤20字）",
        "content": "正文内容（200-300字）",
        "images": ["/absolute/path/to/image.jpg"],
        "tags": ["标签1", "标签2"]
      }
    },
    "id": 1
  }'
```

### Python 调用封装

```python
import subprocess, json

def xhs_publish(title: str, content: str, images: list[str] = None, tags: list[str] = None) -> dict:
    """
    调用 xiaohongshu-mcp 发布图文笔记
    images: 本地绝对路径列表，如 ["/Users/xxx/img.jpg"]；无图则传空列表（文字配图模式）
    tags: 话题标签列表，如 ["AI工具", "效率"]
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": "publish_content",
            "arguments": {
                "title": title,
                "content": content,
                "images": images or [],
                "tags": tags or []
            }
        },
        "id": 1
    }
    result = subprocess.run(
        ["curl", "-s", "-X", "POST", "http://localhost:18060/mcp",
         "-H", "Content-Type: application/json",
         "-d", json.dumps(payload)],
        capture_output=True, text=True, timeout=120
    )
    return json.loads(result.stdout)
```

### 无图发布（文字配图模式）

xiaohongshu-mcp 的 `publish_content` 要求至少 1 张图片。无图时有两种处理方式：

**方式 A（推荐）：先用 generate_images.py 生成配图，再传给 MCP**

```bash
# 1. 生成配图
python3 publishers/douyin-publisher/scripts/generate_images.py \
  --topic "{主题}" --title "{标题}" \
  --point1 "{要点1}" --point2 "{要点2}" --point3 "{要点3}"
# 输出图片路径到 ~/.catpaw/douyin_images/

# 2. 用生成的图片发布到小红书
# 将图片路径传入 images 参数
```

**方式 B：使用旧版 Playwright 脚本的文字配图模式（降级备用）**

```bash
python3 publishers/xhs-publisher/scripts/xhs_publish.py \
  --title "{title}" --content "{content}"
```

---

## 发布成功判断

MCP 返回的 JSON 中：
- `result.content[0].text` 包含 `"发布成功"` 或 `"success"` → 成功
- `result.isError: true` → 失败，读取 `result.content[0].text` 获取错误原因

```python
def is_publish_success(response: dict) -> bool:
    try:
        result = response.get("result", {})
        if result.get("isError"):
            return False
        text = result.get("content", [{}])[0].get("text", "")
        return "发布成功" in text or "success" in text.lower()
    except Exception:
        return False
```

---

## 检查服务是否运行

```bash
# 快速检查
curl -s http://localhost:18060/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{},"id":0}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if 'result' in d else 'FAIL')"
```

如果服务未运行，Agent 应提示用户：
```
xiaohongshu-mcp 服务未启动。请在新终端窗口执行：
cd $XHS_MCP_DIR && go run .
```

---

## 登录态管理

- Cookie 存储路径：`$XHS_MCP_DIR/cookies.json`
- Cookie 过期后，重新运行登录工具扫码即可
- **重要**：同一账号不能同时在多个网页端登录，使用 MCP 期间不要在浏览器登录同一账号

---

## 常见问题

详见 `references/troubleshooting.md`
