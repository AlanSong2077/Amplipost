# Amplipost

多平台内容营销自动化系统。支持闲鱼、小红书、B站、抖音四个平台的内容生成与自动发布。

## 核心约束

**Skill 脚本只调用，不修改。** `publishers/*/scripts/*.py` 和 `publishers/*/SKILL.md` 均为只读。

## Skill 脚本路径

优先使用 openclaw 安装路径，不存在时回退本地路径：

```
# 小红书：不使用脚本，改用 xiaohongshu-mcp MCP Server（见下方）

# 其他平台（闲鱼/B站/抖音）：
~/.openclaw/skills/xianyu-publisher/scripts/xianyu_publish.py
~/.openclaw/skills/bilibili-publisher/scripts/bilibili_publish.py
~/.openclaw/skills/douyin-publisher/scripts/douyin_publish.py

# 回退
publishers/xianyu-publisher/scripts/xianyu_publish.py
publishers/bilibili-publisher/scripts/bilibili_publish.py
publishers/douyin-publisher/scripts/douyin_publish.py
```

## 各平台规格速查

| 平台 | 标题 | 正文 | 图片 | 禁止 |
|------|------|------|------|------|
| 闲鱼 | 10-30字 | 商品描述 | 可选 | 违禁词（见下） |
| 小红书 | ≤20字 | 200-300字 | 可选(AI生成) | emoji、极限词 |
| B站 | ≤40字 | 800-1500字 | 封面可选 | emoji、AI感词 |
| 抖音 | ≤30字 | 150-500字 | 必须≥1张 | emoji、极限词 |


## 登录态路径

```
闲鱼: ~/.openclaw/browser_profiles/xianyu_default/
小红书: $XHS_MCP_DIR/cookies.json
         （由 xiaohongshu-mcp 管理，扫码登录后自动保存）
B站: ~/.catpaw/bilibili_browser_profile/
抖音: ~/.catpaw/douyin_browser_profile/
```

## 小红书 MCP 服务

小红书发布不再使用 Python 脚本，改为调用 **xiaohongshu-mcp MCP Server**：

```
服务地址: http://localhost:18060/mcp
项目路径: $XHS_MCP_DIR/
启动命令: cd $XHS_MCP_DIR && go run .
登录命令: ./xiaohongshu-login-darwin-arm64  （首次使用扫码登录）
```

## 发布成功标志

| 平台 | 成功标志 |
|------|---------|
| 闲鱼 | 脚本退出码 0 |
| 小红书 | MCP 响应 `result.content[0].text` 含「发布成功」或「success」，且 `result.isError != true` |
| B站 | 输出含「提交成功」 |
| 抖音 | 输出含「发布成功」或「审核中」 |
