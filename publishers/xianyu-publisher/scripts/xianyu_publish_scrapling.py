#!/usr/bin/env python3
"""
闲鱼商品发布脚本 - Scrapling 增强版
适配新版闲鱼 (goofish.com)

改进点：
1. Scrapling 预检反爬
2. 异步 Playwright API
3. 自适应选择器
4. 增强容错和重试
"""

import asyncio
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, List

# ── 配置 ──────────────────────────────────────────────────────────────────────
XIANYU_URL = "https://www.goofish.com/publish"
DEFAULT_TIMEOUT = 60000
DEFAULT_PROFILE = "~/.catpaw/xhs_browser_profile"  # 复用小红书的 profile


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
    """清除 Chrome 单例锁"""
    for lock in ["SingletonLock", "SingletonCookie", "SingletonSocket"]:
        try:
            os.remove(os.path.join(profile_dir, lock))
        except FileNotFoundError:
            pass


def get_cookies_file(profile_name: str = "default") -> str:
    """获取 cookies 文件路径"""
    cookie_dir = os.path.expanduser(f"~/.openclaw/browser_profiles/xianyu_{profile_name}")
    return os.path.join(cookie_dir, "cookies.json")


def get_browser_profile(profile_name: str = "default") -> str:
    """获取浏览器 profile 目录"""
    return os.path.expanduser(f"~/.catpaw/xianyu_{profile_name}")


def validate_title(title: str, max_len: int = 50) -> str:
    """验证标题长度"""
    if len(title) > max_len:
        truncated = title[:max_len]
        print(f"[WARN] 标题过长（{len(title)}字），已截断为: {truncated}")
        return truncated
    return title


# ── 元素查找 ─────────────────────────────────────────────────────────────────

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


async def js_click_element(page, script: str) -> dict:
    """执行 JS 点击"""
    try:
        result = await page.evaluate(script)
        return {"success": "clicked" in result or "found" in result, "detail": result}
    except Exception as e:
        return {"success": False, "error": str(e)[:50]}


# ── 核心发布流程 ─────────────────────────────────────────────────────────────

async def fill_title(page, title: str) -> bool:
    """填写标题"""
    print(f"[STEP] 填写标题: {title[:30]}...")
    
    selectors = [
        '[contenteditable="true"]',
        'input[type="text"]',
        'input[placeholder*="标题"]',
        'input[class*="title"]',
    ]
    
    el = await find_element_robust(page, selectors)
    if el:
        await el.fill(title)
        print("[INFO] 标题填写成功")
        return True
    
    # JS 降级
    result = await js_click_element(page, """() => {
        const el = document.querySelector('[contenteditable="true"]') || document.querySelector('input[type="text"]');
        if (el) { el.fill(arguments[0]); return 'js filled'; }
        return 'not found';
    }""")
    print(f"[INFO] JS 填写: {result}")
    return result["success"]


async def fill_price(page, price: str) -> bool:
    """填写价格"""
    print(f"[STEP] 填写价格: ¥{price}")
    
    selectors = [
        'input[placeholder="0.00"]',
        'input[placeholder*="价格"]',
        'input[class*="price"]',
        'input[type="number"]',
    ]
    
    el = await find_element_robust(page, selectors)
    if el:
        await el.fill(str(price))
        print("[INFO] 价格填写成功")
        return True
    
    # JS 降级
    result = await js_click_element(page, """() => {
        const el = document.querySelector('input[placeholder="0.00"]');
        if (el) { el.value = arguments[0]; el.dispatchEvent(new Event('input')); return 'js filled'; }
        return 'not found';
    }""")
    print(f"[INFO] JS 价格: {result}")
    return result["success"]


async def select_new_degree(page, degree: str) -> bool:
    """选择新旧程度"""
    print(f"[STEP] 选择新旧程度: {degree}")
    
    degree_map = {
        "全新": 0, "99新": 1, "95新": 2, "9成新": 3,
        "8成新": 4, "7成新": 5, "6成新及以下": 6
    }
    idx = degree_map.get(degree, 2)
    
    try:
        radios = page.locator('input[type="radio"]')
        if await radios.count() > idx:
            await radios.nth(idx).check()
            print("[INFO] 新旧程度选择成功")
            return True
    except Exception as e:
        print(f"[WARN] 选择失败: {e}")
    
    return False


async def upload_images(page, image_paths: List[str]) -> bool:
    """上传图片"""
    if not image_paths:
        print("[INFO] 未指定图片，跳过")
        return True
    
    valid_paths = [p.strip() for p in image_paths if os.path.exists(p.strip())]
    if not valid_paths:
        print("[WARN] 没有找到有效的图片文件")
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
        
        file_input = page.locator('input[type="file"]').first
        await file_input.set_input_files(valid_paths)
        
        # 等待上传
        await page.wait_for_timeout(3000)
        print("[INFO] 图片上传完成")
        return True
    except Exception as e:
        print(f"[WARN] 图片上传失败: {e}")
        return False


async def click_publish(page) -> bool:
    """点击发布按钮"""
    print("[STEP] 点击发布...")
    
    # 方法1: Playwright locator
    for sel in ['button:has-text("发布")', 'button:has-text("立即发布")']:
        try:
            btn = page.locator(sel).first
            if await btn.count() > 0 and await btn.is_visible(timeout=2000):
                await btn.click()
                print("[INFO] 发布按钮点击成功")
                return True
        except Exception:
            pass
    
    # 方法2: JS 降级
    result = await js_click_element(page, """() => {
        const btns = Array.from(document.querySelectorAll('button'));
        const btn = btns.find(b => ['发布', '立即发布', '提交'].includes(b.textContent.trim()));
        if (btn) { btn.click(); return 'clicked: ' + btn.textContent.trim(); }
        return 'not found';
    }""")
    print(f"[INFO] JS 发布: {result}")
    return result["success"]


