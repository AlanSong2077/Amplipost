---
name: douyin-publisher
description: 抖音图文自动发布助手。生成短平快图文内容并自动发布到抖音创作者中心。复刻小红书 skill 的完整能力：内容生成 + 配图生成 + Playwright 自动化发布 + 持久化登录态。触发词：发布抖音图文、抖音投稿、帮我写抖音内容、抖音图文发布、douyin。
---

# 抖音图文自动发布 Skill

## 使用模式

### 模式一：内容生成 + 自动配图 + 发布（推荐）

用户提供任意输入，Claude 生成内容 + 自动生成配图后发布：

| 输入类型 | 示例 |
|---------|------|
| **主题** | "AI 行业就业分析" |
| **痛点** | "35岁程序员焦虑" |
| **话题** | "技术人职业规划" |
| **目标人群** | "面向转行程序员" |

**生成流程：**
```
1. 理解用户意图，确定目标人群和核心话题
2. 按 references/content-generation.md 规则生成标题 + 正文（150-500字）
3. 用 Python PIL 生成 3-5 张配图（信息图）
4. 展示给用户确认
5. 调用 douyin_publish.py 脚本发布
```

### 模式二：用户提供图片 + 自动发布

用户提供图片路径和内容，直接发布：

```
用户：发布抖音图文，图片在 ~/Desktop/pics/，标题「AI 行业薪资分析」
```

### 模式三：直接发布

用户直接提供标题、正文、图片路径，跳过生成步骤直接发布。

---

## 内容生成规则（核心摘要）

详见 `references/content-generation.md`，核心要点：

- **字数**：正文 150-500 字，标题 ≤30 字
- **风格**：短平快，强钩子开场，口语化，像朋友聊天
- **结构**：强钩子 → 核心干货（2-4点）→ 互动引导
- **配图必须**：抖音图文必须上传至少 1 张图片，建议 3-9 张
- **话题选择**：根据用户指定或自动选择话题
- **抖音合规**：生成前必须对照 `references/douyin-rules.md`，禁止极限词、直接联系方式
- **禁止表情符号**：正文和标题中严禁出现任何 emoji / Unicode 表情

---

## 配图生成（当用户未提供图片时）

使用 `scripts/generate_images.py` 自动生成支持中文的信息图（使用系统 STHeiti 字体）。

### 直接调用
```bash
SKILL_DIR=~/.openclaw/skills/douyin-publisher

# 生成自定义话题配图（3张）
python3 $SKILL_DIR/scripts/generate_images.py --topic 自定义话题 --title 自定义标题 --point1 要点1 --point2 要点2 --point3 要点3

# 测试中文显示
python3 $SKILL_DIR/scripts/generate_images.py --test
```

### 自动集成
`douyin_publish.py` 在未提供 `--images` 时会**自动调用** `generate_images.py` 生成配图：
```bash
# 不提供图片，自动生成通用配图并发布
python3 $SKILL_DIR/scripts/douyin_publish.py \
  --title "AI 行业薪资分析" \
  --content "正文内容..." \
  --auto-generate
```

**配图规格：** 1080×1080 px，JPG，使用系统 STHeiti 中文字体，深色背景专业风格

---

## 发布技术流程（已通过真实 DOM 探查验证）

```
1. 启动 Playwright Chromium（持久化 profile，复用登录态）
   - 视口固定为 1440x900
   - Profile: ~/.catpaw/douyin_browser_profile（独立 profile）
2. 导航到 creator.douyin.com/creator-micro/content/upload?default-tab=image-text
3. 检测登录态 → 未登录则等待手动扫码（120s）
4. 点击「发布图文」Tab（如未自动切换）
5. 上传图片：input[type='file'][accept*='image/png']
   - 等待编辑器出现：.zone-container.editor-kit-container（最多 20s）
6. 填写标题：input.semi-input.semi-input-default
   - fill() + dispatchEvent 触发响应式
7. 填写正文：.zone-container.editor-kit-container（contenteditable div）
   - execCommand('insertText') 插入文字
   - 话题：在正文末尾输入 #关键词，等待下拉，Enter 选择
8. 截图（发布前确认）
9. 点击发布：button.button-dhlUZE.primary-cECiOJ（文字「发布」）
10. 等待成功提示：检测「发布成功」/「审核中」文字或 URL 跳转
11. 截图确认
```

