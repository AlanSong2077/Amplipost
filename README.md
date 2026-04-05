<p align="center">
  <img src="https://img.freepik.com/free-vector/social-media-apps-concept-illustration_114360-1908.jpg?w=1200" width="100%" alt="Social Publisher Banner"/>
</p>

<h1 align="center">
  🚀 Social Publisher
</h1>

<p align="center">
  <strong>全平台社交媒体自动发布助手</strong>
  <br>
  闲鱼 · 小红书 · B站专栏 · 抖音图文 ——— 一键分发全网
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-闲鱼-brightgreen?style=flat-square&logo=rocket" />
  <img src="https://img.shields.io/badge/Platform-小红书-red?style=flat-square&logo=heart" />
  <img src="https://img.shields.io/badge/Platform-B站-cyan?style=flat-square&logo=video" />
  <img src="https://img.shields.io/badge/Platform-抖音-black?style=flat-square&logo=tiktok" />
  <img src="https://img.shields.io/badge/Scrapling-Enhanced-blue?style=flat-square&logo=lightning" />
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" />
</p>

---

## ✨ 它能做什么？

<table>
<tr>
<td width="25%">

### 🐟 闲鱼发布
<img src="https://img.icons8.com/color/48/000000/aliexpress.png" width="32"/>

AI 生成商品配图 · 自动发布 · 违禁词过滤 · 登录态持久化

</td>
<td width="25%">

### 📕 小红书
<img src="https://img.icons8.com/color/48/000000_instagram-logo.png" width="32"/>

文字配图模式 · 上传图片 · 爆款标题 · 话题标签

</td>
<td width="25%">

### 📺 B站专栏
<img src="https://img.icons8.com/color/48/000000 bilibili.png" width="32"/>

800-1500字深度文章 · 自动排版 · 草稿管理

</td>
<td width="25%">

### 🎵 抖音图文
<img src="https://img.icons8.com/color/48/000000/tiktok.png" width="32"/>

短平快图文 · AI配图 · 创作者中心直发

</td>
</tr>
</table>

---

## 🎯 快速开始

### 1️⃣ 安装依赖

```bash
# OpenClaw
npm install -g openclaw

# agent-browser
npm install -g agent-browser
agent-browser install

# Scrapling（可选，增强反爬能力）
pip install "scrapling[all]>=0.4.3"
scrapling install --force
```

### 2️⃣ 一句话发布

```
"帮我发布闲鱼：iPhone 15 Pro Max，5999元，95新"
"发一篇小红书笔记：AI工具推荐"
"写一篇B站专栏：OMSCS申请攻略"
"发布抖音图文：留学省钱技巧"
```

### 3️⃣ 完成！ 🎉

---

## 🌟 核心优势

| 特性 | 说明 |
|------|------|
| 🤖 **AI 驱动** | GPT/LLM 自动生成内容，配图也智能 |
| 🕷️ **Scrapling 增强** | 反爬检测 + 自适应解析，网站变更更鲁棒 |
| 🌐 **真实浏览器** | Playwright 模拟真人操作，零风控 |
| 🔄 **自动登录** | Cookie 持久化，只登录一次 |
| 🛡️ **违禁词过滤** | 内置词库，自动替换敏感词 |
| 📊 **日志追踪** | 完整操作日志，随时回溯 |
| 🔧 **模板化** | 7+ 发货模板，开箱即用 |

---

## 🕷️ Scrapling 增强技术

> 所有发布脚本均提供 **Scrapling 增强版**，带来更强的鲁棒性和反检测能力。

### 增强版脚本

| 平台 | 标准版 | 增强版 |
|------|--------|--------|
| 📕 小红书 | `xhs_publish.py` | `xhs_publish_scrapling.py` ✅已测试 |
| 🐟 闲鱼 | `xianyu_publish.py` | `xianyu_publish_scrapling.py` |
| 📺 B站 | `bilibili_publish.py` | `bilibili_publish_scrapling.py` |
| 🎵 抖音 | `douyin_publish.py` | `douyin_publish_scrapling.py` |

### 技术改进

```
┌─────────────────────────────────────────────────────────────┐
│                    Scrapling 增强层                          │
├─────────────────────────────────────────────────────────────┤
│  🔍 页面预检      │ StealthyFetcher 反爬检测               │
│  🎯 自适应选择器  │ find_similar 自动降级                   │
│  🔄 增强重试      │ 条件等待 + 自动重试机制                 │
│  🛡️ 容错设计     │ JS 降级 + 详细日志                      │
└─────────────────────────────────────────────────────────────┘
```

### 工作原理

```
1. Scrapling 预检 → 检测页面可访问性 + 反爬状态
       ↓
2. Playwright 自动化 → 实际执行发布操作
       ↓
3. 自适应选择器 → 多方法降级，网站变更也能工作
       ↓
4. 增强容错 → 每步都有 JS 兜底方案
```

---

## 🏗️ 技术架构

