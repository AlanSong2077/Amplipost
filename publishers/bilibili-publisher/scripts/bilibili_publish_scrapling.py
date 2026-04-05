#!/usr/bin/env python3
"""
B站专栏自动发布脚本 - Scrapling 增强版
改进点：
1. Scrapling 预检反爬
2. 自适应选择器
3. 增强容错机制
4. 更好的 iframe 处理
"""

import asyncio
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List

# ── 配置 ──────────────────────────────────────────────────────────────────────
DEFAULT_PROFILE = os.path.expanduser("~/.catpaw/bilibili_browser_profile")
PUBLISH_URL = "https://member.bilibili.com/platform/upload/text/new-edit"


# ── Scrapling 预检 ────────────────────────────────────────────────────────────

def try_scrapling_precheck(url: str, timeout: int = 30000) -> dict:
    """使用 Scrapling 检测页面可访问性"""
    try:
        from scrapling.fetchers import StealthyFetcher
        fetcher = StealthyFetcher(headless=True, timeout=timeout/1000)
        page = fetcher.fetch(url)
        return {
            "accessible": True,
            "title": page.css('title::text').get() or "",
            "url": url
        }
    except Exception as e:
        return {"accessible": False, "error": str(e)[:100]}


# ── 工具函数 ──────────────────────────────────────────────────────────────────

def clear_profile_locks(profile_dir: str):
    for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        try:
            os.remove(os.path.join(profile_dir, lock))
        except FileNotFoundError:
            pass


def load_content_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for key in ["title", "content"]:
        if key not in data:
            raise ValueError(f"content.json 缺少必填字段: {key}")
    return data


def validate_title(title: str, max_len: int = 30) -> str:
    if len(title) > max_len:
        truncated = title[:max_len]
        print(f"[WARN] 标题过长（{len(title)}字），已截断为: {truncated}")
        return truncated
    return title


# ── 元素查找 ──────────────────────────────────────────────────────────────────

async def find_element_robust(page_or_frame, selectors: List[str], timeout_ms: int = 5000) -> Optional[object]:
    """自适应元素查找"""
    for sel in selectors:
        try:
            el = page_or_frame.locator(sel).first
            if await el.count() > 0 and await el.is_visible(timeout=1000):
                return el
        except Exception:
            continue
    return None


async def js_click_text(page_or_frame, text: str) -> bool:
    """JS 查找包含文字的元素并点击"""
    script = """(text) => {
        const el = Array.from(document.querySelectorAll('*')).find(
            e => e.children.length === 0 && e.textContent.trim() === text
        ) || Array.from(document.querySelectorAll('button, div[role="button"]')).find(
            e => e.textContent.trim() === text
        );
        if (el) { el.click(); return 'clicked'; }
        return 'not found';
    }"""
    try:
        result = await page_or_frame.evaluate(script, text)
        return result == 'clicked'
    except Exception:
        return False


# ── iframe 处理 ────────────────────────────────────────────────────────────────

async def wait_for_editor_iframe(page, timeout_ms: int = 15000):
    """等待编辑器 iframe 加载完成"""
    print("[STEP] 等待编辑器 iframe 加载...")
    deadline = asyncio.get_event_loop().time() + timeout_ms / 1000
    
    while asyncio.get_event_loop().time() < deadline:
        for frame in page.frames:
            if "read-editor" in frame.url:
                try:
                    await frame.wait_for_selector("textarea.title-input__inner", timeout=3000)
                    print(f"[INFO] 编辑器 iframe 已就绪")
                    return frame
                except Exception:
                    pass
        await page.wait_for_timeout(500)
    
    print("[ERROR] 编辑器 iframe 加载超时")
    return None


# ── 核心发布流程 ─────────────────────────────────────────────────────────────

