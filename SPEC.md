# Amplipost 系统规格 (SPEC)

版本：1.1
更新：2026-04-16

---

## 1. 系统目标

用户输入一句话，Amplipost 自动完成：内容生成 → 配图处理 → 合规检查 → 发布执行 → 结果汇报。

**不在目标范围内：**
- 数据分析、效果追踪（当前版本不做）
- 视频内容生成
- 付费广告投放

---

## 2. 输入规格

### 最小输入（Agent 可从中推断其余一切）

```
"帮我发小红书，主题是 AI 工具推荐"
```

### 完整输入（用户可选择性提供）

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| 平台 | 枚举 | 否 | xianyu / xhs / bilibili / douyin，可多选；不填则 Agent 推断 |
| 主题/商品名 | string | 是 | 内容核心 |
| 正文 | string | 否 | 有则直接用，无则 Agent 生成 |
| 图片路径 | string[] | 否 | 有则上传，无则 Agent 自动处理 |
| 价格 | number | 闲鱼必填 | 商品售价（元） |
| 新旧程度 | 枚举 | 闲鱼必填 | 全新/99新/95新/9成新/8成新/7成新/6成新及以下 |

---

## 3. 输出规格

### 成功输出

```
发布完成。

| 平台   | 状态   |
|--------|--------|
| 小红书 | 已发布 |
| 抖音   | 审核中 |
```

### 失败输出

```
发布完成（部分失败）。

| 平台   | 状态   | 原因               |
|--------|--------|--------------------|
| 小红书 | 已发布 |                    |
| B站    | 失败   | 登录态失效，请重新扫码 |
```

**不输出：** 废话、「还需要什么帮助吗」、中间过程的确认请求。

---

## 4. 各平台内容规格

### 4.1 闲鱼

| 字段 | 规格 |
|------|------|
| 标题 | 10-30字，格式：【新旧程度】商品名 核心规格 |
| 描述 | 状态描述 + 核心卖点 + 使用情况 |
| 价格 | 必填，纯数字 |
| 新旧程度 | 必填，见枚举值 |
| 图片 | 可选，jpg/png，≤5MB/张 |

**违禁词替换表（必须执行）：**

| 原词 | 替换 |
|------|------|
| 高仿 | 复刻 |
| A货 | 正品 |
| 全网最低 | 优惠价 |
| 假货 | 特价商品 |
| 仿品 | 同款 |
| 代购 | 自购 |

### 4.2 小红书

| 字段 | 规格 |
|------|------|
| 标题 | ≤20字 |
| 正文 | 200-300字 |
| 结构 | 痛点共鸣(30-50字) → 干货(120-160字) → 收尾(30-50字) → 互动引导(20-30字) |
| 风格 | 第一人称，口语化，真人感，有情绪 |
| 图片 | 可选；无图使用文字配图模式（小红书 AI 自动生成） |
| 禁止 | emoji、极限词（最好/第一/绝对）、AI感词汇（综上所述/不禁感叹/深度剖析）、虚假数据 |

**标题公式（选一）：**
- 数字干货型：`X个让你...的方法`
- 痛点解答型：`为什么你...？`
- 亲历分享型：`我用了X个月才明白...`
- 对比反差型：`别人...，而我...`

**生成要点：**
- 开头第一句必须是强共鸣句或强钩子，不能是背景介绍
- 干货部分用数字/步骤/对比让信息可操作，不写空话
- 结尾留一个真诚的互动问题，不写「欢迎关注」

### 4.3 B站专栏

| 字段 | 规格 |
|------|------|
| 标题 | ≤40字，有信息量，避免「浅谈」「简析」等模糊词 |
| 正文 | 800-1500字 |
| 结构 | 引言(100-150字) → 核心分析(200-300字) → 干货(300-500字) → 误区(150-200字) → 互动(100-150字) |
| 风格 | 专业、有数据支撑、逻辑严密，面向理性用户 |
| 标签 | 3-5个相关话题 |
| 禁止 | emoji、AI感词（深度剖析/不禁感叹/综上所述）、极限词、直接联系方式、站外导流 |
| 审核 | 提交后进入机器审核，通常数分钟到数小时 |

**生成要点：**
- 引言用具体场景或数据切入，不用「随着...的发展」
- 每个论点后接支撑数据或案例
- 误区章节点出真正的认知盲区
- 结尾提出一个开放性问题引导评论

### 4.4 抖音图文

| 字段 | 规格 |
|------|------|
| 标题 | ≤30字 |
| 正文 | 150-500字 |
| 结构 | 强钩子(15-30字) → 核心干货2-4点(100-300字) → 互动引导(30-50字) → #话题标签 |
| 风格 | 短句，口语，强钩子开场，像朋友聊天 |
| 图片 | **必须**，1-35张，1080×1080 JPG；无图时调用 generate_images.py |
| 话题 | 正文末尾 3-5 个 `#关键词`，触发下拉选择 |
| 禁止 | emoji、极限词 |
| 审核 | 提交后进入机器审核 |

