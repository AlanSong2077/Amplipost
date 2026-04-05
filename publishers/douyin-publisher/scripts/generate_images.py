#!/usr/bin/env python3
"""
抖音图文配图生成脚本（通用版）
使用系统自带中文字体，生成 1080x1080 信息图
支持自定义主题和数据，替代硬编码的行业模板
"""

import os
import sys
import json
import argparse
from PIL import Image, ImageDraw, ImageFont


# ── 字体查找 ──────────────────────────────────────────────────────────────────

FONT_CANDIDATES = [
    # macOS 系统字体
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    # Linux
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    # Windows
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
]


def get_chinese_font(size: int) -> ImageFont.FreeTypeFont:
    """获取支持中文的字体，自动查找系统字体"""
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                font = ImageFont.truetype(path, size, index=0)
                return font
            except Exception:
                continue
    print("[WARN] 未找到中文字体，使用默认字体（中文可能显示为方块）")
    return ImageFont.load_default()


def draw_text_centered(draw, text, y, font, color, img_width=1080):
    """居中绘制文字"""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (img_width - text_width) // 2
    draw.text((x, y), text, font=font, fill=color)


def draw_text_wrapped(draw, text, y, font, color, img_width=1080, max_width=900):
    """自动换行绘制文字，返回最终 y 坐标"""
    words = list(text)
    lines = []
    current_line = ""

    for char in words:
        test_line = current_line + char
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] - bbox[0] > max_width and current_line:
            lines.append(current_line)
            current_line = char
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)

    line_height = font.size + 12
    for line in lines:
        draw_text_centered(draw, line, y, font, color, img_width)
        y += line_height
    return y


def generate_card(
    output_path: str,
    title: str,
    subtitle: str = "",
    body_lines: list = None,
    bg_color: tuple = (20, 30, 60),
    accent_color: tuple = (100, 160, 255),
    brand_text: str = "",
) -> str:
    """
    生成单张信息图
    返回保存路径
    """
    W, H = 1080, 1080
    img = Image.new("RGB", (W, H), color=bg_color)
    draw = ImageDraw.Draw(img)

    # 字体
    font_title    = get_chinese_font(72)
    font_subtitle = get_chinese_font(42)
    font_body     = get_chinese_font(48)
    font_small    = get_chinese_font(34)

    # 背景装饰：顶部色块
    header_h = 220
    draw.rectangle([0, 0, W, header_h], fill=tuple(min(c + 25, 255) for c in bg_color))

    # 边框
    draw.rectangle([20, 20, W - 20, H - 20], outline=accent_color, width=4)

    # 顶部标题
    draw_text_centered(draw, title, 70, font_title, "white", W)

    # 副标题
    if subtitle:
        draw_text_centered(draw, subtitle, 165, font_subtitle, tuple(min(c + 80, 255) for c in accent_color), W)

    # 分隔线
    draw.line([(80, header_h + 20), (W - 80, header_h + 20)], fill=accent_color, width=2)

    # 正文内容
    if body_lines:
        y = header_h + 80
        for i, line in enumerate(body_lines):
            if line.startswith("##"):
                text = line.replace("##", "").strip()
                draw_text_centered(draw, text, y, font_subtitle, accent_color, W)
                y += font_subtitle.size + 20
            elif line == "---":
                draw.line([(120, y + 10), (W - 120, y + 10)], fill=(*accent_color[:3], 128), width=1)
                y += 30
            else:
                display = f"• {line}" if not line.startswith("•") else line
                y = draw_text_wrapped(draw, display, y, font_body, "white", W, max_width=880)
                y += 20

    # 底部品牌标识
    if brand_text:
        draw.rectangle([0, H - 80, W, H], fill=tuple(max(c - 15, 0) for c in bg_color))
        draw_text_centered(draw, brand_text, H - 58, font_small, tuple(min(c + 60, 255) for c in accent_color), W)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path, quality=95)
    print(f"[INFO] 生成配图: {output_path}")
    return output_path