async def fill_title(frame, title: str) -> bool:
    """填写标题"""
    print(f"[STEP] 填写标题: {title[:30]}...")
    
    selectors = [
        "textarea.title-input__inner",
        "textarea[placeholder*='标题']",
        "input.title-input__inner",
        "[class*='title-input']",
    ]
    
    el = await find_element_robust(frame, selectors)
    if el:
        await el.fill(title)
        print("[INFO] 标题填写成功")
        return True
    
    # JS 降级
    try:
        result = await frame.evaluate("""(title) => {
            const ta = document.querySelector('textarea.title-input__inner');
            if (ta) { ta.value = title; ta.dispatchEvent(new Event('input')); return 'filled'; }
            return 'not found';
        }""", title)
        print(f"[INFO] JS 填写标题: {result}")
        return result == 'filled'
    except Exception as e:
        print(f"[WARN] JS 填写失败: {e}")
        return False


async def fill_content(frame, content: str) -> bool:
    """填写正文"""
    print(f"[STEP] 填写正文（{len(content)} 字）...")
    
    selectors = [
        "div.tiptap.ProseMirror",
        "div.ProseMirror",
        "[contenteditable='true']",
        "[class*='ProseMirror']",
    ]
    
    el = await find_element_robust(frame, selectors)
    if not el:
        print("[ERROR] 未找到正文编辑器")
        return False
    
    try:
        await el.click()
        await page.keyboard.press("Control+a")
        await page.keyboard.press("Backspace")
        await page.wait_for_timeout(200)
        
        # 剪贴板粘贴
        try:
            await frame.evaluate("navigator.clipboard.writeText(arguments[0])", content)
            await page.keyboard.press("Control+v")
            await page.wait_for_timeout(500)
            print("[INFO] 正文粘贴成功")
            return True
        except Exception:
            pass
        
        # 降级：逐段输入
        paragraphs = content.split('\n')
        for para in paragraphs:
            if para:
                await page.keyboard.type(para, delay=5)
            await page.keyboard.press("Enter")
        print("[INFO] 正文逐段输入完成")
        return True
        
    except Exception as e:
        print(f"[WARN] 正文填写失败: {e}")
        return False


async def add_tags(frame, tags: List[str]) -> bool:
    """添加话题标签"""
    if not tags:
        return True
    
    print(f"[STEP] 添加标签: {tags}")
    
    try:
        # 点击添加标签按钮
        tag_btn_selectors = [
            "button:has-text('添加标签')",
            "[class*='tag'] button",
            "button[class*='tag']",
        ]
        
        for sel in tag_btn_selectors:
            btn = frame.locator(sel).first
            if await btn.count() > 0:
                await btn.click()
                await page.wait_for_timeout(500)
                break
        
        # 输入标签
        for tag in tags:
            try:
                tag_input = frame.locator("input[placeholder*='标签'], input[class*='tag']").first
                if await tag_input.count() > 0:
                    await tag_input.fill(tag)
                    await page.keyboard.press("Enter")
                    await page.wait_for_timeout(300)
            except Exception as e:
                print(f"[WARN] 添加标签 '{tag}' 失败: {e}")
        
        print("[INFO] 标签添加完成")
        return True
    except Exception as e:
        print(f"[WARN] 添加标签失败: {e}")
        return False


