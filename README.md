<div align="center">

![Social Publisher Banner](./banner.svg)

<br>

[![License](https://img.shields.io/badge/License-MIT-ffd93d?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-74b9ff?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Playwright](https://img.shields.io/badge/Playwright-Latest-4ecdc4?style=flat-square&logo=playwright&logoColor=white)](https://playwright.dev)
[![Scrapling](https://img.shields.io/badge/Scrapling-0.4.3+-a29bfe?style=flat-square)](https://github.com/D4Vinci/Scrapling)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-AI_Agent-ff6b6b?style=flat-square)](https://openclaw.ai)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)

<br>

**Social Publisher** 是一款由 AI 驱动的全平台社交媒体自动发布助手，支持闲鱼、小红书、B站专栏、抖音图文四大平台一键发布。内置 Scrapling 反爬增强层，配合 Playwright 真实浏览器自动化，实现低风控、高鲁棒的内容分发。
以2小时为时间间隔进行内容分发，进行了多账号轮询测试。小红书测试14天后触发风控，B站专栏至今暂未触发风控，抖音图文暂未触发风控，闲鱼暂未触发风控。

<br>

[快速开始](#-快速开始) · [平台支持](#-平台支持) · [技术架构](#-技术架构) · [Scrapling 增强](#-scrapling-增强技术) · [项目结构](#-项目结构) · [故障排查](#-故障排查)

</div>

---

## ✨ 核心特性

<table>
<tr>
<td width="50%">

**🤖 AI 全程驱动**

由 OpenClaw LLM 自动生成标题、正文、话题标签，并智能生成配图。内置违禁词过滤词库，发布前自动替换敏感词，无需人工审核。

</td>
<td width="50%">

**🕷️ Scrapling 反爬增强**

每次发布前通过 StealthyFetcher 预检页面可访问性与反爬状态，自适应选择器在网站改版后自动降级适配，大幅提升长期稳定性。

</td>
</tr>
<tr>
<td width="50%">

**🌐 真实浏览器操作**

基于 Playwright 模拟真人操作行为，Cookie 持久化存储，只需登录一次即可长期使用，规避平台风控检测。

</td>
<td width="50%">

**📊 完整日志追踪**

每次发布操作均记录完整日志，包含时间戳、操作步骤、异常信息，支持随时回溯排查，7+ 发货模板开箱即用。

</td>
</tr>
</table>

---

## 🎯 平台支持

<table>
<tr>
<th align="center" width="25%">🐟 闲鱼</th>
<th align="center" width="25%">📕 小红书</th>
<th align="center" width="25%">📺 B站专栏</th>
<th align="center" width="25%">🎵 抖音图文</th>
</tr>
<tr>
<td align="center">

AI 生成商品配图<br>
自动发布上架<br>
违禁词过滤<br>
登录态持久化<br>
7+ 发货模板

</td>
<td align="center">

文字配图模式<br>
图片批量上传<br>
爆款标题生成<br>
话题标签推荐<br>
Scrapling 增强 ✅

</td>
<td align="center">

800–1500 字深度文章<br>
自动排版格式化<br>
草稿管理<br>
封面图生成<br>
专栏分类设置

</td>
<td align="center">

短平快图文<br>
AI 智能配图<br>
创作者中心直发<br>
话题挂载<br>
定时发布支持

</td>
</tr>
</table>

---

## 🚀 快速开始

### 安装依赖

```bash
# 安装 OpenClaw AI Agent
npm install -g openclaw

# 安装 Playwright 浏览器自动化
npm install -g agent-browser
agent-browser install

# 安装 Scrapling 反爬增强（推荐）
pip install "scrapling[all]>=0.4.3"
scrapling install --force
```

### 一句话发布

```bash
# 闲鱼商品发布
"帮我发布闲鱼：iPhone 15 Pro Max，5999元，95新"

# 小红书笔记
"发一篇小红书笔记：AI工具推荐，附上3张配图"

# B站专栏文章
"写一篇B站专栏：深度解析 Scrapling 反爬技术"

# 抖音图文
"发布抖音图文：5个提升效率的生活小技巧"
```

### 使用 Scrapling 增强版（推荐）

```bash
# 小红书增强版
python3 publishers/xhs-publisher/scripts/xhs_publish_scrapling.py \
    --title "AI工具推荐" \
    --content "今天分享5个超好用的AI工具..." \
    --images ./images/cover.jpg

# 闲鱼增强版
python3 publishers/xianyu-publisher/scripts/xianyu_publish_scrapling.py \
    --title "iPhone 15 Pro Max" \
    --price 5999 \
    --condition "95新"
```

---

## 🏗️ 技术架构

![Architecture Diagram](./architecture.svg)

整体采用三层架构设计。最顶层是 **AI Agent 调度中心**，由 OpenClaw 驱动，负责内容生成、任务编排与违禁词过滤。中间层由 **Playwright 浏览器引擎**和 **Scrapling 反爬引擎**协同工作，前者负责真实浏览器操作，后者提供预检与自适应能力。底层直接对接四大社交平台，完成内容的最终分发。

---

## 🕷️ Scrapling 增强技术

![Scrapling Flow](./scrapling-flow.svg)

所有发布脚本均提供 Scrapling 增强版，在标准 Playwright 自动化之上叠加四层防护：页面预检验证目标可访问性，浏览器执行完成真实操作，自适应选择器在网站改版后自动降级，增强容错层提供 JS 兜底与自动重试。

| 平台 | 标准版 | Scrapling 增强版 |
|------|--------|-----------------|
| 📕 小红书 | `xhs_publish.py` | `xhs_publish_scrapling.py`  |
| 🐟 闲鱼 | `xianyu_publish.py` | `xianyu_publish_scrapling.py` |
| 📺 B站 | `bilibili_publish.py` | `bilibili_publish_scrapling.py` |
| 🎵 抖音 | `douyin_publish.py` | `douyin_publish_scrapling.py` |

---

## 📁 项目结构

```
social-publisher/
├── README.md
├── LICENSE
└── publishers/
    ├── xianyu-publisher/          🐟 闲鱼自动发布
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── xianyu_publish.py
    │   │   ├── xianyu_publish_scrapling.py
    │   │   └── auto_publish.py
    │   └── references/
    │
    ├── xhs-publisher/             📕 小红书自动发布
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── xhs_publish.py
    │   │   └── xhs_publish_scrapling.py
    │   └── references/
    │
    ├── bilibili-publisher/        📺 B站专栏自动发布
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── bilibili_publish.py
    │   │   └── bilibili_publish_scrapling.py
    │   └── references/
    │
    └── douyin-publisher/          🎵 抖音图文自动发布
        ├── SKILL.md
        ├── scripts/
        │   ├── douyin_publish.py
        │   ├── douyin_publish_scrapling.py
        │   └── generate_images.py
        └── references/
```

---

## 🔧 故障排查

**登录失效**

```bash
# 重新登录对应平台，Cookie 会自动更新
"登录闲鱼" / "登录小红书" / "登录B站" / "登录抖音"
```

**发布失败，建议切换增强版**

```bash
# 查看当前浏览器状态快照
agent-browser snapshot

# 切换到 Scrapling 增强版脚本，鲁棒性更强
python3 xhs_publish_scrapling.py --title "标题" --content "内容"
```

**配图中文乱码（macOS）**

```bash
brew install font-morisawa
cp $(find /usr/fonts -name "*.ttc" | head -1) ~/Library/Fonts/
```

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

```bash
git checkout -b feature/AmazingFeature
git commit -m 'feat: Add AmazingFeature'
git push origin feature/AmazingFeature
# 然后创建 Pull Request
```

---

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

---

<div align="center">

**Made with ❤️ by Alan Song & Roxy Li**

[![OpenClaw](https://img.shields.io/badge/Powered_by-OpenClaw-blueviolet?style=for-the-badge)](https://openclaw.ai)
[![Playwright](https://img.shields.io/badge/Browser-Playwright-green?style=for-the-badge&logo=playwright)](https://playwright.dev)
[![Scrapling](https://img.shields.io/badge/Enhanced_by-Scrapling-blue?style=for-the-badge)](https://github.com/D4Vinci/Scrapling)

*Built for creators · Designed for scale*

</div>
