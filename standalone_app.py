import os
import sys
import webbrowser
import threading
import time
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import numpy as np
import tqdm
import subprocess

# 設定日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PrimePhoneApp")

# 設定應用程式標題
APP_TITLE = "我的手機號碼與質數的距離"
APP_VERSION = "1.0.0"

# 獲取應用程式路徑
def get_application_path():
    if getattr(sys, 'frozen', False):
        # 如果是打包後的執行檔
        app_path = os.path.dirname(sys.executable)
        logger.info(f"Running as executable. Path: {app_path}")
        return app_path
    else:
        # 如果是開發環境
        app_path = os.path.dirname(os.path.abspath(__file__))
        logger.info(f"Running in development mode. Path: {app_path}")
        return app_path

# 設定工作目錄
app_path = get_application_path()
os.chdir(app_path)
logger.info(f"Changed working directory to: {app_path}")
logger.info(f"Current directory contents: {os.listdir(app_path)}")

# 創建 Flask 應用程式
api_app = Flask(__name__, static_folder=None)
CORS(api_app)

# 從 embedded_frontend.py 導入嵌入式前端
from embedded_frontend import INDEX_HTML

# 判斷一個數字是否為質數
def is_prime(n):
    """檢查一個數字是否為質數"""
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

# 提供嵌入式前端
@api_app.route('/')
def serve_index():
    return INDEX_HTML

# 尋找最接近的質數
@api_app.route('/api/find_closest_prime', methods=['POST'])
def find_closest_prime():
    try:
        data = request.get_json()
        
        if not data or 'phone_number' not in data:
            return jsonify({"error": "缺少手機號碼"}), 400
        
        phone_number = str(data['phone_number']).strip()
        # 移除所有非數字字符
        phone_number = ''.join(filter(str.isdigit, phone_number))
        
        # 驗證台灣手機號碼格式
        if not phone_number.startswith('09') or len(phone_number) != 10:
            return jsonify({"error": "請輸入有效的台灣手機號碼 (09xxxxxxxx)"}), 400
        
        # 轉換為整數
        number = int(phone_number)
        
        # 檢查輸入的號碼是否為質數
        is_input_prime = is_prime(number)
        
        # 獲取要尋找的質數數量，默認為 5
        count = int(data.get('count', 5))
        if count < 1:
            count = 1
        if count > 100:
            count = 100
            
        # 尋找最接近的質數
        closest_primes = []
        smaller_primes = []
        larger_primes = []
        
        # 向下尋找質數
        current = number - 1
        while len(smaller_primes) < count and current > 1:
            if is_prime(current):
                diff = number - current
                smaller_primes.append({
                    "number": current,
                    "diff": diff,
                    "direction": "smaller"
                })
            current -= 1
            
        # 向上尋找質數
        current = number + 1
        while len(larger_primes) < count:
            if is_prime(current):
                diff = current - number
                larger_primes.append({
                    "number": current,
                    "diff": diff,
                    "direction": "larger"
                })
            current += 1
            
        # 合併並按差值排序
        closest_primes = smaller_primes + larger_primes
        closest_primes.sort(key=lambda x: x["diff"])
        
        # 只返回前 count*2 個結果
        closest_primes = closest_primes[:count*2]
        
        return jsonify({
            "input_number": number,
            "is_prime": is_input_prime,
            "closest_primes": closest_primes
        })
        
    except Exception as e:
        logger.error(f"Error in find_closest_prime: {e}")
        return jsonify({"error": str(e)}), 500

