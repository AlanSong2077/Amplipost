#!/usr/bin/env python3
"""
闲鱼商品发布核心脚本 v3
适配新版闲鱼 (goofish.com)
"""

import os
import sys
import json
import argparse
import time
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("错误：需要安装 Playwright")
    print("请运行：pip install playwright && playwright install chromium")
    sys.exit(1)


# 新版闲鱼 URL
XIANYU_URL = "https://www.goofish.com/publish"
DEFAULT_TIMEOUT = 60000


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="闲鱼商品发布 v3")
    
    parser.add_argument("--title", "-t", required=True, help="商品标题")
    parser.add_argument("--description", "-d", required=True, help="商品描述")
    parser.add_argument("--price", "-p", required=True, help="商品价格")
    parser.add_argument("--category", "-c", default="其他闲置", help="商品分类")
    parser.add_argument("--new-degree", default="95新", help="新旧程度")
    parser.add_argument("--image", "-i", help="商品图片路径（支持多张，用逗号分隔）")
    parser.add_argument("--profile", default="default", help="浏览器配置目录")
    parser.add_argument("--headless", action="store_true", help="无头模式运行")
    
    return parser.parse_args()


def get_cookies_file(profile_name):
    """获取 cookies 文件路径"""
    cookie_dir = os.path.expanduser(f"~/.openclaw/browser_profiles/xianyu_{profile_name}")
    return os.path.join(cookie_dir, "cookies.json")


def publish_to_xianyu(args):
    """发布商品到闲鱼"""
    print(f"\n{'='*50}")
    print(f"闲鱼商品发布 v3 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*50}")
    print(f"标题: {args.title[:30]}...")
    print(f"价格: ¥{args.price}")
    print(f"新旧: {args.new_degree}")
    print(f"{'='*50}\n")
    
    cookies_file = get_cookies_file(args.profile)
    
    if not os.path.exists(cookies_file):
        print("❌ 未找到登录态！请先对我说 '登录闲鱼'")
        return 1
    
    with sync_playwright() as p:
        print("启动浏览器...")
        browser = p.chromium.launch(
            headless=args.headless,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            viewport={'width': 1440, 'height': 900},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # 加载 cookies
        print("加载登录态...")
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
            context.add_cookies(cookies)
        print(f"✅ 已加载 {len(cookies)} 个 cookies")
        
        page = context.new_page()
        
        try:
            print("打开闲鱼发布页面...")
            page.goto(XIANYU_URL, timeout=DEFAULT_TIMEOUT, wait_until="networkidle")
            page.wait_for_timeout(2000)
            
            print(f"URL: {page.url}")
            print(f"标题: {page.title()}")
            
            # 检查是否需要登录
            if "login" in page.url or "passport" in page.url:
                print("❌ 需要登录！请对我说 '登录闲鱼'")
                return 1
            
            # 截图初始状态
            page.screenshot(path="/tmp/xianyu_01_initial.png")
            
            # ========== 填写表单 ==========
            
            # 1. 填写标题 - contenteditable div
            print("\n[1/6] 填写标题...")
            title_input = page.locator('[contenteditable="true"]').first
            if title_input.count() > 0:
                title_input.fill(args.title)
                page.wait_for_timeout(500)
                print("✅ 标题已填写 (contenteditable)")
            else:
                # 备用：找 input[type="text"]
                text_inputs = page.locator('input[type="text"]')
                if text_inputs.count() > 0:
                    text_inputs.nth(0).fill(args.title)
                    page.wait_for_timeout(500)
                    print("✅ 标题已填写 (input)")
                else:
                    print("⚠️ 未找到标题输入框")
            
            # 2. 填写价格 - placeholder=0.00
            print("[2/6] 填写价格...")
            price_inputs = page.locator('input[placeholder="0.00"]')
            if price_inputs.count() > 0:
                price_inputs.nth(0).fill(str(args.price))
                page.wait_for_timeout(500)
                print(f"✅ 价格 ¥{args.price} 已填写")
            else:
                print("⚠️ 未找到价格输入框")
            
            # 3. 选择新旧程度 - radio buttons
            print("[3/6] 选择新旧程度...")
            new_degree_map = {
                "全新": 0,
                "99新": 1,
                "95新": 2,
                "9成新": 3,
                "8成新": 4,
                "7成新": 5,
                "6成新及以下": 6
            }
            
            radio_buttons = page.locator('input[type="radio"]')
            degree_idx = new_degree_map.get(args.new_degree, 2)  # 默认95新
            if radio_buttons.count() > degree_idx:
                radio_buttons.nth(degree_idx).check()
                page.wait_for_timeout(300)
                print(f"✅ 已选择 {args.new_degree}")
            else:
                print(f"⚠️ 未找到新旧程度选项 (索引 {degree_idx})")
            
            # 4. 上传图片
            print("[4/6] 上传图片...")
            if args.image:
                image_paths = [p.strip() for p in args.image.split(",")]
                existing_images = [p for p in image_paths if os.path.exists(p)]
                
                if existing_images:
                    file_input = page.locator('input[type="file"]').first
                    file_input.set_input_files(existing_images)
                    page.wait_for_timeout(3000)
                    print(f"✅ 已上传 {len(existing_images)} 张图片")
                else:
                    print("⚠️ 没有找到有效的图片文件，跳过")
            else:
                print("ℹ️ 未指定图片，跳过")
            
            # 截图填写后状态
            page.screenshot(path="/tmp/xianyu_02_after_fill.png")
            
            # 5. 点击发布按钮
            print("[5/6] 提交发布...")
            publish_buttons = page.locator('button:has-text("发布")')
            if publish_buttons.count() > 0:
                # 确保按钮可见
                btn = publish_buttons.first
                if btn.is_visible():
                    btn.click()
                    print("✅ 已点击发布按钮")
                else:
                    print("⚠️ 发布按钮不可见，尝试 JS 点击")
                    page.evaluate("document.querySelector('button:has-text(\"发布\")').click()")
            else:
                print("⚠️ 未找到发布按钮")
            
            # 等待发布结果
            page.wait_for_timeout(5000)
            
            # 截图最终状态
            page.screenshot(path="/tmp/xianyu_03_final.png")
            
            print("\n" + "="*50)
            print("✅ 发布流程已完成！")
            print("="*50)
            print(f"截图保存：")
            print(f"  - /tmp/xianyu_01_initial.png (初始)")
            print(f"  - /tmp/xianyu_02_after_fill.png (填写后)")
            print(f"  - /tmp/xianyu_03_final.png (最终)")
            print("\n请手动确认发布结果！")
            
            return 0
            
        except Exception as e:
            print(f"\n❌ 发布出错: {e}")
            import traceback
            traceback.print_exc()
            
            page.screenshot(path="/tmp/xianyu_error.png")
            print("错误截图: /tmp/xianyu_error.png")
            
            return 1
            
        finally:
            browser.close()


def main():
    args = parse_arguments()
    return publish_to_xianyu(args)


if __name__ == "__main__":
    exit(main())
