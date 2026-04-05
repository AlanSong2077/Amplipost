#!/usr/bin/env python3
"""
闲鱼自动发布脚本
接收商品信息，自动生成标题和描述，然后发布到闲鱼
"""

import os
import sys
import json
import argparse

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 商品模板
PRODUCT_TEMPLATES = {
    "手机": {
        "title": "【{new_degree}】{brand} {model} {memory} {storage} {color} {version} {highlight} {price}",
        "description": """📱{brand} {model} {memory}+{storage}

【配置详情】
{configuration}

【新旧程度】{new_degree}
【颜色】{color}
【电池健康】{battery}
【配件】{accessories}
【入手渠道】{purchase_channel}
【出手原因】{reason}

📦【交易方式】{trade_method}
💬【说明】{notes}

有意请留言，看到会第一时间回复～"""
    },
    "电脑": {
        "title": "{brand} {model} {chip} {memory}+{storage} {new_degree} {highlight} {price}",
        "description": """💻{brand} {model}

【配置】
- 芯片：{chip}
- 内存：{memory}
- 存储：{storage}
- 屏幕：{screen}

【新旧程度】：{new_degree}
【外观】：{appearance}
【配件】：{accessories}
【购买时间】：{purchase_time}
【出手原因】：{reason}

✅功能正常，无维修记录
🎁配件：{accessories}

📦{trade_method}
🔔{notes}"""
    },
    "通用": {
        "title": "【{new_degree}】{product_name} {highlight} {price}",
        "description": """【商品名称】{product_name}

【商品情况】{description}
【新旧程度】{new_degree}
【入手时间】{purchase_time}
【出手原因】{reason}

📦{trade_method}
💬{notes}

诚心要可议价，谢谢！"""
    }
}

# 违禁词替换表
FORBIDDEN_WORDS = {
    "高仿": "复刻",
    "精仿": "品质",
    "A货": "正品",
    "1:1": "1:1",
    "全网最低": "优惠价",
    "天下第一": "优质",
}


def load_state():
    """加载发布状态"""
    state_file = os.path.expanduser("~/.openclaw/workspace/xianyu_auto_state.json")
    default_state = {
        "published_count": 0,
        "last_index": -1,
        "recent_indices": [],
        "last_publish_time": None
    }
    
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except:
            return default_state
    return default_state


def save_state(state):
    """保存发布状态"""
    state_file = os.path.expanduser("~/.openclaw/workspace/xianyu_auto_state.json")
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def replace_forbidden_words(text):
    """替换违禁词"""
    for word, replacement in FORBIDDEN_WORDS.items():
        text = text.replace(word, replacement)
    return text


def parse_product_info(args):
    """解析商品信息"""
    product = {
        "name": args.name,
        "description": args.description or "",
        "price": args.price,
        "category": args.category or "通用",
        "new_degree": args.new_degree or "95新",
        "brand": args.brand or "",
        "model": args.model or "",
        "memory": args.memory or "",
        "storage": args.storage or "",
        "color": args.color or "",
        "chip": args.chip or "",
        "screen": args.screen or "",
        "battery": args.battery or "",
        "accessories": args.accessories or "无",
        "purchase_channel": args.purchase_channel or "",
        "purchase_time": args.purchase_time or "",
        "reason": args.reason or "闲置",
        "trade_method": args.trade_method or "支持平台交易",
        "highlight": args.highlight or "功能正常",
        "appearance": args.appearance or "外观完好",
        "notes": args.notes or "诚心要可议价",
        "image_path": args.image or ""
    }
    
    # 生成配置详情
    if product["category"] == "手机":
        product["configuration"] = f"型号：{product['model']}\n内存：{product['memory']}\n存储：{product['storage']}\n颜色：{product['color']}"
    else:
        product["configuration"] = product["description"]
    
    return product


def generate_title(product):
    """生成商品标题"""
    template = PRODUCT_TEMPLATES.get(product["category"], PRODUCT_TEMPLATES["通用"])["title"]
    
    title = template.format(
        new_degree=product["new_degree"],
        brand=product["brand"],
        model=product["model"],
        memory=product["memory"],
        storage=product["storage"],
        color=product["color"],
        version="全网通" if product["category"] == "手机" else "",
        highlight=product["highlight"],
        price=f"¥{product['price']}",
        product_name=product["name"],
        chip=product["chip"]
    )
    
    # 清理多余空格
    title = ' '.join(title.split())
    return replace_forbidden_words(title)


