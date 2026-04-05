#!/usr/bin/env python3
"""
小红书网页版自动发布脚本
用法：
  # 直接传参（带图片）
  python3 xhs_publish.py --title "标题" --content "正文" --image "/path/to/img.png"

  # 直接传参（无图片，使用文字配图）
  python3 xhs_publish.py --title "标题" --content "正文"

  # 从 JSON 文件读取
  python3 xhs_publish.py --content-file "/path/to/content.json"

content.json 格式：
  {
    "title": "笔记标题（≤20字）",
    "content": "正文内容（200-300字）",
    "image": "/path/to/image.png"   // 可选
  }
"""

import asyncio
import argparse
import json
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright

# ── 默认配置 ──────────────────────────────────────────────────────────────────
DEFAULT_PROFILE = os.path.expanduser("~/.catpaw/xhs_browser_profile")
PUBLISH_URL     = "https://creator.xiaohongshu.com/publish/publish?source=official"


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def truncate_title(title: str, max_len: int = 20) -> str:
    """截断标题到指定长度，超过才截断，不加..."""
    if len(title) <= max_len:
        return title  # 没超过，不截断
    
    # 超过才截断，直接截断不加...
    return title[:max_len]


def validate_title(title: str) -> str:
    """验证并修正标题长度"""
    if len(title) > 20:
        truncated = truncate_title(title, 20)
        print(f"[WARN] 标题过长（{len(title)}字），已截断为: {truncated}")
        return truncated
    
    return title


def clear_profile_locks(profile_dir: str):
    """清除 Chrome 单例锁文件，避免「正在现有会话中打开」错误"""
    for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        try:
            os.remove(os.path.join(profile_dir, lock))
        except FileNotFoundError:
            pass


