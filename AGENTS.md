# Amplipost — Agent 架构说明

本文件描述 Amplipost 的 Agent 设计，供 Claude Code 及其他 AI 工具读取。

---

## 系统定位

Amplipost 是一个**全自动**多平台内容营销中台。

- 用户输入：一句话指令（「帮我发小红书，主题是 AI 工具推荐」）
- 系统输出：内容已发布到目标平台，返回发布状态

**不需要用户在中途确认内容、选择选项、提供图片。** 所有决策由 Agent 自主完成。

---

## Agent 结构

```
content-coordinator          ← 主 Agent，全程调度
    │
    ├── Phase 0: 读取 memory.md     ← 历史经验、用户偏好、内容指纹
    ├── Phase 1-2: 解析输入 + 查找脚本
    ├── Phase 3: 生成各平台内容      ← 主 Agent 负责生成
    │
    ├── Phase 3.5: ──► content-reviewer   ← subagent：独立质量评审
    │               返回评审报告 JSON
    │               pass=false 则按建议重写，最多2次
    │
    ├── Phase 4: 配图处理
    │
    ├── Phase 4.5: ──► publish-guard      ← subagent：风控拦截
    │               返回 allow/delay/block
    │               delay 则等待后发布，block 则跳过
    │
    ├── Phase 5: 发布执行             ← 调用 4 个平台 Skill 脚本
    ├── Phase 6-7: 验证结果 + 输出报告
    └── Phase 8: 更新 memory.md      ← 发布记录 + 内容指纹
```

### 三 Agent 职责边界

| Agent | 职责 | 不做什么 |
|-------|------|---------|
| **content-coordinator** | 解析输入、生成内容、调度流程、报告结果 | 不自评内容质量、不做风控判断 |
| **content-reviewer** | 独立评审内容质量，给出评分和具体修改建议 | 不生成内容、不做发布决策 |
| **publish-guard** | 评估发布行为的风控风险，决定放行/延迟/拦截 | 不评价内容质量、不修改内容 |
| **xiaohongshu-mcp** | 小红书发布的底层执行层（Go+go-rod+CDP），监听 localhost:18060 | 不生成内容、不做任何判断 |
| **Skill 脚本** | 闲鱼/B站/抖音的浏览器自动化发布 | 不生成内容、不做任何判断 |

**分离 reviewer 的原因：** 生成方对自己的内容天然存在主观偏差，容易打高分。独立 reviewer 用统一评分标准，能识别 AI 感词汇、内容同质化等问题。

**分离 guard 的原因：** 风控是行为维度的判断（频率、间隔、多样性），与内容质量无关，需要独立的历史数据视角。

---

## 智能化能力

### 内容生成（Agent 核心能力，不在 Skill 内执行）

Agent 根据用户输入，自主为每个目标平台生成独立内容：

| 平台 | 字数 | 风格 | 结构 |
|------|------|------|------|
| 小红书 | 200-300 字 | 第一人称，口语化，有情绪，真人感 | 痛点共鸣 → 干货 → 收尾 → 互动引导 |
| B站 | 800-1500 字 | 专业，数据支撑，深度 | 引言 → 核心分析 → 干货 → 误区 → 互动 |
| 抖音 | 150-500 字 | 短句，口语，强钩子 | 强钩子 → 核心干货 2-4 点 → 互动引导 |
| 闲鱼 | 标题 10-30 字 | 简洁，突出卖点 | 【新旧】商品名 规格 |

**内容质量自评（生成后自动执行，不满足则重写）：**
1. 第一句话能让目标用户停下来吗？（钩子强度）
2. 读完有实质收获，还是在凑字数？（信息密度）
3. 像真人说话，还是 AI 模板？（真实感）

**所有平台禁止**：`综上所述`、`首先其次`、`不禁感叹` 等 AI 感词汇

### 平台智能推断

未指定平台时，Agent 根据内容类型自动推断：

| 内容类型 | 发布到 |
|---------|-------|
| 二手商品出售 | 闲鱼 + 小红书 |
| 干货 / 经验分享 | 小红书 + 抖音 + B站 |
| 产品推广 / 营销 | 小红书 + 抖音 |
| 深度技术文章 | B站 + 小红书 |

### 违禁词与合规处理（Agent 在生成内容时执行）

**闲鱼违禁词自动替换：**

| 违禁词 | 替换为 |
|--------|--------|
| 高仿 | 复刻 |
| A货 | 正品 |
| 全网最低 | 优惠价 |
| 假货 | 特价商品 |
| 仿品 | 同款 |

**B站 / 抖音禁止 emoji**：生成内容时严禁任何 emoji / Unicode 表情符号

