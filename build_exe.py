import os
import sys
import subprocess
from PIL import Image, ImageDraw

def create_icon():
    """創建應用程式圖標"""
    print("正在創建應用程式圖標...")
    
    # 創建一個 256x256 的圖像
    img = Image.new('RGBA', (256, 256), color=(255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    
    # 繪製圓形背景
    draw.ellipse((20, 20, 236, 236), fill=(66, 133, 244, 255))
    
    # 繪製數字 "09" 表示手機號碼
    draw.rectangle((78, 78, 178, 178), fill=(255, 255, 255, 255))
    
    # 保存為 ICO 文件
    img.save('app_icon.ico', format='ICO', sizes=[(256, 256)])
    print("圖標已創建: app_icon.ico")

def build_executable():
    """構建可執行文件"""
    print("正在構建可執行文件...")
    
    # 確保圖標存在
    if not os.path.exists('app_icon.ico'):
        create_icon()
    
    # 構建命令
    cmd = [
        'pyinstaller',
        '--onefile',                          # 創建單一執行檔
        '--noconsole',                        # 不顯示控制台窗口
        '--name', '我的手機號碼與質數的距離',   # 應用程式名稱
        '--icon=app_icon.ico',                # 應用程式圖標
        '--version-file=version_info_tk.txt', # 版本信息
        'prime_phone_app.py'                  # 主程式文件
    ]
    
    # 執行命令
    subprocess.run(cmd)
    print("構建完成！")

if __name__ == "__main__":
    build_executable()