def load_content_file(path: str) -> dict:
    """从 JSON 文件加载发布内容"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for key in ["title", "content"]:
        if key not in data:
            raise ValueError(f"content.json 缺少必填字段: {key}")
    return data


async def wait_for_login(page, timeout_ms=90000):
    """若当前在登录页，等待用户手动扫码登录"""
    if "login" not in page.url:
        return True
    print("[WARN] 未登录，请在弹出的浏览器窗口中手动扫码登录（等待最多 90 秒）...")
    try:
        await page.wait_for_url(lambda url: "login" not in url, timeout=timeout_ms)
        await page.wait_for_timeout(2000)
        print("[INFO] 登录成功！登录态已持久化，下次无需再登录。")
        return True
    except Exception:
        print("[ERROR] 登录超时，请重新运行脚本")
        return False


async def js_click_text(page, text: str) -> bool:
    """通用：JS 查找包含指定文字的元素并点击"""
    result = await page.evaluate("""(text) => {
        const el = Array.from(document.querySelectorAll('*')).find(
            e => e.children.length === 0 && e.textContent.trim() === text
        ) || Array.from(document.querySelectorAll('*')).find(
            e => e.textContent.trim() === text
        );
        if (el) { el.click(); return 'clicked'; }
        return 'not found';
    }""", text)
    return result == 'clicked'


async def switch_to_image_tab(page):
    """切换到「上传图文」Tab"""
    print("[STEP] 切换到「上传图文」Tab...")
    ok = await js_click_text(page, '上传图文')
    print(f"[INFO] 上传图文 tab: {'clicked' if ok else 'not found'}")
    await page.wait_for_timeout(1500)


async def upload_image(page, image_path: str) -> bool:
    """上传图片：暴露 file input 后注入文件，等待图片上传完成"""
    if not image_path or not os.path.exists(image_path):
        print(f"[WARN] 图片文件不存在: {image_path}")
        return False

    print(f"[STEP] 上传图片: {image_path}")
    try:
        # 暴露所有图片类型的 file input
        await page.evaluate("""
            document.querySelectorAll('input[type="file"]').forEach(inp => {
                Object.assign(inp.style, {
                    display: 'block', opacity: '1', position: 'fixed',
                    top: '0', left: '0', width: '100px', height: '100px', zIndex: '99999'
                });
            });
        """)
        file_input = page.locator('input[type="file"]').first
        await file_input.set_input_files(image_path)
        print("[INFO] 图片已注入，等待上传完成（8s）...")
        await page.wait_for_timeout(8000)
        return True
    except Exception as e:
        print(f"[WARN] 图片上传失败: {e}")
        return False


async def click_text_image_mode(page, text_for_image: str = "") -> bool:
    """
    文字配图完整流程：
    1. 点击「文字配图」按钮
    2. 在 ProseMirror 编辑器中输入文字
    3. 点击「生成图片」按钮
    4. 等待 AI 生成配图（约 3-5 秒）
    5. 点击「下一步」进入标题/正文填写页

    text_for_image: 用于生成配图的文字（建议一句话，20字以内）
                    若为空则使用正文前20字
    """
    print("[STEP] 点击「文字配图」进入编辑页...")
    ok = await js_click_text(page, '文字配图')
    print(f"[INFO] 文字配图按钮: {'clicked' if ok else 'not found'}")
    await page.wait_for_timeout(2000)

    # ── 在编辑器中输入文字 ──
    if text_for_image:
        print(f"[STEP] 在文字配图编辑器中输入: {text_for_image[:30]}")
        try:
            editor = page.locator('[contenteditable="true"].ProseMirror').first
            if await editor.count() > 0:
                await editor.click()
                await page.wait_for_timeout(300)
                await page.evaluate(
                    "(text) => { document.execCommand('insertText', false, text); }",
                    text_for_image
                )
                print("[INFO] 文字已输入到配图编辑器")
                await page.wait_for_timeout(500)
            else:
                print("[WARN] 未找到文字配图编辑器")
        except Exception as e:
            print(f"[WARN] 输入文字失败: {e}")

    # ── 点击「生成图片」按钮 ──
    print("[STEP] 点击「生成图片」...")
    try:
        gen_btn = page.locator('.edit-text-button').first
        if await gen_btn.count() > 0:
            await gen_btn.click()
            print("[INFO] 已点击「生成图片」")
        else:
            # JS 降级
            result = await page.evaluate("""(() => {
                const btn = document.querySelector('.edit-text-button');
                if (btn) { btn.click(); return 'clicked'; }
                return 'not found';
            })()""")
            print(f"[INFO] JS 点击生成图片: {result}")
    except Exception as e:
        print(f"[WARN] 点击生成图片失败: {e}")

    # ── 等待 AI 生成配图 ──
    print("[INFO] 等待 AI 生成配图（约 5 秒）...")
    await page.wait_for_timeout(5000)

    # ── 点击「下一步」进入编辑页 ──
    print("[STEP] 点击「下一步」...")
    # 录制数据中确认的 selector
    next_selectors = [
        'div.image-editor-container:nth-of-type(2) > div.overview-footer:nth-of-type(2) > button',
        'div.overview-footer button',
        'button:has-text("下一步")',
    ]
    clicked = False
    for sel in next_selectors:
        try:
            btn = page.locator(sel).first
            if await btn.count() > 0:
                await btn.click()
                print(f"[INFO] 已点击「下一步」({sel})")
                clicked = True
                break
        except Exception:
            pass

    if not clicked:
        # JS 降级：查找所有包含「下一步」文字的元素
        result = await page.evaluate("""(() => {
            const candidates = Array.from(document.querySelectorAll('button, div[class*="footer"] button'));
            const btn = candidates.find(b => b.textContent.trim() === '下一步');
            if (btn) { btn.click(); return 'js clicked'; }
            // 尝试通过 overview-footer 找
            const footer = document.querySelector('.overview-footer');
            if (footer) {
                const b = footer.querySelector('button');
                if (b) { b.click(); return 'footer btn clicked: ' + b.textContent.trim(); }
            }
            return 'not found';
        })()""")
        print(f"[INFO] JS 点击下一步: {result}")
        clicked = 'clicked' in result

    await page.wait_for_timeout(2000)
    return clicked


async def fill_title(page, title: str) -> bool:
    """填写标题：input[placeholder*=标题]"""
    print(f"[STEP] 填写标题: {title}")

    # Playwright locator
    for sel in [
        'input[placeholder*="标题"]',
        'input[placeholder*="填写标题"]',
        'input[class*="title"]',
    ]:
        try:
            el = page.locator(sel).first
            if await el.count() > 0:
                await el.scroll_into_view_if_needed()
                await el.click()
                await el.fill(title)
                print(f"[INFO] 标题已填写 ({sel})")
                return True
        except Exception:
            pass

    # JS 降级
    result = await page.evaluate("""(title) => {
        const inp = Array.from(document.querySelectorAll('input')).find(
            i => i.placeholder && i.placeholder.includes('标题')
        );
        if (!inp) return 'not found';
        inp.focus();
        inp.value = title;
        inp.dispatchEvent(new Event('input', {bubbles: true}));
        inp.dispatchEvent(new Event('change', {bubbles: true}));
        return 'js filled';
    }""", title)
    print(f"[INFO] JS 填写标题: {result}")
    return result != 'not found'


async def fill_content_prosemirror(page, content: str) -> bool:
    """
    填写 ProseMirror 富文本正文。
    策略：聚焦编辑器 → 全选清空 → 通过剪贴板粘贴（保留换行）
    """
    print(f"[STEP] 填写正文（{len(content)} 字）")

    # 找到编辑器
    editor_sel = 'div.tiptap.ProseMirror, div.ProseMirror, [contenteditable="true"][role="textbox"], [contenteditable="true"]'
    el = page.locator(editor_sel).first
    count = await el.count()
    if count == 0:
        print("[WARN] 未找到正文编辑器")
        return False

    await el.scroll_into_view_if_needed()
    await el.click()
    await page.wait_for_timeout(300)

    # 全选清空
    await page.keyboard.press("Meta+a")
    await page.keyboard.press("Backspace")
    await page.wait_for_timeout(200)

    # 通过 JS 写入剪贴板，再粘贴（最可靠，保留换行）
    try:
        await page.evaluate("""(text) => {
            return navigator.clipboard.writeText(text);
        }""", content)
        await page.keyboard.press("Meta+v")
        await page.wait_for_timeout(500)
        print("[INFO] 正文通过剪贴板粘贴成功")
        return True
    except Exception as e:
        print(f"[WARN] 剪贴板粘贴失败: {e}，尝试逐段输入...")

    # 降级：逐段 type（慢但可靠）
    try:
        paragraphs = content.split('\n')
        for i, para in enumerate(paragraphs):
            if para:
                await page.keyboard.type(para, delay=10)
            if i < len(paragraphs) - 1:
                await page.keyboard.press("Enter")
        print("[INFO] 正文逐段输入完成")
        return True
    except Exception as e:
        print(f"[WARN] 逐段输入失败: {e}")

    return False


async def click_publish(page) -> bool:
    """点击发布按钮"""
    print("[STEP] 点击发布按钮...")

    # Playwright locator
    for sel in ['button:has-text("发布")', 'button:has-text("立即发布")']:
        try:
            btn = page.locator(sel).first
            if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                await btn.scroll_into_view_if_needed()
                await btn.click()
                print(f"[INFO] 已点击发布 ({sel})")
                return True
        except Exception:
            pass

    # JS 降级
    result = await page.evaluate("""(() => {
        const btn = Array.from(document.querySelectorAll('button')).find(
            b => ['发布', '立即发布'].includes(b.textContent.trim())
        );
        if (btn) { btn.click(); return 'js clicked: ' + btn.textContent.trim(); }
        const all = Array.from(document.querySelectorAll('button')).map(b => b.textContent.trim()).filter(Boolean);
        return 'not found, buttons: ' + all.join(', ');
    })()""")
    print(f"[INFO] JS 点击发布: {result}")
    return "not found" not in result


# ── 主流程 ────────────────────────────────────────────────────────────────────

async def publish(title: str, content: str, image_path: str = None,
                  text_for_image: str = None,
                  profile_dir: str = DEFAULT_PROFILE, headless: bool = False,
                  workspace: str = None):
    """
    完整发布流程，返回 True 表示成功。

    三种模式：
    1. image_path 有值  → 上传图片模式
    2. text_for_image 有值 → 文字配图模式（AI 自动生成配图）
    3. 两者都为空       → 文字配图模式，用正文前20字生成配图
    """
    workspace = workspace or os.getcwd()
    screenshot_before = os.path.join(workspace, "before_publish.png")
    screenshot_after  = os.path.join(workspace, "after_publish.png")

    Path(profile_dir).mkdir(parents=True, exist_ok=True)
    clear_profile_locks(profile_dir)
    print(f"[INFO] Profile: {profile_dir}")

    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-infobars",
                "--start-maximized",
            ],
            ignore_default_args=["--enable-automation"],
            no_viewport=True,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )

        page = context.pages[0] if context.pages else await context.new_page()

        # ── 1. 打开发布页 ──
        print("[STEP 1] 打开发布页...")
        await page.goto(PUBLISH_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2500)

        # ── 2. 检查登录 ──
        if not await wait_for_login(page):
            await context.close()
            return False
        print(f"[INFO] 当前页面: {page.url}")

        # ── 3. 切换到「上传图文」Tab ──
        await switch_to_image_tab(page)

        # ── 4. 上传图片 或 进入文字配图模式 ──
        if image_path:
            uploaded = await upload_image(page, image_path)
            if not uploaded:
                print("[WARN] 图片上传失败，尝试继续...")
        else:
            # 文字配图模式：若未指定 text_for_image，用正文前20字
            img_text = text_for_image or content[:20]
            print(f"[INFO] 文字配图模式，配图文字: {img_text[:20]}")
            await click_text_image_mode(page, text_for_image=img_text)

        # ── 5. 填写标题 ──
        await fill_title(page, title)
        await page.wait_for_timeout(400)

        # ── 6. 填写正文 ──
        await fill_content_prosemirror(page, content)
        await page.wait_for_timeout(500)

        # ── 7. 截图（发布前确认）──
        await page.screenshot(path=screenshot_before)
        print(f"[INFO] 发布前截图: {screenshot_before}")

        # ── 8. 点击发布 ──
        ok = await click_publish(page)
        if not ok:
            print("[ERROR] 未找到发布按钮，请查看截图")
            await context.close()
            return False

        # ── 9. 等待跳转并截图 ──
        try:
            await page.wait_for_url(
                lambda url: "success" in url or "manage" in url,
                timeout=15000
            )
        except Exception:
            pass  # 超时也继续，看截图

        await page.wait_for_timeout(2000)
        await page.screenshot(path=screenshot_after)
        final_url = page.url
        print(f"[INFO] 发布后截图: {screenshot_after}")
        print(f"[INFO] 最终 URL: {final_url}")

        success = "success" in final_url or "manage" in final_url
        if success:
            print("[SUCCESS] 🎉 笔记发布成功！")
        else:
            print("[INFO] 请查看截图确认发布状态")

        await page.wait_for_timeout(2000)
        await context.close()
        return success


# ── CLI 入口 ──────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="小红书网页版自动发布脚本")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--title", help="笔记标题（与 --content 配合使用）")
    group.add_argument("--content-file", metavar="FILE",
                       help="从 JSON 文件读取发布内容（包含 title/content/image/text_for_image 字段）")
    parser.add_argument("--content",        default=None, help="笔记正文（--title 模式下必填）")
    parser.add_argument("--image",          default=None, help="图片路径（可选，与 --text-for-image 互斥）")
    parser.add_argument("--text-for-image", default=None,
                        help="文字配图模式：输入一句话，小红书 AI 自动生成配图（不传则用正文前20字）")
    parser.add_argument("--profile",   default=DEFAULT_PROFILE, help="browser profile 目录")
    parser.add_argument("--headless",  action="store_true", help="无头模式（不显示浏览器）")
    parser.add_argument("--workspace", default=None, help="截图保存目录（默认当前目录）")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.content_file:
        try:
            data = load_content_file(args.content_file)
            # 验证标题长度，不能超过20字
            title          = validate_title(data["title"])
            content        = data["content"]
            image_path     = data.get("image", args.image)
            text_for_image = data.get("text_for_image", getattr(args, 'text_for_image', None))
        except Exception as e:
            print(f"[ERROR] 读取 content.json 失败: {e}")
            sys.exit(1)
    else:
        if not args.content:
            print("[ERROR] 使用 --title 模式时，--content 为必填项")
            sys.exit(1)
        # 验证标题长度，不能超过20字
        title          = validate_title(args.title)
        content        = args.content
        image_path     = args.image
        text_for_image = getattr(args, 'text_for_image', None)

    mode = "上传图片" if image_path else f"文字配图（{text_for_image or '用正文前20字'}）"
    print("=" * 60)
    print("  小红书自动发布脚本")
    print(f"  标题: {title}")
    print(f"  正文: {content[:40]}..." if len(content) > 40 else f"  正文: {content}")
    print(f"  模式: {mode}")
    print("=" * 60)

    ok = asyncio.run(publish(
        title=title,
        content=content,
        image_path=image_path,
        text_for_image=text_for_image,
        profile_dir=args.profile,
        headless=args.headless,
        workspace=args.workspace,
    ))
    sys.exit(0 if ok else 1)
