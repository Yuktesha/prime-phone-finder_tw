import os
import logging
import math
import requests
from flask import Flask, request, render_template_string, jsonify
import re

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('PhonePrimeFinder')

app = Flask(__name__)

# PrimesDB 相關常量和函數
PRIMESDB_URL = "https://github.com/pekesoft/PrimesDB/raw/main/PrimesDB/0000.pdb"
PRIMESDB_CACHE_FILE = "primesdb_cache.bin"
primesdb_data = None

def download_primesdb():
    """下載 PrimesDB 數據文件"""
    global primesdb_data
    try:
        # 首先檢查是否有本地緩存
        if os.path.exists(PRIMESDB_CACHE_FILE):
            logger.info(f"從本地緩存加載 PrimesDB: {PRIMESDB_CACHE_FILE}")
            with open(PRIMESDB_CACHE_FILE, 'rb') as f:
                primesdb_data = f.read()
            return True
        
        # 如果沒有本地緩存，從 GitHub 下載
        logger.info(f"從 GitHub 下載 PrimesDB: {PRIMESDB_URL}")
        response = requests.get(PRIMESDB_URL)
        if response.status_code == 200:
            primesdb_data = response.content
            # 保存到本地緩存
            with open(PRIMESDB_CACHE_FILE, 'wb') as f:
                f.write(primesdb_data)
            logger.info(f"PrimesDB 下載成功，大小: {len(primesdb_data)} 字節")
            return True
        else:
            logger.error(f"下載 PrimesDB 失敗: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"下載 PrimesDB 時出錯: {e}")
        return False

def is_prime_primesdb(number):
    """使用 PrimesDB 檢查一個數字是否為質數"""
    global primesdb_data
    
    # 如果數據未加載，嘗試加載
    if primesdb_data is None:
        if not download_primesdb():
            # 如果無法加載 PrimesDB，回退到傳統方法
            return is_prime(number)
    
    # 使用 PrimesDB 算法檢查質數
    # 首先檢查基本情況
    if number < 2:
        return False
    if number == 2 or number == 3 or number == 5 or number == 7:
        return True
    if number % 2 == 0 or number % 3 == 0 or number % 5 == 0:
        return False
    
    # 只檢查末尾為 1, 3, 7, 9 的數字
    last_digit = number % 10
    if last_digit not in [1, 3, 7, 9]:
        return False
    
    # 計算 PrimesDB 中的位置
    decade = number // 10
    address = int(decade / 2 + 0.5) - 1
    
    # 檢查地址是否在數據範圍內
    if address < 0 or address >= len(primesdb_data):
        # 如果超出範圍，回退到傳統方法
        return is_prime(number)
    
    # 計算位偏移
    bit_positions = {1: 0, 3: 1, 7: 2, 9: 3}
    bit_pos = bit_positions[last_digit]
    
    # 如果十位數是偶數，使用高位元組
    if decade % 2 == 0:
        bit_pos += 4
    
    # 獲取字節並檢查相應的位
    byte_value = primesdb_data[address]
    is_prime_value = (byte_value >> bit_pos) & 1
    
    return is_prime_value == 1

def is_prime(n):
    """傳統方法檢查質數"""
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

def find_primes_near(number, count, direction):
    """查找指定數字附近的質數"""
    global primesdb_data
    
    # 如果數據未加載，嘗試加載
    if primesdb_data is None:
        if not download_primesdb():
            # 如果無法加載 PrimesDB，回退到傳統方法
            return find_primes_near_traditional(number, count, direction)
    
    # 如果數字超過 PrimesDB 的範圍 (約 1,342,177,280)，使用傳統方法
    if number > 1000000000:  # 設置一個安全的閾值
        return find_primes_near_traditional(number, count, direction)
    
    result = []
    current = number
    
    # 根據方向調整步進
    step = 1 if direction == 'larger' else -1
    
    # 如果是向下查找，先減 1
    if direction == 'smaller':
        current -= 1
    # 如果是向上查找，先加 1
    else:
        current += 1
    
    # 查找指定數量的質數
    while len(result) < count and current > 1 and current < 10**10:  # 設置一個上限，避免無限循環
        if is_prime_primesdb(current):
            result.append(current)
        current += step
    
    return result

def find_primes_near_traditional(number, count, direction):
    """使用傳統方法查找指定數字附近的質數"""
    result = []
    current = number
    
    # 根據方向調整步進
    step = 1 if direction == 'larger' else -1
    
    # 如果是向下查找，先減 1
    if direction == 'smaller':
        current -= 1
    # 如果是向上查找，先加 1
    else:
        current += 1
    
    # 查找指定數量的質數
    while len(result) < count and current > 1:
        if is_prime(current):
            result.append(current)
        current += step
    
    return result

def find_closest_primes(number, count=5):
    """找出離指定數字最近的質數"""
    try:
        logger.info(f"查詢最接近 {number} 的質數，數量: {count}")
        
        # 使用 PrimesDB 查找較大和較小的質數
        larger_primes = find_primes_near(number, count, 'larger')
        smaller_primes = find_primes_near(number, count, 'smaller')
        
        logger.info(f"查詢結果: 較大質數 {len(larger_primes)} 個, 較小質數 {len(smaller_primes)} 個")
        
        # 合併結果並計算距離
        result = []
        
        # 處理較大的質數
        for prime in larger_primes:
            distance = prime - number
            result.append((prime, distance))
        
        # 處理較小的質數
        for prime in smaller_primes:
            distance = number - prime
            result.append((prime, distance))
        
        # 按距離排序
        result.sort(key=lambda x: x[1])
        
        # 限制結果數量
        result = result[:count]
        
        # 將結果轉換為字典
        results = []
        for prime, distance in result:
            results.append({
                'prime': prime,
                'distance': distance
            })
        
        logger.info(f"最終結果: {results}")
        
        return results
    except Exception as e:
        logger.error(f"查詢質數時出錯: {e}")
        return []

def clean_phone_number(phone):
    """清理電話號碼，只保留數字"""
    return re.sub(r'[^0-9]', '', phone)

@app.route('/')
def index():
    """首頁"""
    return render_template_string(get_index_template())

@app.route('/search', methods=['POST'])
def search():
    """搜索電話號碼與質數的距離"""
    try:
        phone_number = request.form.get('phone_number', '')
        count = int(request.form.get('count', '10'))
        
        # 限制結果數量在 1-512 之間
        count = max(1, min(512, count))
        
        # 清理電話號碼，只保留數字
        clean_number = clean_phone_number(phone_number)
        
        if not clean_number:
            return jsonify({'error': '請輸入有效的電話號碼'}), 400
        
        # 將電話號碼轉換為整數
        number = int(clean_number)
        
        # 查詢最接近的質數
        closest_primes = find_closest_primes(number, count)
        
        # 檢查電話號碼本身是否為質數
        is_prime_number = is_prime_primesdb(number)
        
        return jsonify({
            'phone_number': phone_number,
            'clean_number': clean_number,
            'is_prime': is_prime_number,
            'closest_primes': closest_primes,
            'count': count
        })
    
    except Exception as e:
        logger.error(f"處理請求時出錯: {e}")
        return jsonify({'error': f'處理請求時出錯: {str(e)}'}), 500

def get_index_template():
    """獲取首頁模板"""
    return '''
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>電話號碼與質數的距離</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            h1 {
                color: #2c3e50;
                text-align: center;
                margin-bottom: 30px;
            }
            .container {
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            .form-container {
                display: flex;
                align-items: flex-end;
                gap: 15px;
                margin-bottom: 20px;
            }
            .form-group {
                flex: 1;
            }
            .count-group {
                width: 100px;
                flex: none;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input[type="text"], input[type="number"] {
                width: 100%;
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 16px;
                box-sizing: border-box;
            }
            button {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                transition: background-color 0.3s;
                height: 38px;
            }
            button:hover {
                background-color: #2980b9;
            }
            #results {
                margin-top: 30px;
                display: none;
            }
            .result-header {
                margin-bottom: 15px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }
            .prime-info {
                margin-bottom: 10px;
                padding: 10px;
                background-color: #f9f9f9;
                border-radius: 4px;
            }
            .prime-info.is-prime {
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
            }
            .prime-info.not-prime {
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                color: #721c24;
            }
            .prime-list {
                margin-top: 20px;
            }
            .prime-item {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }
            .prime-item:last-child {
                border-bottom: none;
            }
            .loading {
                text-align: center;
                margin: 20px 0;
                display: none;
            }
            .error {
                color: #721c24;
                background-color: #f8d7da;
                border: 1px solid #f5c6cb;
                padding: 10px;
                border-radius: 4px;
                margin-top: 20px;
                display: none;
            }
            .celebration {
                text-align: center;
                font-size: 24px;
                margin: 20px 0;
                animation: celebrate 1s infinite;
                display: none;
            }
            @keyframes celebrate {
                0% { transform: scale(1); }
                50% { transform: scale(1.2); }
                100% { transform: scale(1); }
            }
            .footer {
                text-align: center;
                margin-top: 20px;
                font-size: 14px;
                color: #777;
                padding-top: 10px;
                border-top: 1px solid #eee;
            }
            .footer a {
                color: #3498db;
                text-decoration: none;
            }
            .footer a:hover {
                text-decoration: underline;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>電話號碼與質數的距離</h1>
            
            <div class="form-container">
                <div class="form-group">
                    <label for="phone_number">請輸入電話號碼：</label>
                    <input type="text" id="phone_number" placeholder="例如：0912345678 或 +886912345678 或 02-12345678">
                </div>
                
                <div class="form-group count-group">
                    <label for="result_count">結果數量：</label>
                    <input type="number" id="result_count" value="10" min="1" max="512" style="width: 100%;">
                </div>
                
                <button id="search_btn">查詢</button>
            </div>
            
            <div class="loading" id="loading">
                <p>正在查詢中，請稍候...</p>
            </div>
            
            <div class="error" id="error"></div>
            
            <div id="results">
                <div class="result-header">
                    <h2>查詢結果</h2>
                    <p id="phone_display"></p>
                </div>
                
                <div class="prime-info" id="prime_status"></div>
                
                <div class="celebration" id="celebration">
                    🎉 恭喜！您的電話號碼是質數！🎉
                </div>
                
                <div class="prime-list">
                    <h3>最接近的質數：</h3>
                    <div id="prime_list"></div>
                </div>
            </div>
            
            <div class="footer">
                <p>© 2025 質人精神：電話號碼與質數的距離 | 基於<a href="https://github.com/pekesoft/PrimesDB" target="_blank">PrimesDB</a>高效質數資料庫的應用</p>
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const searchBtn = document.getElementById('search_btn');
                const phoneInput = document.getElementById('phone_number');
                const resultCountInput = document.getElementById('result_count');
                const resultsDiv = document.getElementById('results');
                const phoneDisplay = document.getElementById('phone_display');
                const primeStatus = document.getElementById('prime_status');
                const primeList = document.getElementById('prime_list');
                const loading = document.getElementById('loading');
                const errorDiv = document.getElementById('error');
                const celebration = document.getElementById('celebration');
                
                // 添加回車鍵搜索功能
                phoneInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        searchBtn.click();
                    }
                });
                
                resultCountInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        searchBtn.click();
                    }
                });
                
                searchBtn.addEventListener('click', function() {
                    const phoneNumber = phoneInput.value.trim();
                    const count = parseInt(resultCountInput.value) || 10;
                    
                    // 限制結果數量在 1-512 之間
                    const limitedCount = Math.max(1, Math.min(512, count));
                    
                    if (!phoneNumber) {
                        showError('請輸入電話號碼');
                        return;
                    }
                    
                    // 重置顯示
                    resultsDiv.style.display = 'none';
                    errorDiv.style.display = 'none';
                    celebration.style.display = 'none';
                    loading.style.display = 'block';
                    
                    // 創建 FormData
                    const formData = new FormData();
                    formData.append('phone_number', phoneNumber);
                    formData.append('count', limitedCount);
                    
                    // 發送請求
                    fetch('/search', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => {
                        if (!response.ok) {
                            return response.json().then(data => {
                                throw new Error(data.error || '請求失敗');
                            });
                        }
                        return response.json();
                    })
                    .then(data => {
                        loading.style.display = 'none';
                        displayResults(data);
                    })
                    .catch(error => {
                        loading.style.display = 'none';
                        showError(error.message);
                    });
                });
                
                function displayResults(data) {
                    // 顯示電話號碼
                    phoneDisplay.textContent = `電話號碼：${data.phone_number} (純數字：${data.clean_number})`;
                    
                    // 顯示是否為質數
                    if (data.is_prime) {
                        primeStatus.textContent = `${data.clean_number} 是一個質數！`;
                        primeStatus.className = 'prime-info is-prime';
                        celebration.style.display = 'block';
                    } else {
                        primeStatus.textContent = `${data.clean_number} 不是質數`;
                        primeStatus.className = 'prime-info not-prime';
                    }
                    
                    // 顯示最接近的質數
                    primeList.innerHTML = '';
                    data.closest_primes.forEach(item => {
                        const primeItem = document.createElement('div');
                        primeItem.className = 'prime-item';
                        primeItem.innerHTML = `
                            <span>質數：${item.prime}</span>
                            <span>距離：${item.distance}</span>
                        `;
                        primeList.appendChild(primeItem);
                    });
                    
                    // 顯示結果區域
                    resultsDiv.style.display = 'block';
                }
                
                function showError(message) {
                    errorDiv.textContent = message;
                    errorDiv.style.display = 'block';
                }
            });
        </script>
    </body>
    </html>
    '''

# 使用 with app.app_context() 預加載 PrimesDB 數據
with app.app_context():
    # 預加載 PrimesDB 數據
    download_primesdb()

if __name__ == '__main__':
    logger.info("Starting 電話號碼與質數的距離 v1.0.0")
    app.run(host='127.0.0.1', port=5003, debug=True)
