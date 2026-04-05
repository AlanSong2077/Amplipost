#!/usr/bin/env python3
"""
抖音图文自动发布脚本 - Scrapling 增强版
改进点：
1. Scrapling 预检反爬
2. 自适应选择器
3. 增强容错机制
4. 更好的上传流程
"""

import asyncio
import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
from typing import Optional, List

# ── 配置 ──────────────────────────────────────────────────────────────────────
DEFAULT_PROFILE = os.path.expanduser("~/.catpaw/douyin_browser_profile")
PUBLISH_URL = "https://creator.douyin.com/creator-micro/content/upload?default-tab=image-text"


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


def validate_title(title: str, max_len: int = 20) -> str:
    if len(title) > max_len:
        truncated = title[:max_len]
        print(f"[WARN] 标题过长（{len(title)}字），已截断为: {truncated}")
        return truncated
    return title


# ── 配图生成 ──────────────────────────────────────────────────────────────────

def auto_generate_images(title: str, topic: str, output_dir: str, count: int = 3) -> List[str]:
    """自动生成配图"""
    script = Path(__file__).parent / "generate_images.py"
    if not script.exists():
        return []
    
    print(f"[INFO] 自动生成配图（话题：{topic}）...")
    try:
        result = subprocess.run(
            [sys.executable, str(script),
             "--title", title, "--topic", topic,
             "--point1", f"{topic}要点一",
             "--point2", f"{topic}要点二",
             "--point3", f"{topic}要点三",
             "--output-dir", output_dir, "--count", str(count)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            paths = [os.path.join(output_dir, f"card_{i}.jpg") for i in range(1, count+1)]
            existing = [p for p in paths if os.path.exists(p)]
            print(f"[INFO] 自动生成 {len(existing)} 张配图")
            return existing
    except Exception as e:
        print(f"[WARN] 配图生成失败: {e}")
    return []


# ── 元素查找 ──────────────────────────────────────────────────────────────────

async def find_element_robust(page, selectors: List[str], timeout_ms: int = 5000) -> Optional[object]:
    """自适应元素查找"""
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if await el.count() > 0 and await el.is_visible(timeout=1000):
                return el
        except Exception:
            continue
    return None


# ── 核心发布流程 ─────────────────────────────────────────────────────────────

async def upload_images(page, image_paths: List[str]) -> bool:
    """上传图片"""
    if not image_paths:
        print("[INFO] 未指定图片")
        return False
    
    valid_paths = [p for p in image_paths if os.path.exists(p)]
    if not valid_paths:
        print("[WARN] 没有有效的图片文件")
        return False
    
    print(f"[STEP] 上传 {len(valid_paths)} 张图片...")
    
    try:
        # 暴露 file input
        await page.evaluate("""
            document.querySelectorAll('input[type="file"]').forEach(inp => {
                Object.assign(inp.style, {
                    display: 'block', opacity: '1', position: 'fixed',
                    top: '0', left: '0', width: '100px', height: '100px', zIndex: '99999'
                });
            });
        """)
        
        file_input = page.locator('input[type="file"][accept*="image"]').first
        if await file_input.count() == 0:
            file_input = page.locator('input[type="file"]').first
        
        await file_input.set_input_files(valid_paths)
        await page.wait_for_timeout(3000)
        print("[INFO] 图片上传完成")
        return True
    except Exception as e:
        print(f"[WARN] 图片上传失败: {e}")
        return False


async def fill_title(page, title: str) -> bool:
    """填写标题"""
    print(f"[STEP] 填写标题: {title}")
    
    selectors = [
        "input.semi-input",
        "input[placeholder*='标题']",
        "input[class*='title']",
    ]
    
    el = await find_element_robust(page, selectors)
    if el:
        await el.fill(title)
        print("[INFO] 标题填写成功")
        return True
    
    # JS 降级
    try:
        result = await page.evaluate("""(title) => {
            const inp = document.querySelector('input.semi-input');
            if (!inp) return 'not found';
            inp.value = title;
            inp.dispatchEvent(new Event('input'));
            return 'filled';
        }""", title)
        print(f"[INFO] JS 填写标题: {result}")
        return result == 'filled'
    except Exception:
        return False


async def fill_content(page, content: str) -> bool:
    """填写正文"""
    print(f"[STEP] 填写正文（{len(content)} 字）...")
    
    selectors = [
        "[contenteditable='true']",
        ".zone-container.editor-kit-container",
        "[class*='editor']",
    ]
    
    el = await find_element_robust(page, selectors)
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
            await page.evaluate("navigator.clipboard.writeText(arguments[0])", content)
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


async def add_topics(page, topics: List[str]) -> bool:
    """添加话题"""
    if not topics:
        return True
    
    print(f"[STEP] 添加话题: {topics}")
    
    try:
        # 找到编辑器
        editor = page.locator("[contenteditable='true']").first
        if not await editor.count() > 0:
            return False
        
        for topic in topics:
            # 输入 #话题
            await editor.click()
            await page.keyboard.type(f"#{topic}", delay=30)
            await page.wait_for_timeout(500)
            
            # 尝试按回车选择
            try:
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(300)
            except Exception:
                pass
        
        print("[INFO] 话题添加完成")
        return True
    except Exception as e:
        print(f"[WARN] 添加话题失败: {e}")
        return False


async def click_publish(page) -> bool:
    """点击发布按钮"""
    print("[STEP] 点击发布...")
    
    selectors = [
        "button.button-dhlUZE.primary-cECiOJ",
        "button:has-text('发布')",
        "button:has-text('立即发布')",
        "[class*='publish'] button",
    ]
    
    el = await find_element_robust(page, selectors)
    if el:
        await el.click()
        print("[INFO] 发布按钮点击成功")
        return True
    
    # JS 降级
    try:
        result = await page.evaluate("""() => {
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
    images: Optional[List[str]] = None,
    topics: Optional[List[str]] = None,
    auto_generate: bool = False,
    profile_dir: str = DEFAULT_PROFILE,
    headless: bool = False,
    workspace: str = "/tmp"
):
    """抖音图文发布主流程"""
    title = validate_title(title)
    profile_dir = os.path.expanduser(profile_dir)
    Path(profile_dir).mkdir(parents=True, exist_ok=True)
    clear_profile_locks(profile_dir)
    
    print(f"[INFO] Profile: {profile_dir}")
    
    # Scrapling 预检
    print("[SCRAPLING] 预检抖音页面...")
    precheck = try_scrapling_precheck(PUBLISH_URL)
    if precheck["accessible"]:
        print(f"[SCRAPLING] ✅ 页面可访问: {precheck.get('title', '')[:50]}")
    else:
        print(f"[SCRAPLING] ⚠️ 预检结果: {precheck.get('error', 'unknown')[:80]}")
    
    # 自动生成图片
    if auto_generate and not images:
        images = auto_generate_images(title, topics[0] if topics else "话题", workspace)
    
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
            print("[ERROR] 需要登录！请先对我说 '登录抖音'")
            await context.close()
            return False
        
        # 上传图片
        if images:
            await upload_images(page, images)
            await page.wait_for_timeout(2000)
        
        # 截图初始
        await page.screenshot(path=os.path.join(workspace, "douyin_01_initial.png"))
        
        # 填写标题
        await fill_title(page, title)
        await page.wait_for_timeout(300)
        
        # 填写正文
        await fill_content(page, content)
        await page.wait_for_timeout(300)
        
        # 添加话题
        if topics:
            await add_topics(page, topics)
        
        # 截图填写后
        await page.screenshot(path=os.path.join(workspace, "douyin_02_filled.png"))
        
        # 点击发布
        if not await click_publish(page):
            print("[ERROR] 发布按钮点击失败")
            await context.close()
            return False
        
        # 等待结果
        await page.wait_for_timeout(5000)
        
        # 截图最终
        await page.screenshot(path=os.path.join(workspace, "douyin_03_final.png"))
        print(f"[INFO] 最终 URL: {page.url}")
        
        success = "success" in page.url or "published" in page.url
        if success:
            print("[SUCCESS] 🎉 抖音发布成功！")
        else:
            print("[INFO] 请查看截图确认发布状态")
        
        await context.close()
        return success


# ── CLI ──────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="抖音图文发布 - Scrapling 增强版")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--title", help="作品标题")
    group.add_argument("--content-file", metavar="FILE", help="JSON 文件路径")
    parser.add_argument("--content", default=None, help="正文描述")
    parser.add_argument("--images", help="图片路径（逗号分隔）")
    parser.add_argument("--topics", nargs="+", help="话题标签")
    parser.add_argument("--auto-generate", action="store_true", help="自动生成配图")
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
            images = data.get("images", args.images.split(",") if args.images else None)
            topics = data.get("topics", args.topics)
        except Exception as e:
            print(f"[ERROR] 读取 content.json 失败: {e}")
            sys.exit(1)
    else:
        if not args.content:
            print("[ERROR] 使用 --title 模式时，--content 为必填项")
            sys.exit(1)
        title = validate_title(args.title)
        content = args.content
        images = args.images.split(",") if args.images else None
        topics = args.topics
    
    print("=" * 60)
    print("  抖音图文发布 - Scrapling 增强版")
    print(f"  标题: {title}")
    print(f"  正文: {content[:40]}...")
    print(f"  话题: {topics}")
    print("=" * 60)
    
    ok = asyncio.run(publish(
        title=title,
        content=content,
        images=images,
        topics=topics,
        auto_generate=args.auto_generate,
        profile_dir=args.profile,
        headless=args.headless,
        workspace=args.workspace,
    ))
    
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
