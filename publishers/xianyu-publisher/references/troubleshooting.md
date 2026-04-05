# 故障排除指南

## 常见问题

### 1. 登录失效

**症状**：发布时提示需要登录

**解决方案**：
```bash
# 1. 删除旧登录态
rm -rf ~/.openclaw/browser_profiles/xianyu_default/

# 2. 重新登录
# 对我说 "登录闲鱼"
```

### 2. Playwright 未安装

**症状**：`Module not found: 'playwright'`

**解决方案**：
```bash
pip install playwright
playwright install chromium
```

### 3. 标题/价格填写失败

**症状**：提示"未找到标题输入框"

**可能原因**：
- 闲鱼页面改版（使用 contenteditable DIV 而非 input）

**解决方案**：
- 检查 `xianyu_publish.py` 中的选择器是否正确
- 新版闲鱼使用 `locator('[contenteditable="true"]')` 选择标题

### 4. 图片中文乱码

**症状**：生成的图片中文显示为方块

**解决方案**：
```python
from PIL import ImageFont
font = ImageFont.truetype("/System/Library/Fonts/STHeiti Light.ttc", 36)
```

详见 `image-generation.md`

### 5. 发布按钮点击无效

**症状**：点击发布按钮后页面无反应

**可能原因**：
- 按钮被 CSS 禁用（class 包含 `disabled`）
- 某些必填字段未填写

**解决方案**：
1. 检查表单是否完整填写
2. 检查是否有地理位置授权问题
3. 使用 `page.evaluate('...click()')` JS 方式点击

### 6. Cookies 过期

**症状**：提示登录失效，但 cookies 文件存在

**解决方案**：
```bash
rm ~/.openclaw/browser_profiles/xianyu_default/cookies.json
# 重新登录
```

## 调试方法

### 查看截图

发布失败时，系统会保存截图到 `/tmp/xianyu_*.png`

### 查看日志

添加 `--headless` 模式查看浏览器操作：
```bash
python3 scripts/xianyu_publish.py --title "测试" --description "测试" --price 100 --headless
```

### 检查页面元素

在浏览器控制台执行：
```javascript
// 查找所有输入框
document.querySelectorAll('input').forEach(i => console.log(i.type, i.placeholder, i.className))

// 查找标题输入
document.querySelector('[contenteditable="true"]')

// 查找发布按钮
Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('发布'))
```

## 日志文件

- 截图：`/tmp/xianyu_01_initial.png`
- 填写后：`/tmp/xianyu_02_after_fill.png`
- 发布后：`/tmp/xianyu_03_final.png`
- 错误：`/tmp/xianyu_error.png`

## 技术支持

如果问题持续：
1. 提供截图 `/tmp/xianyu_*.png`
2. 说明操作步骤
3. 描述预期 vs 实际结果
