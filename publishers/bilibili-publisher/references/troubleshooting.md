# B站专栏自动发布 - 常见问题排查

## 问题一：「正在现有的浏览器会话中打开」

**原因**：profile 目录被另一个 Chrome 实例锁定（SingletonLock 文件存在）。

**解决**：
```bash
rm -f ~/.catpaw/bilibili_browser_profile/SingletonLock \
       ~/.catpaw/bilibili_browser_profile/SingletonCookie \
       ~/.catpaw/bilibili_browser_profile/SingletonSocket
```
脚本内部已自动清除这些锁文件，若仍报错说明有其他 Chrome 进程占用该 profile，关闭后重试。

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

**原因**：B站正文编辑器是 **ProseMirror（tiptap）富文本 contenteditable div**，Playwright 的 `fill()` 对其无效。

**当前解决方案（已内置于脚本）**：
1. 聚焦编辑器 → `Meta+a` 全选 → `Backspace` 清空
2. `document.execCommand('insertText', false, text)`（保留换行，最可靠）
3. 降级：剪贴板 paste → `Meta+v`
4. 终极降级：逐段 `keyboard.type()`

**若仍失败**：检查 `bilibili_before_publish.png` 截图，确认编辑器是否已正确加载。

---

## 问题四：标题填写失败

**原因**：B站专栏标题是一个 `textarea.title-input__inner`（不是 input！），若 Vue 未正确响应，标题不会保存。

**解决**：
- 脚本已包含 `dispatchEvent('input')` 触发 Vue 响应式更新
- 若仍失败，检查截图确认 textarea 中确实有文字
- 注意：某些情况下需要先点击 textarea 再填写

---

## 问题五：编辑器 iframe 加载超时

**原因**：B站专栏编辑器在 `iframe[src*='read-editor']` 内，若网络慢或页面结构变化，可能超时。

**解决**：
- 当前超时设置 20 秒，可在脚本中调大 `timeout_ms`
- 也可能是登录失败导致页面停留在其他页面，检查 URL 是否为 `new-edit`

---

## 问题六：发布按钮点击后无反应

**原因**：发布按钮在 iframe 内部，且可能需要滚动到可见区域才能点击。

**解决**：
- 脚本已包含 `scroll_into_view_if_needed()`
- 降级方案：使用 JS 直接调用 `button.click()`
- 确认当前处于 iframe 内（检查 `frame.url` 是否含 `read-editor`）

---

## 问题七：发布成功弹窗未检测到

**可能原因**：
1. B站专栏发布后不跳转 URL，而是显示「你的专栏已提交成功」弹窗
2. 弹窗文字检测逻辑可能因页面结构变化失效

**解决**：
1. 弹窗在 iframe 内，检查 `frame.evaluate()` 的文字检测结果
2. 也检查主页面文字：「提交成功」「发布成功」
3. 截图 `bilibili_after_publish.png` 确认实际状态
4. 只要脚本未报错返回 false，即使未检测到弹窗也视为提交成功（B站机器审核中）

---

## 问题八：登录态失效，每次都要重新登录

**原因**：profile 目录被误删，或 B站强制重新登录（账号风控）。

**解决**：
- 确认 `~/.catpaw/bilibili_browser_profile/` 目录存在且包含登录状态文件
- 若目录为空或状态丢失，首次运行会自动触发登录流程（等待 120 秒）
- 若频繁需要重新登录，可能是 B站风控，建议使用较老但稳定的账号

---

## 问题九：新账号无法发布专栏

**原因**：B站专栏发布功能对账号等级有要求，通常需要 Lv2 以上。

**解决**：
- 先提升账号等级：每日签到、观看视频、投稿稿件（可投普通视频而非专栏）
- 或联系 B站客服申请专栏功能解锁

---

## 问题十：审核时间过长

**原因**：B站专栏机器审核通常数分钟到数小时，人工抽审可能更久。

**解决**：
- 截图确认「提交成功」即表示已进入审核队列，无需等待审核完成
- 若超过 24 小时仍未发布，联系 B站客服查询审核状态

---

## 问题十一：URL 跳转异常（停留在编辑页）

**可能原因**：
1. 内容触发了某种风控（内容违规检测）
2. 账号风控

**解决**：
1. 查看 `bilibili_after_publish.png` 截图确认实际状态
2. 手动刷新页面检查是否已发布（查看「稿件管理」）
3. 缩短内容或移除可能违规的表述后重试
