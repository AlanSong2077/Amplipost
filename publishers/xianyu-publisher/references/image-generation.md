# 商品图片生成指南

## Python PIL 生成支持中文的图片

```python
from PIL import Image, ImageDraw, ImageFont
import os

def generate_product_image(product_name, price, output_path="/tmp/product.jpg"):
    """生成商品图片（支持中文）"""
    
    # 查找支持中文的字体
    font_paths = [
        "/System/Library/Fonts/STHeiti Light.ttc",  # macOS 黑体
        "/System/Library/Fonts/PingFang.ttc",       # macOS 苹方
        "/System/Library/Fonts/Hiragino Sans GB.ttc", # macOS 冬青黑体
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    
    font = None
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                font = ImageFont.truetype(fp, 40)
                print(f"使用字体: {fp}")
                break
            except:
                continue
    
    if not font:
        font = ImageFont.load_default()
        print("警告: 使用默认字体，中文可能显示不正确")
    
    # 创建图片
    img = Image.new('RGB', (800, 600), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    # 标题框
    draw.rectangle([30, 30, 770, 130], fill='#4a90d9')
    draw.text((400, 80), str(product_name), fill='white', anchor='mm', align='center', font=font)
    
    # 价格标签
    draw.rectangle([300, 250, 500, 350], fill='#e74c3c')
    draw.text((400, 300), f"¥{price}", fill='white', anchor='mm', align='center', font=font)
    
    # 保存
    img.save(output_path, 'JPEG', quality=90)
    return output_path

# 使用示例
generate_product_image("中美港股上市财报数据", "2", "/tmp/product.jpg")
```

## 常见问题

### 中文显示为方块
**原因**: 默认字体不支持中文

**解决方案**: 使用上面代码中的字体路径列表，优先选择 `STHeiti Light.ttc`（macOS 黑体）

### 字体太大或太小
**解决方案**: 调整 `ImageFont.truetype(fp, size)` 中的 size 参数
- 标题: 36-48
- 正文: 24-32
- 价格: 48-64

### 图片背景色
推荐使用深色背景 (#1a1a2e) 配白色文字，对比度更好