# ── 主流程 ────────────────────────────────────────────────────────────────────

async def publish(
    title: str,
    description: str,
    price: str,
    new_degree: str = "95新",
    category: str = "其他闲置",
    image_paths: Optional[List[str]] = None,
    profile_dir: str = None,
    headless: bool = False,
    workspace: str = "/tmp"
):
    """
    闲鱼发布主流程
    """
    # 验证参数
    title = validate_title(title)
    
    # Profile 路径
    if not profile_dir:
        profile_dir = get_browser_profile()
    profile_dir = os.path.expanduser(profile_dir)
    
    # 确保目录存在
    Path(profile_dir).mkdir(parents=True, exist_ok=True)
    clear_profile_locks(profile_dir)
    
    print(f"[INFO] Profile: {profile_dir}")
    
    # Scrapling 预检
    print("[SCRAPLING] 预检闲鱼页面...")
    precheck = try_scrapling_precheck(XIANYU_URL)
    if precheck["accessible"]:
        print(f"[SCRAPLING] ✅ 页面可访问: {precheck.get('title', '')[:50]}")
    else:
        print(f"[SCRAPLING] ⚠️ 预检结果: {precheck.get('error', 'unknown')[:80]}")
    
    # 运行浏览器
    await run_browser(
        title=title,
        description=description,
        price=price,
        new_degree=new_degree,
        category=category,
        image_paths=image_paths,
        profile_dir=profile_dir,
        headless=headless,
        workspace=workspace
    )


async def run_browser(**kwargs):
    """浏览器运行任务"""
    from playwright.async_api import async_playwright
    
    title = kwargs["title"]
    description = kwargs["description"]
    price = kwargs["price"]
    new_degree = kwargs["new_degree"]
    image_paths = kwargs["image_paths"]
    profile_dir = kwargs["profile_dir"]
    headless = kwargs["headless"]
    workspace = kwargs["workspace"]
    
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
        await page.goto(XIANYU_URL, wait_until="domcontentloaded", timeout=DEFAULT_TIMEOUT)
        await page.wait_for_timeout(3000)
        
        print(f"[INFO] 当前 URL: {page.url}")
        
        # 检查登录状态
        if "login" in page.url or "passport" in page.url:
            print("[ERROR] 需要登录！请先对我说 '登录闲鱼'")
            await context.close()
            return False
        
        # 截图初始状态
        await page.screenshot(path=os.path.join(workspace, "xianyu_01_initial.png"))
        
        # 填写标题
        await fill_title(page, title)
        await page.wait_for_timeout(500)
        
        # 填写价格
        await fill_price(page, price)
        await page.wait_for_timeout(500)
        
        # 选择新旧程度
        await select_new_degree(page, new_degree)
        await page.wait_for_timeout(300)
        
        # 上传图片
        if image_paths:
            await upload_images(page, image_paths)
        
        # 截图填写后
        await page.screenshot(path=os.path.join(workspace, "xianyu_02_filled.png"))
        
        # 点击发布
        await click_publish(page)
        await page.wait_for_timeout(5000)
        
        # 截图最终状态
        await page.screenshot(path=os.path.join(workspace, "xianyu_03_final.png"))
        
        print(f"[INFO] 最终 URL: {page.url}")
        print(f"[INFO] 截图已保存到: {workspace}")
        
        # 判断成功
        success = "success" in page.url or "published" in page.url or "manage" in page.url
        if success:
            print("[SUCCESS] 🎉 商品发布成功！")
        else:
            print("[INFO] 请查看截图确认发布状态")
        
        await context.close()
        return success


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args():
    parser = argparse.ArgumentParser(description="闲鱼商品发布 - Scrapling 增强版")
    parser.add_argument("--title", "-t", required=True, help="商品标题")
    parser.add_argument("--description", "-d", required=True, help="商品描述")
    parser.add_argument("--price", "-p", required=True, help="商品价格")
    parser.add_argument("--category", "-c", default="其他闲置", help="商品分类")
    parser.add_argument("--new-degree", default="95新", help="新旧程度")
    parser.add_argument("--image", "-i", help="商品图片路径（多张用逗号分隔）")
    parser.add_argument("--profile", default=None, help="浏览器 profile 目录")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--workspace", default="/tmp", help="截图保存目录")
    return parser.parse_args()


def main():
    args = parse_args()
    
    print("=" * 60)
    print("  闲鱼商品发布 - Scrapling 增强版")
    print(f"  标题: {args.title[:30]}...")
    print(f"  价格: ¥{args.price}")
    print(f"  新旧: {args.new_degree}")
    print("=" * 60)
    
    image_paths = None
    if args.image:
        image_paths = [p.strip() for p in args.image.split(",")]
    
    ok = asyncio.run(publish(
        title=args.title,
        description=args.description,
        price=args.price,
        new_degree=args.new_degree,
        category=args.category,
        image_paths=image_paths,
        profile_dir=args.profile,
        headless=args.headless,
        workspace=args.workspace,
    ))
    
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