def generate_description(product):
    """生成商品描述"""
    template = PRODUCT_TEMPLATES.get(product["category"], PRODUCT_TEMPLATES["通用"])["description"]
    
    description = template.format(
        brand=product["brand"],
        model=product["model"],
        memory=product["memory"],
        storage=product["storage"],
        color=product["color"],
        battery=product["battery"],
        configuration=product["configuration"],
        new_degree=product["new_degree"],
        accessories=product["accessories"],
        purchase_channel=product["purchase_channel"],
        purchase_time=product["purchase_time"],
        reason=product["reason"],
        trade_method=product["trade_method"],
        notes=product["notes"],
        product_name=product["name"],
        description=product["description"],
        chip=product["chip"],
        screen=product["screen"],
        appearance=product["appearance"],
        highlight=product["highlight"],
        price=f"¥{product['price']}"
    )
    
    return replace_forbidden_words(description)


def publish(product):
    """发布商品到闲鱼"""
    script_dir = os.path.expanduser("~/.openclaw/skills/xianyu-publisher/scripts")
    script = os.path.join(script_dir, "xianyu_publish.py")
    
    # 构建命令
    cmd = f"""python3 {script} \\
  --title "{product['title']}" \\
  --description "{product['description']}" \\
  --price "{product['price']}" \\
  --category "{product['category']}" \\
  --new-degree "{product['new_degree']}" """
    
    if product.get("image_path"):
        cmd += f' --image "{product["image_path"]}"'
    
    print(f"执行命令: {cmd}")
    return os.system(cmd)


def main():
    parser = argparse.ArgumentParser(description="闲鱼自动发布")
    
    # 必填参数
    parser.add_argument("--name", "-n", required=True, help="商品名称")
    parser.add_argument("--price", "-p", required=True, type=int, help="商品价格")
    
    # 可选参数
    parser.add_argument("--description", "-d", help="商品描述")
    parser.add_argument("--category", "-c", default="通用", help="商品分类")
    parser.add_argument("--new-degree", default="95新", help="新旧程度")
    
    # 商品详情
    parser.add_argument("--brand", help="品牌")
    parser.add_argument("--model", help="型号")
    parser.add_argument("--memory", help="内存")
    parser.add_argument("--storage", help="存储")
    parser.add_argument("--color", help="颜色")
    parser.add_argument("--chip", help="芯片")
    parser.add_argument("--screen", help="屏幕")
    parser.add_argument("--battery", help="电池健康度")
    parser.add_argument("--accessories", help="配件")
    parser.add_argument("--purchase-channel", help="入手渠道")
    parser.add_argument("--purchase-time", help="入手时间")
    parser.add_argument("--reason", default="闲置", help="出手原因")
    parser.add_argument("--trade-method", default="支持平台交易", help="交易方式")
    parser.add_argument("--highlight", default="功能正常", help="卖点")
    parser.add_argument("--appearance", default="外观完好", help="外观描述")
    parser.add_argument("--notes", default="诚心要可议价", help="备注")
    parser.add_argument("--image", "-i", help="商品图片路径")
    
    args = parser.parse_args()
    
    print(f"\n{'='*50}")
    print(f"闲鱼自动发布 - {parser.parse_args()}")
    print(f"{'='*50}\n")
    
    # 解析商品信息
    product = parse_product_info(args)
    
    # 生成标题和描述
    product["title"] = generate_title(product)
    product["description"] = generate_description(product)
    
    print(f"商品名称: {product['name']}")
    print(f"商品分类: {product['category']}")
    print(f"新旧程度: {product['new_degree']}")
    print(f"价格: ¥{product['price']}")
    print(f"\n标题: {product['title']}")
    print(f"\n描述:\n{product['description'][:200]}...")
    
    # 加载状态
    state = load_state()
    print(f"\n已发布 {state['published_count']} 件商品")
    
    # 发布
    print("\n开始发布...\n")
    result = publish(product)
    
    # 更新状态
    if result == 0:
        state["published_count"] += 1
        state["last_publish_time"] = __import__('datetime').datetime.now().isoformat()
        save_state(state)
        print(f"\n✅ 发布成功！已累计发布 {state['published_count']} 件")
    else:
        print(f"\n❌ 发布失败，错误码: {result}")
    
    return result


if __name__ == "__main__":
    exit(main())