**实测验证的关键 selector：**

| 元素 | Selector | 说明 |
|------|----------|------|
| 图片上传 | `input[type='file'][accept*='image/png']` | 上传前存在于页面 |
| 标题输入框 | `input.semi-input.semi-input-default` | placeholder: 添加作品标题 |
| 正文编辑器 | `.zone-container.editor-kit-container` | contenteditable div |
| 话题触发 | 在编辑器内输入 `#关键词` | 触发下拉列表 |
| 发布按钮 | `button.button-dhlUZE.primary-cECiOJ` | 文字「发布」 |
| 继续添加图片 | `button.continue-add-clE5aC` | 文字「继续添加」 |

---

## 快速运行

### 前置安装（首次，在目标电脑上执行）
```bash
pip install playwright pillow -i https://mirrors.aliyun.com/pypi/simple/
python3 -m playwright install chromium
```

### CLI 调用
```bash
SKILL_DIR=~/.openclaw/skills/douyin-publisher

# 基础发布（需提供图片）
python3 $SKILL_DIR/scripts/douyin_publish.py \
  --title "AI 行业薪资分析" \
  --content "正文内容（150-500字）..." \
  --images "/path/to/img1.jpg,/path/to/img2.jpg"

# 带话题标签
python3 $SKILL_DIR/scripts/douyin_publish.py \
  --title "标题" \
  --content "正文内容" \
  --images "/path/to/img1.jpg" \
  --topics "职业规划,程序员,AI行业"

# 自动生成配图
python3 $SKILL_DIR/scripts/douyin_publish.py \
  --title "标题" \
  --content "正文内容" \
  --auto-generate

# 从 JSON 文件读取（推荐）
python3 $SKILL_DIR/scripts/douyin_publish.py \
  --content-file "/path/to/content.json"
```

### content.json 格式
```json
{
  "title": "作品标题（建议20字以内）",
  "content": "正文描述（150-500字）",
  "images": [
    "/path/to/img1.jpg",
    "/path/to/img2.jpg",
    "/path/to/img3.jpg"
  ],
  "topics": ["职业规划", "程序员", "AI行业"]
}
```

---

## 重要注意事项

1. **发布必须调用 `douyin_publish.py` Python 脚本**，不要用 browser_action 操作浏览器。
2. **图片为必填项**，抖音图文没有图片无法发布，至少需要 1 张。
3. **图片格式**：支持 jpg、jpeg、png、bmp、webp，不支持 gif。
4. **审核时间**：抖音图文提交后进入机器审核，通常数分钟到数小时。
5. **首次使用**：脚本会打开浏览器等待扫码登录，登录态保存在 `~/.catpaw/douyin_browser_profile`，后续无需再登录。
6. **话题输入**：抖音话题通过在正文中输入 `#关键词` 触发，与其他平台不同。

---

## 三平台对比

| 维度 | 小红书 | B站专栏 | 抖音图文 |
|------|--------|---------|---------|
| 内容长度 | 200-300 字 | 800-1500 字 | 150-500 字 |
| 配图 | AI配图/上传 | 封面图（可选） | **必须上传图片** |
| 发布 URL | creator.xiaohongshu.com | member.bilibili.com/... | creator.douyin.com/... |
| Profile 目录 | ~/.catpaw/xhs_browser_profile | ~/.catpaw/bilibili_browser_profile | ~/.catpaw/douyin_browser_profile |
| 话题方式 | 标签栏选择 | 按钮添加 | 正文内 # 触发下拉 |
| 发布后状态 | 直接发布 | 进入审核 | 进入审核 |
| 目标用户 | 泛用户 | 25-35岁理性用户 | 18-35岁泛用户 |