# 尋找指定前綴的質數手機號碼
@api_app.route('/api/find_prime_phones', methods=['POST'])
def find_prime_phones():
    try:
        data = request.get_json()
        
        if not data or 'prefix' not in data:
            return jsonify({"error": "缺少前綴"}), 400
        
        prefix = str(data['prefix']).strip()
        # 移除所有非數字字符
        prefix = ''.join(filter(str.isdigit, prefix))
        
        # 驗證台灣手機號碼前綴格式
        if not prefix.startswith('09') or len(prefix) < 2 or len(prefix) > 6:
            return jsonify({"error": "請輸入有效的台灣手機號碼前綴 (09xx)"}), 400
        
        # 生成所有可能的號碼
        start = int(prefix + '0' * (10 - len(prefix)))
        end = int(prefix + '9' * (10 - len(prefix)))
        
        # 限制範圍，避免處理過多數據
        if end - start > 10000:
            end = start + 10000
            
        prime_phones = []
        for num in range(start, end + 1):
            if is_prime(num):
                prime_phones.append(num)
                # 限制結果數量
                if len(prime_phones) >= 100:
                    break
                    
        return jsonify({
            "prefix": prefix,
            "prime_phones": prime_phones,
            "count": len(prime_phones)
        })
        
    except Exception as e:
        logger.error(f"Error in find_prime_phones: {e}")
        return jsonify({"error": str(e)}), 500