async def click_publish(frame) -> bool:
    """点击发布按钮"""
    print("[STEP] 点击发布...")
    
    selectors = [
        "button:has-text('发布')",
        "button:has-text('立即发布')",
        "[class*='publish'] button",
    ]
    
    el = await find_element_robust(frame, selectors)
    if el:
        await el.click()
        print("[INFO] 发布按钮点击成功")
        return True
    
    # JS 降级
    try:
        result = await frame.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const btn = btns.find(b => ['发布', '立即发布'].includes(b.textContent.trim()));
            if (btn) { btn.click(); return 'clicked'; }
            return 'not found';
        }""")
        print(f"[INFO] JS 发布: {result}")
        return 'not found' not in result
    except Exception:
        return False


# ── 主流程 ────────────────────────────────────────────────────────────────────

async def publish(
    title: str,
    content: str,
    tags: Optional[List[str]] = None,
    profile_dir: str = DEFAULT_PROFILE,
    headless: bool = False,
    workspace: str = "/tmp"
):
    """
    B站专栏发布主流程
    """
    title = validate_title(title)
    profile_dir = os.path.expanduser(profile_dir)
    Path(profile_dir).mkdir(parents=True, exist_ok=True)
    clear_profile_locks(profile_dir)
    
    print(f"[INFO] Profile: {profile_dir}")
    
    # Scrapling 预检
    print("[SCRAPLING] 预检B站页面...")
    precheck = try_scrapling_precheck(PUBLISH_URL)
    if precheck["accessible"]:
        print(f"[SCRAPLING] ✅ 页面可访问: {precheck.get('title', '')[:50]}")
    else:
        print(f"[SCRAPLING] ⚠️ 预检结果: {precheck.get('error', 'unknown')[:80]}")
    
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-infobars",
            ],
            ignore_default_args=["--enable-automation"],
            viewport={'width': 1440, 'height': 900},
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 打开发布页
        print("[STEP 1] 打开发布页...")
        await page.goto(PUBLISH_URL, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        
        print(f"[INFO] 当前 URL: {page.url}")
        
        # 检查登录
        if "login" in page.url or "passport" in page.url:
            print("[ERROR] 需要登录！请先对我说 '登录B站'")
            await context.close()
            return False
        
        # 等待编辑器 iframe
        editor_frame = await wait_for_editor_iframe(page)
        if not editor_frame:
            await page.screenshot(path=os.path.join(workspace, "bilibili_error.png"))
            await context.close()
            return False
        
        # 截图初始
        await page.screenshot(path=os.path.join(workspace, "bilibili_01_initial.png"))
        
        # 填写标题
        if not await fill_title(editor_frame, title):
            print("[WARN] 标题填写有问题")
        await page.wait_for_timeout(300)
        
        # 填写正文
        if not await fill_content(editor_frame, content):
            print("[WARN] 正文填写有问题")
        await page.wait_for_timeout(300)
        
        # 添加标签
        if tags:
            await add_tags(editor_frame, tags)
        
        # 截图填写后
        await page.screenshot(path=os.path.join(workspace, "bilibili_02_filled.png"))
        
        # 点击发布
        if not await click_publish(editor_frame):
            print("[ERROR] 发布按钮点击失败")
            await context.close()
            return False
        
        # 等待结果
        await page.wait_for_timeout(5000)
        
        # 截图最终
        await page.screenshot(path=os.path.join(workspace, "bilibili_03_final.png"))
        print(f"[INFO] 最终 URL: {page.url}")
        
        success = "success" in page.url or "published" in page.url
        if success:
            print("[SUCCESS] 🎉 专栏发布成功！")
        else:
            print("[INFO] 请查看截图确认发布状态")
        
        await context.close()
        return success


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="B站专栏发布 - Scrapling 增强版")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--title", help="文章标题")
    group.add_argument("--content-file", metavar="FILE", help="JSON 文件路径")
    parser.add_argument("--content", default=None, help="文章正文")
    parser.add_argument("--tags", nargs="+", help="话题标签")
    parser.add_argument("--profile", default=DEFAULT_PROFILE, help="浏览器 profile")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--workspace", default="/tmp", help="截图保存目录")
    return parser.parse_args()


def main():
    args = parse_args()
    
    if args.content_file:
        try:
            data = load_content_file(args.content_file)
            title = validate_title(data["title"])
            content = data["content"]
            tags = data.get("tags", args.tags)
        except Exception as e:
            print(f"[ERROR] 读取 content.json 失败: {e}")
            sys.exit(1)
    else:
        if not args.content:
            print("[ERROR] 使用 --title 模式时，--content 为必填项")
            sys.exit(1)
        title = validate_title(args.title)
        content = args.content
        tags = args.tags
    
    print("=" * 60)
    print("  B站专栏发布 - Scrapling 增强版")
    print(f"  标题: {title}")
    print(f"  正文: {content[:40]}...")
    print(f"  标签: {tags}")
    print("=" * 60)
    
    ok = asyncio.run(publish(
        title=title,
        content=content,
        tags=tags,
        profile_dir=args.profile,
        headless=args.headless,
        workspace=args.workspace,
    ))
    
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