**生成要点：**
- 开头15字内制造悬念或反常识认知
- 干货用「1. 2. 3.」清晰分点，每点一句话说清楚

---

## 5. 图片处理规格

### 决策树

```
用户提供了图片路径？
├─ 是 → 验证文件存在且格式合法 → 使用
└─ 否
    ├─ 平台=抖音 → 调用 generate_images.py 生成信息图
    ├─ 平台=小红书 → 不传 --image，使用文字配图模式
    └─ 平台=闲鱼/B站 → 无图发布，不阻塞
```

### generate_images.py 调用规格

```bash
python3 {DOUYIN_SKILL_DIR}/scripts/generate_images.py \
  --topic  "{内容主题}" \
  --title  "{文章标题}" \
  --point1 "{要点1}" \
  --point2 "{要点2}" \
  --point3 "{要点3}"
```

输出：3张 1080×1080 JPG，路径写入 `~/.catpaw/douyin_images/`

### 合法图片格式

- 闲鱼：jpg / png（≤5MB/张）
- 小红书：png / jpg / jpeg / webp（不支持 gif）
- 抖音：jpg / jpeg / png / bmp / webp（不支持 gif）

---

## 6. 发布调用规格

### 6.1 小红书：xiaohongshu-mcp MCP Server

小红书不再使用 Python 脚本，改为调用本地 MCP Server。

**前置检查：**
```bash
# 检查服务是否运行
curl -s --max-time 3 -X POST http://localhost:18060/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"check_login_status","arguments":{}},"id":1}'
# 无响应 → 服务未启动，提示用户手动启动
```

**发布图文：**
```bash
# 有图
curl -s -X POST http://localhost:18060/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "publish_content",
      "arguments": {
        "title": "{title}",
        "content": "{content}",
        "images": ["{img_absolute_path}"],
        "tags": ["{tag1}", "{tag2}"]
      }
    },
    "id": 1
  }'

# 无图（文字配图模式）
curl -s -X POST http://localhost:18060/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "tools/call",
    "params": {
      "name": "publish_content",
      "arguments": {
        "title": "{title}",
        "content": "{content}",
        "images": [],
        "tags": ["{tag1}", "{tag2}"]
      }
    },
    "id": 1
  }'
```

**成功判断：**
```python
def is_xhs_success(response_json: dict) -> bool:
    result = response_json.get("result", {})
    if result.get("isError"):
        return False
    text = result.get("content", [{}])[0].get("text", "")
    return "发布成功" in text or "success" in text.lower()
```

### 6.2 其他平台：Python 脚本

**路径查找顺序（闲鱼/B站/抖音）：**

```python
SKILL_BASE = os.path.expanduser("~/.openclaw/skills")
LOCAL_BASE  = os.path.join(os.getcwd(), "publishers")

def find_script(platform):
    name = f"{platform}-publisher"
    script = f"{platform}_publish.py"
    paths = [
        f"{SKILL_BASE}/{name}/scripts/{script}",
        f"{LOCAL_BASE}/{name}/scripts/{script}",
    ]
    for p in paths:
        if os.path.isfile(p):
            return p
    return None  # → 跳过该平台，报告未安装
```

**闲鱼：**
```bash
python3 $SCRIPT \
  --title       "【{condition}】{product_name}" \
  --description "{description}" \
  --price       "{price}" \
  --new-degree  "{condition}" \
  [--image      "{image_path}"]
```

**B站：**
```bash
python3 $SCRIPT \
  --title "{title}" \
  --content "{content}" \
  [--tags "{tag1},{tag2},{tag3}"]
```

**抖音：**
```bash
python3 $SCRIPT \
  --title   "{title}" \
  --content "{content}" \
  --images  "{img1},{img2},{img3}"
```

### 多平台发布顺序

商品类：闲鱼 → 小红书
干货/经验类：小红书 → 抖音 → B站
营销推广类：小红书 → 抖音

每个平台间等待 **15 秒**（避免平台判定重复内容）。

---

## 7. 内容准出规格

内容生成完成后，Agent 必须执行以下检查，全部通过才能进入发布阶段。**不通过则原地重写，不询问用户，不展示草稿。**

### 7.1 通用检查（所有平台）

| 检查项 | 通过标准 | 不通过时 |
|--------|---------|---------|
| 字数 | 在平台规定范围内 | 增删内容至合规 |
| 禁用词 | 无 emoji、无极限词、无 AI 感词汇 | 替换或删除 |
| 闲鱼违禁词 | 无高仿/A货/假货/仿品/全网最低/代购 | 按替换表替换 |
| 钩子强度 | 第一句话能让目标用户停下来看 | 重写开头 |
| 信息密度 | 读完有实质收获，不是空话套话 | 补充具体干货 |
| 真实感 | 像真人说话，不像 AI 模板 | 口语化改写 |

