import os
import sys
import webbrowser
import threading
import time
import logging
import sqlite3
from flask import Flask, jsonify, request, render_template_string, send_from_directory
from flask_cors import CORS

# 設定日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("license_plate_app_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LicensePlatePrimeApp")

# 設定應用程式標題
APP_TITLE = "我的車牌號碼與質數的距離"
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

# 創建 Flask 應用程式
app = Flask(__name__, static_folder=None)
CORS(app)

# 數據庫路徑
DB_PATH = os.path.join(app_path, 'backend', 'primes.db')

# 英文字母轉換為數字
def letter_to_number(letter):
    """將英文字母轉換為數字: A=10, B=11, ..., Z=35"""
    if 'A' <= letter <= 'Z':
        return ord(letter) - ord('A') + 10
    elif 'a' <= letter <= 'z':
        return ord(letter) - ord('a') + 10
    return None

# 數字轉換回英文字母
def number_to_letter(number):
    """將數字轉換回英文字母: 10=A, 11=B, ..., 35=Z"""
    if 10 <= number <= 35:
        return chr(number - 10 + ord('A'))
    return str(number)

# 計算兩個數字之間的距離
def calculate_distance(num1, num2):
    """計算兩個數字之間的距離"""
    return abs(num1 - num2)

# 將車牌轉換為數字
def plate_to_number(plate):
    """將車牌轉換為數字，英文字母按照 A=10, B=11, ... 轉換"""
    result = ""
    for char in plate:
        if char.isdigit():
            result += char
        elif char.isalpha():
            result += str(letter_to_number(char))
    return int(result) if result else 0

# 將數字轉換回類似車牌的格式
def number_to_plate_format(number, original_plate):
    """將數字轉換回類似車牌的格式，保留原始車牌的字母/數字結構"""
    # 確保輸入是字符串
    number_str = str(number)
    original_plate = str(original_plate)
    
    # 創建字母位置映射
    letter_positions = []
    digit_positions = []
    
    # 記錄原始車牌中字母和數字的位置
    for i, char in enumerate(original_plate):
        if char.isalpha():
            letter_positions.append(i)
        elif char.isdigit():
            digit_positions.append(i)
    
    # 如果原始車牌中沒有字母或數字，直接返回數字
    if not letter_positions and not digit_positions:
        return str(number)
    
    # 確保數字字符串足夠長
    total_chars = len(letter_positions) + len(digit_positions)
    if len(number_str) < total_chars:
        number_str = number_str.zfill(total_chars)
    
    # 構建結果字符串
    result_chars = list(original_plate)  # 保留原始格式，包括特殊字符
    
    # 填充數字部分
    num_index = 0
    
    # 先處理字母位置
    for pos in letter_positions:
        if num_index < len(number_str):
            digit = int(number_str[num_index])
            # 將數字轉換為字母 (0->A, 1->B, ...)
            if 0 <= digit <= 9:
                # 對於 0-9，轉換為 A-J
                letter = chr(ord('A') + digit)
            else:
                # 對於 >= 10 的數字，保持為數字
                letter = str(digit)
            result_chars[pos] = letter
            num_index += 1
    
    # 再處理數字位置
    for pos in digit_positions:
        if num_index < len(number_str):
            result_chars[pos] = number_str[num_index]
            num_index += 1
    
    # 組合最終結果
    result = ''.join(result_chars)
    logger.debug(f"Converted {number} to format {original_plate} -> {result}")
    
    return result