**极限词警告**：「全网最好」「全网第一」「史上最」「绝对最」——生成时主动规避

### 配图智能处理

```
抖音（必须有图）
  → 无图时：调用 generate_images.py 生成 3 张 1080×1080 信息图，继续执行

小红书（图片可选）
  → 无图时：不传 --image，使用文字配图模式，继续执行

闲鱼 / B站
  → 无图也可发布，继续执行
```

---

## 自主决策边界

Agent **自主处理**，不询问用户：

| 情况 | Agent 的行动 |
|------|------------|
| 未指定平台 | 根据内容类型推断 |
| 未提供图片（抖音） | 调用 `generate_images.py` 自动生成信息图 |
| 未提供图片（小红书） | 使用文字配图模式 |
| 内容含违禁词 | 生成时自动替换，不使用违规词 |
| 内容质量不达标 | 交给 content-reviewer 评审，按建议重写，最多 2 次 |
| 风控评估为 delay | 等待 guard 建议的随机延迟时间后发布 |
| 风控评估为 block | 跳过该平台，报告中说明原因 |
| 发布失败可修复 | 修复后自动重试，最多 3 次 |

Agent **停下来询问用户**的情况（仅两种）：

1. 登录态失效——需要用户手动扫码（90 秒窗口期），物理限制无法绕过
2. 指令完全歧义——「帮我发一下」，完全不知道发什么内容

---

## 小红书发布层：xiaohongshu-mcp MCP Server

小红书发布不再使用 Python/Playwright 脚本，改为调用独立运行的 **xiaohongshu-mcp** 服务。

```
项目路径: $XHS_MCP_DIR/
服务地址: http://localhost:18060/mcp  (本地 HTTP MCP 协议)
底层技术: Go + go-rod + Chrome DevTools Protocol (CDP)
反风控优势: 无 WebDriver 特征，行为拟人化，Cookie 持久化
```

**为什么换掉 Playwright：**
- Playwright 走 WebDriver 协议，`navigator.webdriver=true` 被小红书风控识别
- xiaohongshu-mcp 走 CDP 直连，无 WebDriver 特征，原作者自用一年无封号

**调用方式：** content-coordinator 通过 `curl` 发送 HTTP POST 到 `http://localhost:18060/mcp`

**工具列表（共 13 个）：** check_login_status, publish_content, publish_with_video, list_feeds, search_feeds, get_feed_detail, post_comment_to_feed, reply_comment_in_feed, user_profile, like_feed, favorite_feed, get_login_qrcode, delete_cookies

详见 `publishers/xhs-publisher/SKILL.md`。

## 其他平台 Skill 脚本（只读，仅执行发布）

以下脚本**不可修改**，只能调用。脚本**不负责内容生成**，只接收已生成好的参数执行浏览器自动化发布：

```
publishers/xianyu-publisher/scripts/xianyu_publish.py
publishers/bilibili-publisher/scripts/bilibili_publish.py
publishers/douyin-publisher/scripts/douyin_publish.py
publishers/douyin-publisher/scripts/generate_images.py
```

每个平台的完整调用规范见 `publishers/*/SKILL.md`。

---

## Hooks（Claude Code settings.json）

```
PreToolUse[Bash]   → 发布前合规检查（违禁词、emoji、极限词）
PostToolUse[Bash]  → 发布后结果验证（成功标志检测、日志记录）
```

退出码规范（Claude Code 标准）：
- `exit 0` — 通过，继续执行
- `exit 2` — 阻止，将 stderr 传给 Claude 作为错误原因
- `exit 1` — 非阻止错误，记录但继续

---

## 目录结构

```
Amplipost/
├── CLAUDE.md                          # Claude Code 读取的项目指令（速查表）
├── AGENTS.md                          # 本文件，跨工具架构说明
├── SPEC.md                            # 完整系统规格（人类可读）
├── memory.md                          # 长期记忆（发布记录/内容指纹/风控日志/用户偏好）
├── publishers/                        # Skill 脚本（只读，仅执行发布）
│   ├── xianyu-publisher/
│   ├── xhs-publisher/
│   ├── bilibili-publisher/
│   └── douyin-publisher/
└── .claude/
    ├── CLAUDE.md                      # 补充指令
    ├── agents/
    │   ├── content-coordinator.md    # 主 Agent（生成 + 调度 + 报告）
    │   ├── content-reviewer.md       # subagent：独立内容质量评审
    │   └── publish-guard.md          # subagent：发布风控拦截
    ├── hooks/
    │   ├── pre-publish-check.py      # PreToolUse hook（违禁词/emoji）
    │   └── post-publish-verify.py    # PostToolUse hook（结果验证/日志）
    └── settings.json                  # hooks 注册 + 权限配置
```
