<div align="center">

![AmpliPost Banner](./banner.svg)

<br>

[![License](https://img.shields.io/badge/License-MIT-6366f1?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-06b6d4?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Go](https://img.shields.io/badge/Go-1.21+-00acd7?style=flat-square&logo=go&logoColor=white)](https://go.dev)
[![Claude Code](https://img.shields.io/badge/Claude_Code-Multi--Agent-8b5cf6?style=flat-square)](https://docs.anthropic.com/claude-code)
[![MCP](https://img.shields.io/badge/MCP-xiaohongshu--mcp-00acd7?style=flat-square)](https://github.com/xpzouying/xiaohongshu-mcp)
[![Playwright](https://img.shields.io/badge/Playwright-Latest-10b981?style=flat-square&logo=playwright&logoColor=white)](https://playwright.dev)
[![PRs Welcome](https://img.shields.io/badge/PRs-Welcome-f43f5e?style=flat-square)](CONTRIBUTING.md)

<br>

**AmpliPost** 是基于 **Claude Code Multi-Agent 架构**构建的智能营销中台。三个协作 Agent（content-coordinator、content-reviewer、publish-guard）分工明确，配合 Hooks 系统与长期记忆，将「一句话指令」转化为跨平台内容的全自动生产与分发。小红书发布层由 **xiaohongshu-mcp**（Go + go-rod + CDP）驱动。——无需人工确认，无需手动操作，全程自主决策。

<br>

[快速开始](#-快速开始) · [Multi-Agent 架构](#-multi-agent-架构) · [发布流水线](#-发布流水线) · [平台矩阵](#-平台矩阵) · [Hooks 系统](#-hooks-系统) · [长期记忆](#-长期记忆)

</div>

---

## 为什么是 Multi-Agent + MCP

传统自动化脚本的瓶颈不在执行，而在判断与风控。内容质量好不好？这次发布会不会触发风控？这两个问题如果由同一个 Agent 自问自答，天然存在偏差。与此同时，Playwright 走 WebDriver 协议，`navigator.webdriver=true` 特征会被小红书等平台识别，导致持续封号。

AmpliPost 的解法是双重分离：**职责分离**（content-coordinator 生成、content-reviewer 评审、publish-guard 风控，三者通过结构化 JSON 通信互不干涉）+ **技术分离**（小红书发布层独立为 xiaohongshu-mcp MCP Server，Go + go-rod 直连 CDP，无 WebDriver 特征，行为拟人化，Cookie 持久化，原作者自用一年无封号）。

---

## 🤖 Multi-Agent 架构

![Architecture](./architecture.svg)

### 三 Agent + MCP Server 职责边界

<table>
<tr>
<th width="22%">组件</th>
<th width="38%">职责</th>
<th width="40%">不做什么</th>
</tr>
<tr>
<td><strong>content-coordinator</strong><br><sub>主 Agent</sub></td>
<td>解析用户输入、生成各平台内容、调度 subagent、执行发布、汇报结果、更新记忆</td>
<td>不自评内容质量、不做风控判断</td>
</tr>
<tr>
<td><strong>content-reviewer</strong><br><sub>质量评审</sub></td>
<td>从钩子强度、信息密度、真实感、平台适配、多样性五个维度独立评分，给出具体修改建议</td>
<td>不生成内容、不做发布决策</td>
</tr>
<tr>
<td><strong>publish-guard</strong><br><sub>风控守卫</sub></td>
<td>评估发布频率、间隔规律性、内容多样性、账号行为特征，输出 allow / delay / block 三态决策</td>
<td>不评价内容质量、不修改内容</td>
</tr>
<tr>
<td><strong>xiaohongshu-mcp</strong><br><sub>MCP Server · Go</sub></td>
<td>小红书发布底层执行层，监听 localhost:18060，通过 go-rod + CDP 直连 Chromium，提供 13 个工具</td>
<td>不生成内容、不做任何判断</td>
</tr>
</table>

### 自主决策边界

Agent 在以下情况**自主处理，不询问用户**：未指定平台时根据内容类型推断目标平台；抖音无图时自动调用 `generate_images.py` 生成信息图；内容含违禁词时自动替换；内容质量不达标时交 reviewer 评审并按建议重写（最多 2 次）；风控评估为 delay 时等待随机延迟后发布；xiaohongshu-mcp 服务未运行时自动后台唤起（含自动安装）；发布失败可修复时自动重试（最多 3 次）。

**只有两种情况会停下来询问用户**：登录态失效（需手动扫码，物理限制）；指令完全歧义（主题空白，无法推断）。

---

## 🚀 快速开始

### 安装依赖

```bash
# Playwright 浏览器自动化（闲鱼 / B站 / 抖音）
npm install -g agent-browser
agent-browser install

# Scrapling 反爬增强
pip install "scrapling[all]>=0.4.3"
scrapling install --force
```

### 一键安装 xiaohongshu-mcp（小红书发布层）

```bash
# 自动 clone、编译、写入环境变量（需要 Go 1.21+）
bash scripts/setup-xhs-mcp.sh

# 首次登录小红书（扫码，只需一次）
bash scripts/start-xhs-mcp.sh --login
```

> 之后无需手动管理服务。content-coordinator 发布小红书时会自动检测并唤起 MCP Server。

### 配置 API Key

```bash
cp keys.example.txt keys.txt
# 编辑 keys.txt，填入各平台所需的 API Key
```

### 一句话触发全链路

```bash
# 内容类型自动推断平台（干货 → 小红书 + 抖音 + B站）
"帮我发：2025年最值得入手的5款AI工具"

# 指定平台
"发小红书和抖音：职场效率提升的3个反直觉技巧"

# 闲鱼商品（自动识别为商品类 → 闲鱼 + 小红书）
"帮我发闲鱼：iPhone 15 Pro Max 256G，5999元，95新"

# 深度技术文章（→ B站 + 小红书）
"写一篇关于 Scrapling 反爬原理的深度文章"
```

### 登录态说明

```bash
# 各平台首次使用需手动扫码（90秒窗口期），之后 Cookie 自动复用
# 闲鱼:  ~/.openclaw/browser_profiles/xianyu_default/
# 小红书: $XHS_MCP_DIR/cookies.json  （由 xiaohongshu-mcp 管理）
# B站:   ~/.catpaw/bilibili_browser_profile/
# 抖音:  ~/.catpaw/douyin_browser_profile/
```

---

## 🔄 发布流水线

![Pipeline](./scrapling-flow.svg)

完整流水线共 8 个阶段，全程自动执行：

**Phase 0** 读取 `memory.md`，提取历史有效内容方向、用户偏好、内容指纹和风控日志，为后续生成提供参考。

**Phase 1–2** 解析用户输入，推断目标平台，查找各平台 Skill 脚本路径（小红书检查 MCP Server 是否运行，未运行则自动后台唤起），处理图片决策树（抖音无图自动生成，小红书无图使用文字配图模式）。

**Phase 3** 为每个目标平台独立生成内容，严格遵循各平台字数、结构、风格规格，禁止平台间内容互相复制。

**Phase 3.5** 调用 content-reviewer subagent 进行独立质量评审，总分低于 70 分则按具体建议重写，最多重写 2 次。

**Phase 4.5** 调用 publish-guard subagent 进行风控评估，delay 决策时等待随机延迟，block 决策时跳过并在报告中说明原因。

**Phase 5–8** 依次执行发布（小红书通过 HTTP POST 调用 xiaohongshu-mcp，其他平台调用 Python Skill 脚本，平台间间隔 15 秒），验证成功标志，输出表格报告，将本次发布记录和内容指纹写入 `memory.md`。

---

## 🎯 平台矩阵

<table>
<tr>
<th align="center" width="25%">🐟 闲鱼</th>
<th align="center" width="25%">📕 小红书</th>
<th align="center" width="25%">📺 B站专栏</th>
<th align="center" width="25%">🎵 抖音图文</th>
</tr>
<tr>
<td>

标题 10–30 字<br>
【新旧程度】商品名 规格<br>
违禁词自动替换<br>
AI 配图可选<br>
Python · Playwright

</td>
<td>

标题 ≤20 字<br>
正文 200–300 字<br>
四段结构：痛点→干货→收尾→互动<br>
**xiaohongshu-mcp · Go+CDP**<br>
无 WebDriver · 反风控验证 ✅

</td>
<td>

标题 ≤40 字<br>
正文 800–1500 字<br>
五段结构：引言→分析→干货→误区→互动<br>
3–5 个话题标签<br>
Python · Playwright

</td>
<td>

标题 ≤30 字<br>
正文 150–500 字<br>
必须有图（无图自动生成信息图）<br>
3–5 个 # 话题标签<br>
Python · Playwright

</td>
</tr>
</table>

### 平台智能推断规则

| 内容类型 | 自动发布到 |
|---------|-----------|
| 二手商品出售 | 闲鱼 + 小红书 |
| 干货 / 经验分享 | 小红书 + 抖音 + B站 |
| 产品推广 / 营销 | 小红书 + 抖音 |
| 深度技术文章 | B站 + 小红书 |

---

## ⚡ Hooks 系统

AmpliPost 通过 Claude Code 的 Hooks 机制在发布行为的前后各设一道拦截：

**PreToolUse Hook** 在每次调用发布脚本前触发（闲鱼 / B站 / 抖音），检查闲鱼违禁词（高仿/A货/假货/仿品/全网最低/代购）、B站和抖音的 emoji、以及极限词（全网最好/史上最/绝对最）。违禁词和 emoji 检测到则 `exit 2` 阻止执行，极限词仅输出警告不阻止。小红书通过 MCP HTTP 调用，合规检查在内容生成阶段完成，不经过此 Hook。

**PostToolUse Hook** 在发布脚本执行完成后异步触发，按平台检测成功标志，并将结果写入 `~/.amplipost/logs/publish_YYYYMMDD.log`。

```json
{
  "hooks": {
    "PreToolUse":  [{ "matcher": "Bash", "command": "python3 .claude/hooks/pre-publish-check.py" }],
    "PostToolUse": [{ "matcher": "Bash", "command": "python3 .claude/hooks/post-publish-verify.py", "async": true }]
  }
}
```

---

## 💾 长期记忆

`memory.md` 是 AmpliPost 的持久化记忆层，由 content-coordinator 在每次任务结束后自动维护，content-reviewer 和 publish-guard 在评审时主动读取。

记忆层包含六个区块：**发帖方向演进**（有效方向与待规避方向）、**平台经验积累**（各平台有效开头/标题模式）、**发布记录**（每次发布的时间、平台、主题、状态）、**Agent 自主迭代笔记**（Agent 发现的规律和改进思路）、**用户偏好记录**（用户明确表达的风格要求）、**风控日志**（每次风控评估的决策和风险分）。

随着使用次数增加，Agent 会逐渐积累对用户偏好和平台规律的理解，内容质量和风控安全性会持续提升。

---

## 📁 项目结构

```
Amplipost/
├── CLAUDE.md                          # Claude Code 项目指令（速查表）
├── AGENTS.md                          # Multi-Agent 架构说明
├── SPEC.md                            # 完整系统规格
├── memory.md                          # 长期记忆（自动维护）
├── keys.example.txt                   # API Key 配置模板
│
├── scripts/
│   ├── setup-xhs-mcp.sh              # 一键安装 xiaohongshu-mcp（clone+编译+环境变量）
│   └── start-xhs-mcp.sh              # 启动/自动唤起 MCP Server
│
├── publishers/                        # Skill 脚本（只读，仅执行发布）
│   ├── xianyu-publisher/
│   │   └── scripts/
│   │       ├── xianyu_publish.py
│   │       └── xianyu_publish_scrapling.py
│   ├── xhs-publisher/
│   │   └── SKILL.md                  # 小红书发布规范（MCP 调用方式）
│   ├── bilibili-publisher/
│   └── douyin-publisher/
│       └── scripts/
│           └── generate_images.py    # 抖音 AI 信息图生成
│
└── .claude/
    ├── settings.json                  # Hooks 注册 + 权限配置
    ├── agents/
    │   ├── content-coordinator.md    # 主 Agent
    │   ├── content-reviewer.md       # 质量评审 subagent
    │   └── publish-guard.md          # 风控守卫 subagent
    └── hooks/
        ├── pre-publish-check.py      # PreToolUse Hook
        └── post-publish-verify.py    # PostToolUse Hook
```

---

## 🔧 故障排查

**小红书 MCP 服务未启动**

content-coordinator 会自动调用 `scripts/start-xhs-mcp.sh --bg` 后台唤起服务。若自动唤起失败（通常是首次未登录），会提示：`bash scripts/start-xhs-mcp.sh --login`。

**换新电脑部署**

```bash
bash scripts/setup-xhs-mcp.sh        # 自动 clone + 编译 + 写环境变量
bash scripts/start-xhs-mcp.sh --login  # 首次扫码登录
```

**内容评审连续不通过**

content-reviewer 连续 2 次评审不通过时，该平台会被跳过，最终报告中会注明「内容评审未通过」及具体原因。可以调整输入描述后重新触发。

**发布被风控拦截**

publish-guard 输出 block 决策时，报告中会说明拦截原因（通常是当日发布频率过高或内容重复度过高）。建议等待 24–48 小时后重试，或调整内容主题。

**配图中文乱码（macOS）**

```bash
brew install font-morisawa
cp $(find /usr/fonts -name "*.ttc" | head -1) ~/Library/Fonts/
```

---

## 🤝 贡献

```bash
git checkout -b feature/your-feature
git commit -m 'feat: add your feature'
git push origin feature/your-feature
# 提交 Pull Request
```

**注意：** `publishers/*/scripts/*.py` 和 `publishers/*/SKILL.md` 为只读文件，`.claude/settings.json` 已通过 `deny` 规则保护，PR 中请勿修改这些路径。

---

## 📄 许可证

[MIT License](LICENSE) · © 2025 Alan Song & Roxy Li

---

## 🙏 致谢

本项目的小红书发布能力基于 [xiaohongshu-mcp](https://github.com/xpzouying/xiaohongshu-mcp) 实现，感谢开源！

---

<div align="center">

[![Claude Code](https://img.shields.io/badge/Built_with-Claude_Code-8b5cf6?style=for-the-badge)](https://docs.anthropic.com/claude-code)
[![xiaohongshu-mcp](https://img.shields.io/badge/XHS-xiaohongshu--mcp-00acd7?style=for-the-badge&logo=go)](https://github.com/xpzouying/xiaohongshu-mcp)
[![Playwright](https://img.shields.io/badge/Browser-Playwright-06b6d4?style=for-the-badge&logo=playwright)](https://playwright.dev)

*One sentence in · Four platforms out · Zero human intervention*

</div>