### 7.2 平台专项检查

| 平台 | 专项检查项 | 通过标准 |
|------|-----------|---------|
| 小红书 | 结构完整 | 含痛点/干货/收尾/互动四段 |
| 小红书 | 标题公式 | 符合四种公式之一 |
| B站 | 结构完整 | 含引言/分析/干货/误区/互动五段 |
| B站 | 字数达标 | ≥800字 |
| 抖音 | 话题标签 | 正文末尾有 3-5 个 # 话题 |
| 闲鱼 | 价格存在 | price 字段非空 |
| 闲鱼 | 新旧程度存在 | condition 字段非空且在枚举值内 |

### 7.3 重写上限

每个平台最多重写 **2 次**。2 次仍不通过，跳过该平台，在最终报告中说明原因。

---

## 8. 错误处理规格

| 错误类型 | Agent 行动 | 是否询问用户 |
|---------|-----------|------------|
| 脚本不存在 | 跳过该平台，报告「未安装 {platform}-publisher Skill」 | 否 |
| 登录态失效 | 停止，告知用户去哪里重新扫码（90s 窗口期） | **是** |
| 内容含违禁词 | 生成时自动替换，继续执行 | 否 |
| 内容质量不达标 | 准出检查重写，最多 2 次，仍不通过则跳过 | 否 |
| 无图（抖音） | 调用 generate_images.py，继续执行 | 否 |
| 网络超时（偶发） | 等待 30 秒，重试，最多 3 次 | 否 |
| 网络超时（持续） | 停止，报告网络问题 | 否 |
| 发布失败（可修复） | 修复后重试，最多 3 次 | 否 |
| 发布失败（不可修复） | 报告具体原因（分析脚本 stderr） | 否 |

---

## 9. Hook 规格

### PreToolUse[Bash] — 发布前合规检查

**触发条件：** 即将执行包含 `*_publish.py` 的 Bash 命令（闲鱼/B站/抖音）

> 注意：小红书发布改为 MCP curl 调用（`http://localhost:18060/mcp`），不经过此 hook。
> 小红书的合规检查在 content-coordinator 生成内容阶段完成。

**输入（stdin JSON）：**
```json
{
  "tool_name": "Bash",
  "tool_input": { "command": "python3 ... xianyu_publish.py ..." }
}
```

**检查项：**
1. 闲鱼命令 → 检测违禁词，有则 exit 2 阻止
2. B站/抖音命令 → 检测 emoji，有则 exit 2 阻止
3. 任意命令 → 检测极限词，有则输出 warning（exit 0，不阻止）

**输出（stdout JSON，exit 2 时）：**
```json
{ "continue": false, "reason": "检测到违禁词「高仿」，请替换为「复刻」后重试" }
```

### PostToolUse[Bash] — 发布后结果验证

**触发条件：** 包含 `*_publish.py` 的 Bash 命令执行完成

**输入（stdin JSON）：**
```json
{
  "tool_name": "Bash",
  "tool_input": { "command": "..." },
  "tool_response": { "stdout": "...", "stderr": "...", "exit_code": 0 }
}
```

**行动：**
- 按平台检测成功标志
- 写入日志 `~/.amplipost/logs/publish_YYYYMMDD.log`
- 始终 exit 0（后置 hook 不阻止）

---

## 10. 文件结构

```
Amplipost/
├── CLAUDE.md              ← Claude Code 项目指令（速查表）
├── AGENTS.md              ← 跨工具架构说明（本文件由此引用）
├── SPEC.md                ← 本文件，完整系统规格
│
├── publishers/            ← Skill 脚本（只读，不可修改）
│   ├── xianyu-publisher/
│   │   ├── SKILL.md
│   │   ├── scripts/
│   │   └── references/
│   ├── xhs-publisher/
│   ├── bilibili-publisher/
│   └── douyin-publisher/
│
└── .claude/
    ├── CLAUDE.md          ← 补充指令
    ├── agents/
    │   └── content-coordinator.md   ← Agent 定义
    ├── hooks/
    │   ├── pre-publish-check.py     ← PreToolUse hook（Python，读 stdin JSON）
    │   └── post-publish-verify.py   ← PostToolUse hook（Python，读 stdin JSON）
    └── settings.json                ← hooks 注册
```

---

## 11. 已知限制

1. **登录态** — 首次使用各平台需手动扫码登录（90s 窗口期），之后自动复用
2. **B站/抖音审核** — 发布后进入机器审核，无法控制审核时长
3. **图片生成质量** — `generate_images.py` 生成的是信息图，不是摄影图；实物商品建议用户提供真实图片
4. **并发限制** — 多平台顺序发布，不支持真正并行（平台风控限制）