# 列出所有台灣手機號碼前綴
@api_app.route('/api/list_prime_phone_prefixes', methods=['GET'])
def list_prime_phone_prefixes():
    try:
        # 台灣手機號碼前綴列表
        prefixes = [
            # 中華電信
            {"prefix": "0910", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0911", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0912", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0913", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0914", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0915", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0916", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0917", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0918", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0919", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0930", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0931", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0932", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0933", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0934", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0935", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0936", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0937", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0938", "operator": "中華電信", "type": "4G/5G"},
            {"prefix": "0939", "operator": "中華電信", "type": "4G/5G"},
            
            # 台灣大哥大
            {"prefix": "0905", "operator": "台灣大哥大", "type": "4G/5G"},
            {"prefix": "0909", "operator": "台灣大哥大", "type": "4G/5G"},
            {"prefix": "0920", "operator": "台灣大哥大", "type": "4G/5G"},
            {"prefix": "0921", "operator": "台灣大哥大", "type": "4G/5G"},
            {"prefix": "0922", "operator": "台灣大哥大", "type": "4G/5G"},
            {"prefix": "0923", "operator": "台灣大哥大", "type": "4G/5G"},
            {"prefix": "0925", "operator": "台灣大哥大", "type": "4G/5G"},
            {"prefix": "0926", "operator": "台灣大哥大", "type": "4G/5G"},
            {"prefix": "0927", "operator": "台灣大哥大", "type": "4G/5G"},
            {"prefix": "0928", "operator": "台灣大哥大", "type": "4G/5G"},
            {"prefix": "0929", "operator": "台灣大哥大", "type": "4G/5G"},
            
            # 遠傳電信
            {"prefix": "0906", "operator": "遠傳電信", "type": "4G/5G"},
            {"prefix": "0907", "operator": "遠傳電信", "type": "4G/5G"},
            {"prefix": "0908", "operator": "遠傳電信", "type": "4G/5G"},
            {"prefix": "0950", "operator": "遠傳電信", "type": "4G/5G"},
            {"prefix": "0951", "operator": "遠傳電信", "type": "4G/5G"},
            {"prefix": "0952", "operator": "遠傳電信", "type": "4G/5G"},
            {"prefix": "0953", "operator": "遠傳電信", "type": "4G/5G"},
            {"prefix": "0954", "operator": "遠傳電信", "type": "4G/5G"},
            {"prefix": "0955", "operator": "遠傳電信", "type": "4G/5G"},
            {"prefix": "0956", "operator": "遠傳電信", "type": "4G/5G"},
            {"prefix": "0957", "operator": "遠傳電信", "type": "4G/5G"},
            {"prefix": "0958", "operator": "遠傳電信", "type": "4G/5G"},
            {"prefix": "0959", "operator": "遠傳電信", "type": "4G/5G"},
            
            # 台灣之星
            {"prefix": "0901", "operator": "台灣之星", "type": "4G/5G"},
            {"prefix": "0902", "operator": "台灣之星", "type": "4G/5G"},
            {"prefix": "0903", "operator": "台灣之星", "type": "4G/5G"},
            {"prefix": "0904", "operator": "台灣之星", "type": "4G/5G"},
            {"prefix": "0960", "operator": "台灣之星", "type": "4G/5G"},
            {"prefix": "0961", "operator": "台灣之星", "type": "4G/5G"},
            {"prefix": "0962", "operator": "台灣之星", "type": "4G/5G"},
            {"prefix": "0963", "operator": "台灣之星", "type": "4G/5G"},
            {"prefix": "0964", "operator": "台灣之星", "type": "4G/5G"},
            {"prefix": "0965", "operator": "台灣之星", "type": "4G/5G"},
            {"prefix": "0966", "operator": "台灣之星", "type": "4G/5G"},
            {"prefix": "0967", "operator": "台灣之星", "type": "4G/5G"},
            {"prefix": "0968", "operator": "台灣之星", "type": "4G/5G"},
            {"prefix": "0969", "operator": "台灣之星", "type": "4G/5G"},
            
            # 亞太電信
            {"prefix": "0970", "operator": "亞太電信", "type": "4G/5G"},
            {"prefix": "0971", "operator": "亞太電信", "type": "4G/5G"},
            {"prefix": "0972", "operator": "亞太電信", "type": "4G/5G"},
            {"prefix": "0973", "operator": "亞太電信", "type": "4G/5G"},
            {"prefix": "0974", "operator": "亞太電信", "type": "4G/5G"},
            {"prefix": "0975", "operator": "亞太電信", "type": "4G/5G"},
            {"prefix": "0976", "operator": "亞太電信", "type": "4G/5G"},
            {"prefix": "0977", "operator": "亞太電信", "type": "4G/5G"},
            {"prefix": "0978", "operator": "亞太電信", "type": "4G/5G"},
            {"prefix": "0979", "operator": "亞太電信", "type": "4G/5G"},
            
            # 其他
            {"prefix": "0980", "operator": "其他電信業者", "type": "4G/5G"},
            {"prefix": "0981", "operator": "其他電信業者", "type": "4G/5G"},
            {"prefix": "0982", "operator": "其他電信業者", "type": "4G/5G"},
            {"prefix": "0983", "operator": "其他電信業者", "type": "4G/5G"},
            {"prefix": "0984", "operator": "其他電信業者", "type": "4G/5G"},
            {"prefix": "0985", "operator": "其他電信業者", "type": "4G/5G"},
            {"prefix": "0986", "operator": "其他電信業者", "type": "4G/5G"},
            {"prefix": "0987", "operator": "其他電信業者", "type": "4G/5G"},
            {"prefix": "0988", "operator": "其他電信業者", "type": "4G/5G"},
            {"prefix": "0989", "operator": "其他電信業者", "type": "4G/5G"},
        ]
        
        return jsonify(prefixes)
        
    except Exception as e:
        logger.error(f"Error in list_prime_phone_prefixes: {e}")
        return jsonify({"error": str(e)}), 500

# 主函數
def main():
    try:
        logger.info(f"Starting {APP_TITLE} v{APP_VERSION}")
        
        # 啟動 Flask 服務器
        port = 8000
        logger.info(f"Starting Flask server on http://127.0.0.1:{port}")
        
        # 打開瀏覽器
        threading.Timer(1.5, lambda: webbrowser.open(f'http://127.0.0.1:{port}')).start()
        logger.info(f"Opening browser at http://127.0.0.1:{port}")
        
        print(f"=== {APP_TITLE} v{APP_VERSION} ===")
        print("應用程式已啟動，請勿關閉此視窗")
        print(f"如果瀏覽器沒有自動打開，請手動訪問：http://127.0.0.1:{port}")
        print("日誌文件保存在：app_log.txt")
        
        # 啟動 Flask 服務器（這會阻塞主線程）
        api_app.run(host='127.0.0.1', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        print(f"應用程式發生錯誤: {e}")
        print("詳細信息請查看日誌文件：app_log.txt")
        sys.exit(1)

if __name__ == "__main__":
    main()
