# 小红书自动发布 - 常见问题排查

## 问题一：「正在现有的浏览器会话中打开」

**原因**：profile 目录被另一个 Chrome 实例锁定（SingletonLock 文件存在）。

**解决**：
```bash
rm -f ~/.catpaw/xhs_browser_profile/SingletonLock \
       ~/.catpaw/xhs_browser_profile/SingletonCookie \
       ~/.catpaw/xhs_browser_profile/SingletonSocket
```
脚本内部已自动清除，若仍报错说明有其他进程占用，关闭后重试。

---

## 问题二：playwright 安装失败 / 超时

**原因**：默认 PyPI 源在国内访问慢。

**解决**：使用阿里云镜像：
```bash
pip install playwright -i https://mirrors.aliyun.com/pypi/simple/
python3 -m playwright install chromium
```

---

## 问题三：正文填写失败 / 正文为空

**原因**：小红书正文编辑器是 **ProseMirror（tiptap）富文本 contenteditable div**，Playwright 的 `fill()` 对其无效。

**当前解决方案（已内置于脚本）**：
1. 聚焦编辑器 → `Meta+a` 全选 → `Backspace` 清空
2. `navigator.clipboard.writeText(content)` 写入剪贴板
3. `Meta+v` 粘贴（保留换行和特殊字符）
4. 降级：逐段 `keyboard.type()`

**若仍失败**：检查 `before_publish.png` 截图，确认编辑器是否已聚焦。

---

## 问题四：标题填写失败

**原因**：selector 失效，或图片上传未完成时标题 input 尚未渲染。

**解决**：
- 确认图片上传等待时间足够（当前 8s），可适当增加
- 检查 `input[placeholder*="标题"]` 是否仍有效（DevTools 确认）

---

## 问题五：图片上传后页面无变化

**原因**：上传等待时间不足，或图片格式不支持。

**解决**：
- 确认图片格式为 `.jpg .jpeg .png .webp`（不支持 `.gif`）
- 将 `upload_image` 中的 `wait_for_timeout(8000)` 改为更长时间（如 12000）

---

## 问题六：「文字配图」模式下标题/正文找不到

**原因**：「文字配图」页面的正文是 ProseMirror，但没有标题 input（标题在图文编辑页才有）。

**当前行为**：无图片时走文字配图模式，只有正文编辑器，无标题输入框。若需要标题，建议提供一张图片走图文模式。

---

## 问题七：发布后 URL 未跳转到 /success

**可能原因**：
1. 标题为空（小红书要求标题必填）
2. 图片上传未完成就点击了发布
3. 触发了风控验证

**解决**：
1. 确认 `--title` 参数不为空
2. 增加图片上传等待时间
3. 手动在浏览器中完成验证后重试

---

## 问题八：登录态失效，每次都要扫码

**原因**：profile 目录被误删，或小红书强制重新登录。

**解决**：
- 确认 `~/.catpaw/xhs_browser_profile/` 目录存在且有内容
- 若目录为空，首次运行会自动触发扫码登录流程（等待 90s）

---

## 问题九：`no_viewport=True` 导致截图异常

**原因**：部分环境下无头模式 + no_viewport 组合有问题。

**解决**：改用固定 viewport：
```python
# 将 no_viewport=True 替换为：
viewport={"width": 1440, "height": 900},
```
同时将 `--start-maximized` 从 args 中移除。

---

## 问题十：JS SyntaxError: Illegal return statement

**原因**：`page.evaluate()` 中的 JS 代码顶层不能有 `return`，必须包在 IIFE 中。

**正确写法**：
```python
# ❌ 错误
await page.evaluate("return document.title")

# ✅ 正确
await page.evaluate("(() => { return document.title })()")
# 或传函数字符串
await page.evaluate("document.title")
```
