---
name: xhs-publisher
description: 小红书（RED/XHS）自动发布助手。支持文字配图模式（小红书 AI 自动生成配图）和上传图片模式。复刻官方能力：内容生成 + Playwright 自动化发布 + 持久化登录态。触发词：发布小红书、发小红书笔记、发XHS、发布到小红书、小红书自动发布、xhs publisher。
---

# 小红书自动发布 Skill

## 使用模式

### 模式一：内容生成 + 自动发布（推荐）

用户提供以下任意输入，Claude 先生成内容，直接发布：

| 输入类型 | 示例 |
|---------|------|
| **主题** | "AI 行业职业发展分析" |
| **痛点** | "35岁程序员焦虑" |
| **目的** | "推广某个产品/服务" |
| **话题** | "技术人职业规划" |

**生成流程：**
```
1. 理解用户意图，确定目标人群和核心话题
2. 按 references/content-generation.md 规则起草标题 + 正文（200-300 字）
3. 调用 xhs_publish.py 脚本发布（文字配图模式或上传图片模式）
```

### 模式二：直接发布

用户直接提供标题和正文，跳过生成步骤直接调用脚本发布。

---

## 内容生成规则（核心摘要）

详见 `references/content-generation.md`，核心要点：

- **字数**：正文 200-300 字，标题 ≤20 字
- **口吻**：有经验的分享者视角，诚恳专业，有温度
- **结构**：痛点共鸣 → 干货分享 → 自然收尾 → 互动引导
- **标签策略**：融入相关热门话题标签
- **小红书合规**：生成前对照 `references/content-generation.md` 中的合规要求

---

## 发布技术流程

```
1. 启动 Playwright Chromium（持久化 profile，复用登录态）
   - 视口固定为 1440x900（确保所有按钮在可视区域内）
2. 导航到 creator.xiaohongshu.com/publish/publish?source=official
3. 检测登录态 → 未登录则等待手动扫码（90s）
4. JS 点击「上传图文」Tab → 等待 1.5s
5a. 【上传图片模式】暴露 file input → set_input_files → 等待 8s
5b. 【文字配图模式】6步完整流程：
    ① 点击「文字配图」按钮 → 等待 2s
    ② wait_for_selector 等待 ProseMirror 编辑器出现（最多 8s）
    ③ execCommand('insertText') 输入配图文字
    ④ 轮询检测 .edit-text-button-text 的 disabled class 消失 → 点击「生成图片」
    ⑤ 轮询检测 .overview-footer button 出现（最多 20s）
    ⑥ 点击「下一步」→ 验证标题输入框出现
6. fill 填写标题（input[placeholder*="标题"]）
7. 正文编辑器（ProseMirror）：
   - 聚焦 → Meta+a 全选 → Backspace 清空
   - navigator.clipboard.writeText → Meta+v 粘贴
   - 降级：逐段 keyboard.type()
8. click button:has-text("发布")
9. 等待跳转 /publish/success → 截图确认
```

**文字配图模式关键机制：**
- 视口从 428x598 改为 **1440x900**，避免按钮被遮挡
- 「下一步」改为**轮询等待** `.overview-footer` 出现后再点击，不再盲目等待固定时间
- 增加**进入编辑页验证**：检测 `input[placeholder*="标题"]` 是否存在，失败则报错终止

---

## 快速运行

### 前置安装（首次，在目标电脑上执行）
```bash
pip install playwright -i https://mirrors.aliyun.com/pypi/simple/
python3 -m playwright install chromium
```

### CLI 调用
```bash
SKILL_DIR=~/.openclaw/skills/xhs-publisher

# 文字配图模式（指定配图文字）
python3 $SKILL_DIR/scripts/xhs_publish.py \
  --title "申请XXX被拒？这3个坑99%的人都踩过" \
  --content "正文内容..." \
  --text-for-image "申请XXX这3个坑别踩" \
  --workspace ~/Desktop

# 文字配图模式（自动用正文前20字）
python3 $SKILL_DIR/scripts/xhs_publish.py \
  --title "标题" \
  --content "正文内容"

# 上传图片模式
python3 $SKILL_DIR/scripts/xhs_publish.py \
  --title "标题" \
  --content "正文内容" \
  --image "/path/to/img.png"

# 从 JSON 文件读取
python3 $SKILL_DIR/scripts/xhs_publish.py \
  --content-file "/path/to/content.json"
```

### content.json 格式
```json
{
  "title": "笔记标题（≤20字）",
  "content": "正文内容（200-300字）",
  "text_for_image": "配图文字（可选，不填则用正文前20字）",
  "image": "/path/to/image.png"
}
```

---

## 重要注意事项

1. **发布必须调用 `xhs_publish.py` Python 脚本**，不要用 browser_action 操作浏览器。
2. **图片格式**：支持 `.png .jpg .jpeg .webp`，不支持 `.gif`。
3. **发布成功判断**：最终 URL 包含 `/publish/success` 即为成功。
4. **首次使用**：脚本会打开浏览器等待扫码，登录态保存在 `~/.catpaw/xhs_browser_profile`，后续无需再登录。
5. **文字配图模式**：无需准备图片，小红书 AI 自动根据文字生成配图（适合干货类内容）

---

## 常见问题

详见 `references/troubleshooting.md`
