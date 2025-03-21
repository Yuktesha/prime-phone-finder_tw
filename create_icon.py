from PIL import Image, ImageDraw, ImageFont
import os

# 創建一個 256x256 的圖像，帶透明背景
img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# 繪製圓形背景
draw.ellipse((20, 20, 236, 236), fill=(66, 133, 244, 255))

# 繪製數字 "09" 作為手機號碼前綴
try:
    # 嘗試加載字體
    font = ImageFont.truetype("arial.ttf", 100)
except:
    # 如果無法加載字體，使用默認字體
    font = ImageFont.load_default()

# 繪製文字
draw.text((65, 75), "09", fill=(255, 255, 255, 255), font=font)

# 繪製質數符號 (使用希臘字母 π 的近似)
draw.text((100, 120), "π", fill=(255, 255, 255, 255), font=font)

# 保存為 PNG
img.save('app_icon.png')

# 保存為 ICO (多種尺寸)
sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
img.save('app_icon.ico', sizes=sizes)

print("圖標文件已創建: app_icon.ico 和 app_icon.png")
