---
name: xianyu-publisher
description: 闲鱼自动发布助手。自动化在闲鱼平台发布商品，支持 AI 生成配图、自动填写表单、违禁词过滤。触发词：发布闲鱼、闲鱼上架、自动发布二手商品、卖闲置、闲鱼商品发布、闲鱼助手、在闲鱼发布商品。
---

# 闲鱼自动发布 Skill

> 适配新版闲鱼 (goofish.com)，支持 AI 生成商品配图、中文显示、多种商品分类。

## 功能概述

1. **自动发布** - 自动填写标题、价格、描述、新旧程度
2. **AI 配图** - 自动生成支持中文的商品图片
3. **违禁词过滤** - 自动替换敏感词
4. **登录态保存** - 首次登录后自动保存 cookies

## 触发词

- "发布闲鱼"
- "闲鱼上架"
- "卖闲置"
- "帮我发布商品"
- "自动发布二手"
- "闲鱼助手"

## 快速开始

### 1. 首次登录

```text
对我说 "登录闲鱼"
```

会打开浏览器让你登录闲鱼，自动保存登录状态。

### 2. 发布商品

**简单模式：**
```text
发布闲鱼：iPhone 15 Pro Max，256GB，5999元，95新
```

**完整模式：**
```text
帮我发布闲鱼：
- 商品：MacBook Pro 14寸
- 描述：M3 Pro芯片，18G+512G，无划痕
- 价格：9999
- 新旧：95新
- 图片：/tmp/macbook.jpg
```

**自动配图模式：**
```text
帮我发布闲鱼（自动生成图片）：
- 商品：中美港股财报数据
- 描述：Excel格式，83列财务指标
- 价格：2
- 新旧：全新
```

## 输入参数

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| 商品名称 | 是 | 商品标题 | iPhone 15 Pro Max |
| 价格 | 是 | 售价（元） | 5999 |
| 描述 | 否 | 商品详情 | 256GB，电池健康98% |
| 新旧程度 | 否 | 全新/95新/9成新等 | 95新 |
| 图片 | 否 | 本地路径或自动生成 | /tmp/iphone.jpg |

### 新旧程度选项

- 全新、99新、95新、9成新、8成新、7成新、6成新及以下

## 内部结构

```
xianyu-publisher/
├── SKILL.md                      # 本文件
├── references/
│   ├── content-rules.md          # 发布规则和违禁词
│   ├── troubleshooting.md        # 故障排除
│   └── image-generation.md       # AI 配图指南
└── scripts/
    ├── xianyu_publish.py         # 核心发布脚本 (Playwright)
    └── auto_publish.py           # 高级发布（模板+违禁词）
```

## 核心脚本用法

### xianyu_publish.py

```bash
python3 scripts/xianyu_publish.py \
  --title "【95新】iPhone 14 128GB" \
  --description "功能正常，欢迎咨询" \
  --price "2000" \
  --new-degree "95新" \
  --image "/tmp/product.jpg" \
  --profile "default"
```

### 自动配图

使用 `references/image-generation.md` 中的代码生成支持中文的图片。

## 违禁词处理

自动替换以下敏感词：
- 高仿 → 复刻
- A货 → 正品
- 全网最低 → 优惠价

详见 `references/content-rules.md`

## 故障排除

详见 `references/troubleshooting.md`

常见问题：
1. **登录失效** → 对我说"登录闲鱼"重新登录
2. **发布失败** → 检查 cookies 是否过期
3. **图片中文乱码** → 使用 PIL 中文字体（STHeiti Light.ttc）

## 更新日志

- 2026-03-23: 适配新版 goofish.com，修复 contenteditable 标题输入，添加中文配图支持