def generate_cards(
    output_dir: str,
    title: str = "通用标题",
    subtitle: str = "",
    points: list = None,
    bg_color: tuple = (20, 30, 60),
    accent_color: tuple = (100, 160, 255),
    brand_text: str = "",
    count: int = 3,
) -> list:
    """
    根据传入的自定义数据生成 N 张信息图
    返回图片路径列表

    Args:
        output_dir: 输出目录
        title: 主标题（每张卡片相同）
        subtitle: 副标题
        points: 要点列表，每张卡片一个要点
        bg_color: 背景色 RGB 元组
        accent_color: 强调色 RGB 元组
        brand_text: 底部品牌文字（可为空）
        count: 生成卡片数量（默认3张）
    """
    os.makedirs(output_dir, exist_ok=True)
    paths = []

    if not points:
        points = ["要点一", "要点二", "要点三"]

    for i in range(count):
        point_text = points[i] if i < len(points) else points[-1]
        path = os.path.join(output_dir, f"card_{i+1}.jpg")
        generate_card(
            output_path=path,
            title=title,
            subtitle=subtitle if subtitle else f"第{i+1}点",
            body_lines=[point_text],
            bg_color=bg_color,
            accent_color=accent_color,
            brand_text=brand_text,
        )
        paths.append(path)

    return paths


# ── CLI 入口 ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="抖音图文配图生成器（通用版）")
    parser.add_argument("--topic",      default="通用话题", help="话题名称（用于生成描述性标题）")
    parser.add_argument("--title",     default="深度解析", help="卡片主标题")
    parser.add_argument("--subtitle",   default="", help="副标题")
    parser.add_argument("--point1",    default="核心要点一", help="第1张卡片要点")
    parser.add_argument("--point2",    default="核心要点二", help="第2张卡片要点")
    parser.add_argument("--point3",    default="核心要点三", help="第3张卡片要点")
    parser.add_argument("--brand",      default="", help="底部品牌文字")
    parser.add_argument("--output-dir", default=os.path.expanduser("~/.catpaw/douyin_images"), help="输出目录")
    parser.add_argument("--bg-r",       type=int, default=20, help="背景色 R (0-255)")
    parser.add_argument("--bg-g",       type=int, default=30, help="背景色 G (0-255)")
    parser.add_argument("--bg-b",      type=int, default=60, help="背景色 B (0-255)")
    parser.add_argument("--accent-r",  type=int, default=100, help="强调色 R (0-255)")
    parser.add_argument("--accent-g",  type=int, default=160, help="强调色 G (0-255)")
    parser.add_argument("--accent-b",  type=int, default=255, help="强调色 B (0-255)")
    parser.add_argument("--test",       action="store_true", help="生成测试图片验证中文显示")
    parser.add_argument("--count",      type=int, default=3, help="生成卡片数量")
    args = parser.parse_args()

    if args.test:
        path = os.path.join(args.output_dir, "test_chinese.jpg")
        generate_card(
            output_path=path,
            title="中文测试",
            subtitle="通用配图生成器",
            body_lines=["第一行测试文字", "第二行测试内容", "第三行验证信息"],
            bg_color=(20, 30, 60),
            accent_color=(100, 160, 255),
            brand_text="品牌标识",
        )
        print(f"测试图片已生成: {path}")
        sys.exit(0)

    bg_color = (args.bg_r, args.bg_g, args.bg_b)
    accent_color = (args.accent_r, args.accent_g, args.accent_b)

    paths = generate_cards(
        output_dir=args.output_dir,
        title=args.title,
        subtitle=args.subtitle or args.topic,
        points=[args.point1, args.point2, args.point3],
        bg_color=bg_color,
        accent_color=accent_color,
        brand_text=args.brand,
        count=args.count,
    )

    print(f"\n生成完成，共 {len(paths)} 张图片：")
    for p in paths:
        print(f"  {p}")