# 從數據庫獲取3位數和4位數的質數
def get_primes_from_db():
    """從數據庫獲取3位數和4位數的質數"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 獲取3位數質數
        cursor.execute("SELECT value FROM primes WHERE value >= 100 AND value <= 999")
        three_digit_primes = [row[0] for row in cursor.fetchall()]
        
        # 獲取4位數質數
        cursor.execute("SELECT value FROM primes WHERE value >= 1000 AND value <= 9999")
        four_digit_primes = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return three_digit_primes, four_digit_primes
    except Exception as e:
        logger.error(f"Error getting primes from database: {e}")
        return [], []

# 查找最接近的質數
def find_closest_primes(number, primes, count=5):
    """查找最接近指定數字的質數"""
    distances = [(prime, calculate_distance(number, prime)) for prime in primes]
    distances.sort(key=lambda x: x[1])  # 按距離排序
    return distances[:count]

# API 路由：分析車牌號碼
@app.route('/api/analyze_plate', methods=['POST'])
def analyze_plate():
    try:
        data = request.get_json()
        
        if not data or 'plate' not in data:
            return jsonify({"error": "缺少車牌號碼"}), 400
        
        plate = data['plate'].strip()
        count = int(data.get('count', 5))  # 預設顯示5個最接近的質數
        
        logger.debug(f"Analyzing plate: {plate}")
        
        # 獲取3位數和4位數質數
        three_digit_primes, four_digit_primes = get_primes_from_db()
        all_primes = three_digit_primes + four_digit_primes
        
        results = {}
        
        # 如果車牌包含連字符，分別分析前後部分
        if '-' in plate:
            front_part, back_part = plate.split('-', 1)
            logger.debug(f"Split plate into front: {front_part}, back: {back_part}")
            
            # 分析前半部分
            front_number = plate_to_number(front_part)
            logger.debug(f"Front part {front_part} converted to number: {front_number}")
            
            if front_number > 0:
                suitable_primes = three_digit_primes if front_number <= 999 else four_digit_primes
                front_closest = find_closest_primes(front_number, suitable_primes, count)
                logger.debug(f"Found {len(front_closest)} closest primes for front part")
                
                # 將質數轉換回類似車牌的格式
                front_formatted_primes = []
                for p, d in front_closest:
                    formatted_prime = number_to_plate_format(p, front_part)
                    logger.debug(f"Front part: Prime {p} formatted as {formatted_prime}")
                    front_formatted_primes.append({"prime": p, "formatted_prime": formatted_prime, "distance": d})
                
                results["front_part"] = {
                    "original": front_part,
                    "number": front_number,
                    "closest_primes": front_formatted_primes
                }
            
            # 分析後半部分
            back_number = plate_to_number(back_part)
            logger.debug(f"Back part {back_part} converted to number: {back_number}")
            
            if back_number > 0:
                suitable_primes = three_digit_primes if back_number <= 999 else four_digit_primes
                back_closest = find_closest_primes(back_number, suitable_primes, count)
                logger.debug(f"Found {len(back_closest)} closest primes for back part")
                
                # 將質數轉換回類似車牌的格式
                back_formatted_primes = []
                for p, d in back_closest:
                    formatted_prime = number_to_plate_format(p, back_part)
                    logger.debug(f"Back part: Prime {p} formatted as {formatted_prime}")
                    back_formatted_primes.append({"prime": p, "formatted_prime": formatted_prime, "distance": d})
                
                results["back_part"] = {
                    "original": back_part,
                    "number": back_number,
                    "closest_primes": back_formatted_primes
                }
        
        # 分析完整車牌（忽略連字符）
        full_plate = plate.replace('-', '')
        full_number = plate_to_number(full_plate)
        logger.debug(f"Full plate {full_plate} converted to number: {full_number}")
        
        if full_number > 0:
            full_closest = find_closest_primes(full_number, all_primes, count)
            logger.debug(f"Found {len(full_closest)} closest primes for full plate")
            
            # 將質數轉換回類似車牌的格式
            full_formatted_primes = []
            for p, d in full_closest:
                formatted_prime = number_to_plate_format(p, full_plate)
                logger.debug(f"Full plate: Prime {p} formatted as {formatted_prime}")
                full_formatted_primes.append({"prime": p, "formatted_prime": formatted_prime, "distance": d})
            
            results["full_plate"] = {
                "original": full_plate,
                "number": full_number,
                "closest_primes": full_formatted_primes
            }
        
        logger.debug(f"Final results: {results}")
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in analyze_plate: {e}")
        return jsonify({"error": str(e)}), 500

# 提供前端靜態文件
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_static(path):
    static_folder = os.path.join(app_path, 'license_plate_frontend')
    if os.path.exists(static_folder):
        return send_from_directory(static_folder, path)
    else:
        # 如果靜態文件夾不存在，返回內嵌的HTML
        if path == 'index.html' or path == '':
            return render_template_string(get_embedded_html())
        else:
            return "File not found", 404

# 內嵌的HTML模板
def get_embedded_html():
    return '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的車牌號碼與質數的距離</title>
    <style>
        body {
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        input, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            display: block;
            margin: 20px auto;
            transition: background-color 0.3s;
        }
        button:hover {
            background-color: #2980b9;
        }
        .results {
            margin-top: 30px;
            border-top: 1px solid #eee;
            padding-top: 20px;
        }
        .result-section {
            margin-bottom: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-radius: 4px;
        }
        .result-section h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #f2f2f2;
        }
        .loading {
            text-align: center;
            display: none;
        }
        .error {
            color: #e74c3c;
            text-align: center;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>我的車牌號碼與質數的距離</h1>
        
        <div class="form-group">
            <label for="plate">輸入車牌號碼：</label>
            <input type="text" id="plate" placeholder="例如：ABC-1234 或 ABC1234" autofocus>
            <small>可包含或不包含「-」號</small>
        </div>
        
        <div class="form-group">
            <label for="count">顯示結果數量：</label>
            <select id="count">
                <option value="3">3個</option>
                <option value="5" selected>5個</option>
                <option value="10">10個</option>
            </select>
        </div>
        
        <button id="analyze">分析車牌</button>
        
        <div class="loading" id="loading">
            <p>分析中，請稍候...</p>
        </div>
        
        <div class="error" id="error"></div>
        
        <div class="results" id="results"></div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const plateInput = document.getElementById('plate');
            const countSelect = document.getElementById('count');
            const analyzeBtn = document.getElementById('analyze');
            const loadingDiv = document.getElementById('loading');
            const errorDiv = document.getElementById('error');
            const resultsDiv = document.getElementById('results');
            
            // 當按下Enter鍵時自動提交
            plateInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    analyzePlate();
                }
            });
            
            // 點擊分析按鈕
            analyzeBtn.addEventListener('click', analyzePlate);
            
            function analyzePlate() {
                const plate = plateInput.value.trim();
                if (!plate) {
                    showError('請輸入車牌號碼');
                    return;
                }
                
                // 清空先前結果並顯示載入中
                resultsDiv.innerHTML = '';
                errorDiv.textContent = '';
                loadingDiv.style.display = 'block';
                
                // 發送API請求
                fetch('/api/analyze_plate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        plate: plate,
                        count: parseInt(countSelect.value)
                    })
                })
                .then(response => response.json())
                .then(data => {
                    loadingDiv.style.display = 'none';
                    
                    if (data.error) {
                        showError(data.error);
                        return;
                    }
                    
                    displayResults(data);
                })
                .catch(error => {
                    loadingDiv.style.display = 'none';
                    showError('發生錯誤：' + error.message);
                });
            }
            
            function showError(message) {
                errorDiv.textContent = message;
            }
            
            function displayResults(data) {
                let html = '';
                
                // 顯示完整車牌結果
                if (data.full_plate) {
                    html += createResultSection(
                        '完整車牌',
                        data.full_plate.original,
                        data.full_plate.number,
                        data.full_plate.closest_primes
                    );
                }
                
                // 顯示前半部分結果
                if (data.front_part) {
                    html += createResultSection(
                        '前半部分',
                        data.front_part.original,
                        data.front_part.number,
                        data.front_part.closest_primes
                    );
                }
                
                // 顯示後半部分結果
                if (data.back_part) {
                    html += createResultSection(
                        '後半部分',
                        data.back_part.original,
                        data.back_part.number,
                        data.back_part.closest_primes
                    );
                }
                
                resultsDiv.innerHTML = html;
            }
            
            function createResultSection(title, original, number, primes) {
                let html = `
                    <div class="result-section">
                        <h3>${title}：${original}</h3>
                        <p>轉換後的數字：${number}</p>
                        <table>
                            <thead>
                                <tr>
                                    <th>質數</th>
                                    <th>格式化顯示</th>
                                    <th>距離</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                primes.forEach(item => {
                    html += `
                        <tr>
                            <td>${item.prime}</td>
                            <td>${item.formatted_prime}</td>
                            <td>${item.distance}</td>
                        </tr>
                    `;
                });
                
                html += `
                            </tbody>
                        </table>
                    </div>
                `;
                
                return html;
            }
        });
    </script>
</body>
</html>
'''

# 啟動 Flask 服務器
def run_flask_server():
    app.run(host='127.0.0.1', port=5001, debug=False)

# 開啟瀏覽器
def open_browser():
    time.sleep(1.5)  # 等待服務器啟動
    webbrowser.open('http://127.0.0.1:5001')

# 主函數
def main():
    try:
        logger.info(f"Starting {APP_TITLE} v{APP_VERSION}")
        
        # 檢查數據庫是否存在
        if not os.path.exists(DB_PATH):
            logger.error(f"Database not found at {DB_PATH}")
            print(f"錯誤：找不到數據庫文件 {DB_PATH}")
            time.sleep(5)
            return
            
        # 啟動瀏覽器線程
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # 啟動 Flask 服務器
        run_flask_server()
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        print(f"發生錯誤：{e}")
        time.sleep(5)

if __name__ == "__main__":
    main()
