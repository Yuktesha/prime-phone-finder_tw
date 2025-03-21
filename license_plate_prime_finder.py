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
        logging.FileHandler("license_plate_prime_finder_log.txt"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("LicensePlatePrimeFinder")

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

# 36進位轉換函數
def base36_to_int(s):
    """將36進位字符串轉換為10進位整數"""
    # 檢查是否包含字母
    has_letters = any(c.isalpha() for c in s)
    
    # 如果不包含字母，則直接作為10進位數字處理
    if not has_letters:
        try:
            return int(s)
        except ValueError:
            # 如果無法轉換為整數，則返回0
            return 0
    
    # 包含字母，按36進位處理
    return int(s, 36)

def int_to_base36(i, original_format):
    """將10進位整數轉換為36進位字符串，保持原始格式的特性"""
    # 檢查原始格式是否包含字母
    has_letters = any(c.isalpha() for c in original_format)
    
    # 如果原始格式不包含字母，則直接返回10進位數字字符串
    if not has_letters:
        return str(i)
    
    # 包含字母，按36進位處理
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if i == 0:
        return "0"
    
    result = ""
    while i > 0:
        result = digits[i % 36] + result
        i //= 36
    
    return result

# 計算兩個數字之間的距離
def calculate_distance(num1, num2):
    """計算兩個數字之間的距離"""
    return abs(num1 - num2)

# 從數據庫獲取質數
def get_primes_from_db():
    """從數據庫獲取質數"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 獲取所有質數
        cursor.execute("SELECT value FROM primes ORDER BY value")
        all_primes = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        return all_primes
    except Exception as e:
        logger.error(f"Error getting primes from database: {e}")
        return []

# 查找最接近的質數
def find_closest_primes(number, primes, count=10):
    """查找最接近指定數字的質數"""
    distances = [(prime, calculate_distance(number, prime)) for prime in primes]
    distances.sort(key=lambda x: x[1])  # 按距離排序
    return distances[:count]

# API 路由：分析車牌號碼
@app.route('/api/analyze_plate', methods=['POST'])
def analyze_plate():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "缺少數據"}), 400
        
        part1 = data.get('part1', '').strip().upper()
        part2 = data.get('part2', '').strip().upper()
        count = int(data.get('count', 10))  # 預設顯示10個最接近的質數
        
        # 驗證輸入
        if not part1 or not part2:
            return jsonify({"error": "請輸入完整的車牌號碼"}), 400
        
        if len(part1) < 2 or len(part1) > 5 or len(part2) < 2 or len(part2) > 5:
            return jsonify({"error": "車牌號碼格式不正確，每部分應為2-5個字符"}), 400
        
        # 限制結果數量
        if count < 1:
            count = 1
        if count > 256:
            count = 256
        
        # 獲取質數
        all_primes = get_primes_from_db()
        
        results = {}
        
        # 分析第一部分
        try:
            part1_base36 = part1
            part1_int = base36_to_int(part1)
            
            # 檢查是否包含字母
            part1_has_letters = any(c.isalpha() for c in part1)
            
            # 查找最接近的質數
            part1_closest = find_closest_primes(part1_int, all_primes, count)
            
            # 將質數轉換回適當格式
            part1_formatted = []
            for p, d in part1_closest:
                base36_repr = int_to_base36(p, part1)
                part1_formatted.append({
                    "prime_base10": p,
                    "prime_base36": base36_repr,
                    "distance": d,
                    "has_letters": part1_has_letters
                })
            
            results["part1"] = {
                "original": part1,
                "base10": part1_int,
                "closest_primes": part1_formatted,
                "has_letters": part1_has_letters
            }
        except ValueError as e:
            return jsonify({"error": f"第一部分格式錯誤: {str(e)}"}), 400
        
        # 分析第二部分
        try:
            part2_base36 = part2
            part2_int = base36_to_int(part2)
            
            # 檢查是否包含字母
            part2_has_letters = any(c.isalpha() for c in part2)
            
            # 查找最接近的質數
            part2_closest = find_closest_primes(part2_int, all_primes, count)
            
            # 將質數轉換回適當格式
            part2_formatted = []
            for p, d in part2_closest:
                base36_repr = int_to_base36(p, part2)
                part2_formatted.append({
                    "prime_base10": p,
                    "prime_base36": base36_repr,
                    "distance": d,
                    "has_letters": part2_has_letters
                })
            
            results["part2"] = {
                "original": part2,
                "base10": part2_int,
                "closest_primes": part2_formatted,
                "has_letters": part2_has_letters
            }
        except ValueError as e:
            return jsonify({"error": f"第二部分格式錯誤: {str(e)}"}), 400
        
        # 分析完整車牌
        try:
            full_plate = part1 + part2
            full_int = base36_to_int(full_plate)
            
            # 檢查是否包含字母
            full_has_letters = any(c.isalpha() for c in full_plate)
            
            # 查找最接近的質數
            full_closest = find_closest_primes(full_int, all_primes, count)
            
            # 將質數轉換回適當格式
            full_formatted = []
            for p, d in full_closest:
                base36_repr = int_to_base36(p, full_plate)
                full_formatted.append({
                    "prime_base10": p,
                    "prime_base36": base36_repr,
                    "distance": d,
                    "has_letters": full_has_letters
                })
            
            results["full"] = {
                "original": full_plate,
                "base10": full_int,
                "closest_primes": full_formatted,
                "has_letters": full_has_letters
            }
        except ValueError as e:
            return jsonify({"error": f"完整車牌格式錯誤: {str(e)}"}), 400
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in analyze_plate: {e}")
        return jsonify({"error": str(e)}), 500

# 首頁路由
@app.route('/')
def index():
    return render_template_string(get_embedded_html())

# 內嵌的HTML模板
def get_embedded_html():
    return '''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的車牌號碼與質數的距離</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
            color: #333;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
        }
        .container {
            width: 85%;
            max-width: 1200px;
            margin: 20px auto;
            background-color: #fff;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
            font-size: 28px;
        }
        .input-section {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-bottom: 30px;
            width: 100%;
        }
        .input-container {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            align-items: center;
            gap: 15px;
            width: 100%;
            margin-bottom: 20px;
        }
        .input-group {
            display: flex;
            align-items: center;
        }
        .plate-input {
            width: 120px;
            padding: 12px;
            font-size: 18px;
            border: 2px solid #3498db;
            border-radius: 4px;
            text-align: center;
            margin: 0 5px;
            text-transform: uppercase;
        }
        .separator {
            font-size: 24px;
            margin: 0 5px;
            font-weight: bold;
        }
        .count-group {
            display: flex;
            align-items: center;
            margin-left: 10px;
        }
        .count-input {
            width: 70px;
            padding: 12px;
            font-size: 16px;
            border: 1px solid #ddd;
            border-radius: 4px;
            text-align: center;
        }
        label {
            margin-right: 10px;
            font-weight: bold;
        }
        button {
            background-color: #3498db;
            color: white;
            border: none;
            padding: 12px 25px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: background-color 0.3s, transform 0.2s;
            margin-top: 10px;
        }
        button:hover {
            background-color: #2980b9;
            transform: translateY(-2px);
        }
        button:active {
            transform: translateY(0);
        }
        .results {
            margin-top: 30px;
        }
        .result-section {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 8px;
            border-left: 4px solid #3498db;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }
        .result-section h3 {
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
            font-size: 20px;
        }
        .result-info {
            margin-bottom: 15px;
            font-size: 16px;
        }
        .loading {
            text-align: center;
            display: none;
            margin: 20px 0;
        }
        .loading-spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .error {
            color: #e74c3c;
            text-align: center;
            margin: 20px 0;
            padding: 10px;
            background-color: #fadbd8;
            border-radius: 4px;
            display: none;
        }
        .plate-display {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 15px 0;
        }
        .plate-part {
            background-color: #fff;
            border: 2px solid #333;
            padding: 8px 15px;
            font-size: 24px;
            font-weight: bold;
            min-width: 80px;
            text-align: center;
        }
        .plate-part-left {
            text-align: right;
            border-right: none;
            border-radius: 4px 0 0 4px;
        }
        .plate-part-right {
            text-align: left;
            border-left: none;
            border-radius: 0 4px 4px 0;
        }
        .plate-results {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            justify-content: center;
        }
        .plate-result-item {
            width: calc(20% - 16px);
            min-width: 180px;
            margin-bottom: 15px;
            padding: 15px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .plate-result-item:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .plate-info {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-top: 8px;
            font-size: 14px;
            color: #7f8c8d;
        }
        .plate-info span {
            margin: 2px 0;
        }
        .action-buttons {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 20px;
        }
        .action-button {
            background-color: #2ecc71;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            display: flex;
            align-items: center;
            transition: background-color 0.3s;
        }
        .action-button:hover {
            background-color: #27ae60;
        }
        .action-button i {
            margin-right: 5px;
        }
        
        /* 響應式設計 */
        @media (max-width: 1600px) {
            .plate-result-item {
                width: calc(25% - 16px);
            }
        }
        
        @media (max-width: 1200px) {
            .plate-result-item {
                width: calc(33.333% - 16px);
            }
        }
        
        @media (max-width: 768px) {
            .container {
                width: 95%;
                padding: 15px;
            }
            .plate-result-item {
                width: calc(50% - 15px);
            }
            h1 {
                font-size: 24px;
            }
        }
        
        @media (max-width: 576px) {
            .container {
                width: 100%;
                border-radius: 0;
            }
            .plate-result-item {
                width: 100%;
            }
            .input-container {
                flex-direction: column;
            }
            .count-group {
                margin-left: 0;
                margin-top: 10px;
            }
            h1 {
                font-size: 22px;
            }
            .action-buttons {
                flex-direction: column;
                align-items: center;
            }
            .action-button {
                width: 100%;
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>我的車牌號碼與質數的距離</h1>
        
        <div class="input-section">
            <div class="input-container">
                <div class="input-group">
                    <input type="text" id="part1" class="plate-input" placeholder="ABC" maxlength="5" autofocus>
                    <span class="separator">-</span>
                    <input type="text" id="part2" class="plate-input" placeholder="1234" maxlength="5">
                </div>
                
                <div class="count-group">
                    <label for="count">顯示數量:</label>
                    <input type="number" id="count" class="count-input" value="10" min="1" max="256">
                </div>
            </div>
            
            <button id="analyze">分析車牌</button>
        </div>
        
        <div class="loading" id="loading">
            <div class="loading-spinner"></div>
            <p>分析中，請稍候...</p>
        </div>
        
        <div class="error" id="error"></div>
        
        <div class="results" id="results"></div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const part1Input = document.getElementById('part1');
            const part2Input = document.getElementById('part2');
            const countInput = document.getElementById('count');
            const analyzeBtn = document.getElementById('analyze');
            const loadingDiv = document.getElementById('loading');
            const errorDiv = document.getElementById('error');
            const resultsDiv = document.getElementById('results');
            
            // 自動轉換為大寫
            part1Input.addEventListener('input', function() {
                this.value = this.value.toUpperCase();
            });
            
            part2Input.addEventListener('input', function() {
                this.value = this.value.toUpperCase();
            });
            
            // 當按下Enter鍵時自動提交
            part1Input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    part2Input.focus();
                }
            });
            
            part2Input.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    countInput.focus();
                }
            });
            
            countInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    analyzePlate();
                }
            });
            
            // 點擊分析按鈕
            analyzeBtn.addEventListener('click', analyzePlate);
            
            function analyzePlate() {
                const part1 = part1Input.value.trim();
                const part2 = part2Input.value.trim();
                const count = parseInt(countInput.value);
                
                if (!part1 || !part2) {
                    showError('請輸入完整的車牌號碼');
                    return;
                }
                
                if (part1.length < 2 || part1.length > 5 || part2.length < 2 || part2.length > 5) {
                    showError('車牌號碼格式不正確，每部分應為2-5個字符');
                    return;
                }
                
                if (isNaN(count) || count < 1 || count > 256) {
                    showError('顯示數量應為1-256之間的數字');
                    return;
                }
                
                // 清空先前結果並顯示載入中
                resultsDiv.innerHTML = '';
                errorDiv.style.display = 'none';
                loadingDiv.style.display = 'block';
                
                // 發送API請求
                fetch('/api/analyze_plate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        part1: part1,
                        part2: part2,
                        count: count
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
                errorDiv.style.display = 'block';
            }
            
            function displayResults(data) {
                let html = '';
                
                // 顯示原始車牌
                html += `
                    <div class="result-section">
                        <h3>原始車牌</h3>
                        <div class="plate-display">
                            <div class="plate-part plate-part-left">${data.part1.original}</div>
                            <span class="separator">-</span>
                            <div class="plate-part plate-part-right">${data.part2.original}</div>
                        </div>
                        <div class="result-info">
                `;
                
                // 只有當包含字母時才顯示進位轉換說明
                if (data.part1.has_letters) {
                    html += `<p>前半部分 ${data.part1.original} 包含字母，以36進位轉換為10進位：${data.part1.base10}</p>`;
                }
                
                if (data.part2.has_letters) {
                    html += `<p>後半部分 ${data.part2.original} 包含字母，以36進位轉換為10進位：${data.part2.base10}</p>`;
                }
                
                if (data.full.has_letters) {
                    html += `<p>完整車牌 ${data.full.original} 包含字母，以36進位轉換為10進位：${data.full.base10}</p>`;
                }
                
                html += `
                        </div>
                    </div>
                `;
                
                // 顯示前半部分結果
                html += `
                    <div class="result-section">
                        <h3>最接近的質數車牌</h3>
                        <div class="plate-results">
                `;
                
                // 整合前半部分和後半部分的結果，但只顯示10組配對
                for (let i = 0; i < Math.min(data.part1.closest_primes.length, data.part2.closest_primes.length, 10); i++) {
                    const part1Item = data.part1.closest_primes[i];
                    const part2Item = data.part2.closest_primes[i];
                    
                    html += `
                        <div class="plate-result-item">
                            <div class="plate-display">
                                <div class="plate-part plate-part-left">${part1Item.prime_base36}</div>
                                <span class="separator">-</span>
                                <div class="plate-part plate-part-right">${part2Item.prime_base36}</div>
                            </div>
                            <div class="plate-info">
                                <span>前半部: ${part1Item.prime_base10} (距離: ${part1Item.distance})</span>
                                <span>後半部: ${part2Item.prime_base10} (距離: ${part2Item.distance})</span>
                            </div>
                        </div>
                    `;
                }
                
                // 顯示完整車牌結果
                html += `
                        </div>
                        <div class="action-buttons">
                            <button class="action-button" id="copy-to-clipboard"><i class="fas fa-copy"></i> 複製到剪貼簿</button>
                            <button class="action-button" id="export-csv"><i class="fas fa-file-export"></i> 輸出為CSV</button>
                        </div>
                    </div>
                    
                    <div class="result-section">
                        <h3>完整車牌 (${data.full.original}) 最接近的質數</h3>
                `;
                
                if (data.full.has_letters) {
                    html += `
                        <div class="result-info">
                            <p>36進位轉換為10進位：${data.full.base10}</p>
                        </div>
                    `;
                }
                
                html += `
                        <div class="plate-results">
                `;
                
                data.full.closest_primes.forEach(item => {
                    // 分割完整質數為前半部和後半部
                    const fullBase36 = item.prime_base36;
                    const part1Length = data.part1.original.length;
                    const part2Length = data.part2.original.length;
                    
                    let part1Prime, part2Prime;
                    
                    // 確保正確分割
                    if (fullBase36.length <= part1Length) {
                        part1Prime = fullBase36.padStart(part1Length, '0');
                        part2Prime = '0'.repeat(part2Length);
                    } else if (fullBase36.length <= part1Length + part2Length) {
                        part1Prime = fullBase36.substring(0, Math.max(0, fullBase36.length - part2Length)).padStart(part1Length, '0');
                        part2Prime = fullBase36.substring(Math.max(0, fullBase36.length - part2Length)).padStart(part2Length, '0');
                    } else {
                        // 如果質數太長，只取最後的部分
                        part1Prime = fullBase36.substring(0, part1Length);
                        part2Prime = fullBase36.substring(part1Length, part1Length + part2Length);
                    }
                    
                    html += `
                        <div class="plate-result-item">
                            <div class="plate-display">
                                <div class="plate-part plate-part-left">${part1Prime}</div>
                                <span class="separator">-</span>
                                <div class="plate-part plate-part-right">${part2Prime}</div>
                            </div>
                            <div class="plate-info">
                                <span>完整質數值: ${item.prime_base10}</span>
                                <span>距離: ${item.distance}</span>
                            </div>
                        </div>
                    `;
                });
                
                html += `
                        </div>
                        <div class="action-buttons">
                            <button class="action-button" id="copy-full-to-clipboard"><i class="fas fa-copy"></i> 複製到剪貼簿</button>
                            <button class="action-button" id="export-full-csv"><i class="fas fa-file-export"></i> 輸出為CSV</button>
                        </div>
                    </div>
                `;
                
                resultsDiv.innerHTML = html;
                
                // 添加複製到剪貼簿功能
                document.getElementById('copy-to-clipboard').addEventListener('click', function() {
                    let clipboardText = '前半部-後半部,前半部質數值,前半部距離,後半部質數值,後半部距離\n';
                    
                    for (let i = 0; i < Math.min(data.part1.closest_primes.length, data.part2.closest_primes.length, 10); i++) {
                        const part1Item = data.part1.closest_primes[i];
                        const part2Item = data.part2.closest_primes[i];
                        
                        clipboardText += `${part1Item.prime_base36}-${part2Item.prime_base36},${part1Item.prime_base10},${part1Item.distance},${part2Item.prime_base10},${part2Item.distance}\n`;
                    }
                    
                    navigator.clipboard.writeText(clipboardText).then(function() {
                        alert('已複製到剪貼簿');
                    }, function() {
                        alert('複製失敗');
                    });
                });
                
                // 添加輸出為CSV功能
                document.getElementById('export-csv').addEventListener('click', function() {
                    let csvContent = '前半部-後半部,前半部質數值,前半部距離,後半部質數值,後半部距離\n';
                    
                    for (let i = 0; i < Math.min(data.part1.closest_primes.length, data.part2.closest_primes.length, 10); i++) {
                        const part1Item = data.part1.closest_primes[i];
                        const part2Item = data.part2.closest_primes[i];
                        
                        csvContent += `${part1Item.prime_base36}-${part2Item.prime_base36},${part1Item.prime_base10},${part1Item.distance},${part2Item.prime_base10},${part2Item.distance}\n`;
                    }
                    
                    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.setAttribute('href', url);
                    link.setAttribute('download', `車牌質數_${data.part1.original}-${data.part2.original}.csv`);
                    link.style.visibility = 'hidden';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                });
                
                // 添加完整車牌複製到剪貼簿功能
                document.getElementById('copy-full-to-clipboard').addEventListener('click', function() {
                    let clipboardText = '完整車牌,質數值,距離\n';
                    
                    data.full.closest_primes.forEach(item => {
                        const fullBase36 = item.prime_base36;
                        const part1Length = data.part1.original.length;
                        const part2Length = data.part2.original.length;
                        
                        let part1Prime, part2Prime;
                        
                        if (fullBase36.length <= part1Length) {
                            part1Prime = fullBase36.padStart(part1Length, '0');
                            part2Prime = '0'.repeat(part2Length);
                        } else if (fullBase36.length <= part1Length + part2Length) {
                            part1Prime = fullBase36.substring(0, Math.max(0, fullBase36.length - part2Length)).padStart(part1Length, '0');
                            part2Prime = fullBase36.substring(Math.max(0, fullBase36.length - part2Length)).padStart(part2Length, '0');
                        } else {
                            part1Prime = fullBase36.substring(0, part1Length);
                            part2Prime = fullBase36.substring(part1Length, part1Length + part2Length);
                        }
                        
                        clipboardText += `${part1Prime}-${part2Prime},${item.prime_base10},${item.distance}\n`;
                    });
                    
                    navigator.clipboard.writeText(clipboardText).then(function() {
                        alert('已複製到剪貼簿');
                    }, function() {
                        alert('複製失敗');
                    });
                });
                
                // 添加完整車牌輸出為CSV功能
                document.getElementById('export-full-csv').addEventListener('click', function() {
                    let csvContent = '完整車牌,質數值,距離\n';
                    
                    data.full.closest_primes.forEach(item => {
                        const fullBase36 = item.prime_base36;
                        const part1Length = data.part1.original.length;
                        const part2Length = data.part2.original.length;
                        
                        let part1Prime, part2Prime;
                        
                        if (fullBase36.length <= part1Length) {
                            part1Prime = fullBase36.padStart(part1Length, '0');
                            part2Prime = '0'.repeat(part2Length);
                        } else if (fullBase36.length <= part1Length + part2Length) {
                            part1Prime = fullBase36.substring(0, Math.max(0, fullBase36.length - part2Length)).padStart(part1Length, '0');
                            part2Prime = fullBase36.substring(Math.max(0, fullBase36.length - part2Length)).padStart(part2Length, '0');
                        } else {
                            part1Prime = fullBase36.substring(0, part1Length);
                            part2Prime = fullBase36.substring(part1Length, part1Length + part2Length);
                        }
                        
                        csvContent += `${part1Prime}-${part2Prime},${item.prime_base10},${item.distance}\n`;
                    });
                    
                    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                    const url = URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.setAttribute('href', url);
                    link.setAttribute('download', `完整車牌質數_${data.full.original}.csv`);
                    link.style.visibility = 'hidden';
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                });
            }
        });
    </script>
</body>
</html>
'''

# 啟動 Flask 服務器
def run_flask_server():
    app.run(host='127.0.0.1', port=5002, debug=False)

# 開啟瀏覽器
def open_browser():
    time.sleep(1.5)  # 等待服務器啟動
    webbrowser.open('http://127.0.0.1:5002')

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
