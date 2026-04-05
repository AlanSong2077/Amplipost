---
name: bilibili-publisher
description: B站（哔哩哔哩）专栏自动发布助手。生成深度专栏文章并自动发布到 B站专栏平台。复刻小红书 skill 的完整能力：内容生成 + Playwright 自动化发布 + 持久化登录态。触发词：发布B站专栏、B站投稿、帮我写B站文章、B站专栏发布、bilibili。
---

# B站专栏自动发布 Skill

## 使用模式

### 模式一：内容生成 + 自动发布（推荐）

用户提供任意输入，Claude 生成深度专栏文章后自动发布：

| 输入类型 | 示例 |
|---------|------|
| **主题** | "AI 行业就业分析" |
| **痛点** | "35岁程序员焦虑" |
| **话题** | "技术人职业规划" |
| **目标人群** | "面向转行程序员" |

**生成流程：**
```
1. 理解用户意图，确定目标人群和核心话题
2. 用 web_search 搜索相关热点和数据（可选）
3. 按 references/content-generation.md 规则生成标题 + 正文（800-1500字）
4. 展示给用户确认
5. 调用 bilibili_publish.py 脚本发布
```

### 模式二：直接发布

用户直接提供标题和正文，跳过生成步骤直接发布。

---

## 内容生成规则（核心摘要）

详见 `references/content-generation.md`，核心要点：

- **字数**：正文 800-1500 字，标题 ≤40 字
- **风格**：深度专栏，有逻辑有数据，面向理性用户
- **结构**：引言 → 核心分析 → 干货内容 → 常见误区 → 结尾互动引导
- **话题选择**：根据用户指定或自动从话题库选取
- **B站合规**：生成前必须对照 `references/bilibili-rules.md`，禁止极限词、直接联系方式、站外导流
- **禁止表情符号**：正文和标题中严禁出现任何 emoji / Unicode 表情

---

## 发布技术流程

```
1. 启动 Playwright Chromium（持久化 profile，复用登录态）
   - 视口固定为 1440x900
   - Profile: ~/.catpaw/bilibili_browser_profile
2. 导航到 member.bilibili.com/platform/upload/text/new-edit
   ⚠️  注意：URL 是 new-edit，不是 edit
3. 检测登录态 → 未登录则等待手动登录（120s）
4. 等待编辑器 iframe 加载（iframe[src*='read-editor']）
   - 轮询检测 iframe 内 textarea.title-input__inner 出现（最多 20s）
5. 通过 frame 对象操作 iframe 内的元素：
   - 标题: textarea.title-input__inner（TEXTAREA，不是 input！）
     → fill() + dispatchEvent('input') 触发响应式
   - 正文: div.tiptap.ProseMirror.eva3-editor
     → execCommand('selectAll') + execCommand('insertText')
     → 降级：clipboard paste → 逐段 keyboard.type()
6. 话题标签（可选）：button:has-text('添加话题') → 输入框 Enter
7. 截图（发布前确认）
8. 点击发布：iframe 内 button（文字「发布」）
9. 等待成功弹窗：检测「你的专栏已提交成功」文字出现
10. 截图确认
```

**实测验证的关键 selector：**

| 元素 | Selector | 说明 |
|------|----------|------|
| 编辑器 iframe | `iframe[src*='read-editor']` | 所有编辑操作在此 frame 内 |
| 标题输入框 | `textarea.title-input__inner` | TEXTAREA，非 input |
| 正文编辑器 | `div.tiptap.ProseMirror` | ProseMirror，非 Quill |
| 发布按钮 | `button`（文字「发布」） | 在 iframe 内 |
| 成功弹窗 | 文字含「提交成功」 | 不跳转 URL |

---

## 快速运行

### 前置安装（首次，在目标电脑上执行）
```bash
pip install playwright -i https://mirrors.aliyun.com/pypi/simple/
python3 -m playwright install chromium
```

### CLI 调用
```bash
SKILL_DIR=~/.openclaw/skills/bilibili-publisher

# 基础发布
python3 $SKILL_DIR/scripts/bilibili_publish.py \
  --title "深度好文：技术人职业规划指南" \
  --content "正文内容（800-1500字）..."

# 带话题标签
python3 $SKILL_DIR/scripts/bilibili_publish.py \
  --title "标题" \
  --content "正文内容" \
  --tags "职业规划,程序员,互联网,技术成长"

# 从 JSON 文件读取（推荐，内容较长时使用）
python3 $SKILL_DIR/scripts/bilibili_publish.py \
  --content-file "/path/to/content.json"

# 指定截图保存目录
python3 $SKILL_DIR/scripts/bilibili_publish.py \
  --title "标题" --content "正文" \
  --workspace ~/Desktop
```

### content.json 格式
```json
{
  "title": "文章标题（建议30字以内）",
  "content": "正文内容（800-1500字）",
  "tags": ["职业规划", "程序员", "互联网", "技术成长"]
}
```

---

## 重要注意事项

1. **发布必须调用 `bilibili_publish.py` Python 脚本**，不要用 browser_action 操作浏览器。
2. **B站专栏需要账号有一定等级**（通常 Lv2 以上），新账号可能无法发布专栏。
3. **审核时间**：B站专栏提交后进入机器审核，通常数分钟到数小时，截图确认提交成功即可。
4. **封面图规格**：建议 1200×628 像素，JPG/PNG 格式。
5. **首次使用**：脚本会打开浏览器等待登录，登录态保存在 `~/.catpaw/bilibili_browser_profile`，后续无需再登录。
6. **内容准确性**：涉及具体数据时，建议用 web_search 确认最新信息。

---

## 常见问题

详见 `references/troubleshooting.md`