```
         ┌─────────────────────────────────────┐
         │           🤖 OpenClaw               │
         │        AI Agent 调度中心            │
         └──────────────┬──────────────────────┘
                        │
    ┌───────────────────┼───────────────────┐
    │                   │                   │
    ▼                   ▼                   ▼
┌────────┐        ┌──────────┐        ┌────────┐
│ 闲鱼   │        │ 小红书   │        │  B站   │ ...
│Publisher│        │Publisher │        │Publisher│
└────┬───┘        └────┬─────┘        └────┬───┘
     │                 │                   │
     └─────────────────┼───────────────────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
┌─────────────────────┐  ┌─────────────────────┐
│      Playwright      │  │      Scrapling       │
│   🌐 浏览器自动化     │  │   🕷️ 反爬预检       │
└──────────┬──────────┘  └──────────┬──────────┘
           │                        │
           └────────────┬───────────┘
                        ▼
         ┌─────────────────────────────┐
         │          🐟 闲鱼             │
         │          📕 小红书            │
         │          📺 B站               │
         │          🎵 抖音              │
         └─────────────────────────────┘
```

---

## 📁 项目结构

```
social-publisher/
│
├── README.md                 📖 项目文档
├── LICENSE                   📄 MIT 许可证
│
└── publishers/               🚀 四大平台发布模块
    │
    ├── 🐟 xianyu-publisher/     闲鱼自动发布
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── xianyu_publish.py             # 标准版
    │   │   ├── xianyu_publish_scrapling.py   # Scrapling增强版 ✨
    │   │   └── auto_publish.py               # 高级发布
    │   └── references/
    │
    ├── 📕 xhs-publisher/        小红书自动发布
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── xhs_publish.py              # 标准版
    │   │   └── xhs_publish_scrapling.py   # Scrapling增强版 ✨
    │   └── references/
    │
    ├── 📺 bilibili-publisher/   B站专栏自动发布
    │   ├── SKILL.md
    │   ├── scripts/
    │   │   ├── bilibili_publish.py              # 标准版
    │   │   └── bilibili_publish_scrapling.py   # Scrapling增强版 ✨
    │   └── references/
    │
    └── 🎵 douyin-publisher/      抖音图文自动发布
        ├── SKILL.md
        ├── scripts/
        │   ├── douyin_publish.py              # 标准版
        │   ├── douyin_publish_scrapling.py   # Scrapling增强版 ✨
        │   └── generate_images.py             # AI配图
        └── references/
```

---

## 🚀 使用示例

### 🐟 闲鱼 - 卖二手iPhone

```
帮我发布闲鱼：
- 商品：iPhone 15 Pro Max
- 描述：256GB 钛金属，电池健康98%
- 价格：1517.04
- 新旧：95新
- 配图：自动生成
```

### 📕 小红书 - 种草笔记

```
发布小红书（文字配图）：
- 内容：5个提升效率的AI工具推荐
- 标签：#AI工具 #效率提升
```

### 📺 B站 - 留学攻略

```
帮我写B站专栏：
- 主题：OMSCS申请全攻略
- 字数：1000字
- 风格：干货分享
```

### 🎵 抖音 - 热点图文

```
发布抖音图文：
- 内容：留学省钱小技巧
- 配图：自动生成
```

---

## 🛡️ 安全说明

| ✅ 已实现 | ❌ 不支持 |
|----------|----------|
| 真实 Chrome 环境 | 批量注册账号 |
| 真人操作轨迹 | 刷量/刷粉 |
| Scrapling 反爬 | 违规内容发布 |
| Cookie 加密存储 | 绕过平台限制 |
| 操作日志审计 | |

**⚠️ 免责声明：本工具仅供学习和个人使用，请遵守各平台服务条款。**

---

## 🔧 故障排查

**Q: 登录失效怎么办？**
```bash
# 重新登录对应平台
"登录闲鱼" / "登录小红书" / "登录B站"
```

**Q: 发布失败？**
```bash
# 检查浏览器状态
agent-browser snapshot

# 使用 Scrapling 增强版脚本（更鲁棒）
python3 xhs_publish_scrapling.py --title "标题" --content "内容"
```

**Q: 配图中文乱码？**
```bash
# macOS 安装字体
brew install font-morisawa
cp $(find /usr/fonts -name "*.ttc" | head -1) ~/Library/Fonts/
```

---

## 🤝 贡献

欢迎 Star ⭐ 和 PR！

```bash
1. Fork 本项目
2. 创建分支 git checkout -b feature/AmazingFeature
3. 提交更改 git commit -m 'Add AmazingFeature'
4. 推送 git push origin feature/AmazingFeature
5. 创建 Pull Request
```

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

<p align="center">
  <strong>Made with ❤️ by AI Agent</strong>
  <br><br>
  <img src="https://img.shields.io/badge/OpenClaw-Automation-blueviolet?style=for-the-badge&logo=robot" />
  <img src="https://img.shields.io/badge/Playwright-Browser-green?style=for-the-badge&logo=microsoft" />
  <img src="https://img.shields.io/badge/Scrapling-Enhanced-blue?style=for-the-badge&logo=lightning" />
</p>

<p align="center">
  <sub>Built for creators · Designed for scale</sub>
</p>
