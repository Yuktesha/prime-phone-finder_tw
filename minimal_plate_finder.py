import os
import sqlite3
import logging
from flask import Flask, render_template_string, request, jsonify

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('LicensePlatePrimeFinder')

app = Flask(__name__)
DB_PATH = 'D:/WinSurf/backend/primes.db'  # 使用絕對路徑

def get_db_connection():
    """連接到質數資料庫"""
    try:
        logger.info(f"Attempting to connect to database at {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def contains_letters(text):
    """檢查文字是否包含字母"""
    return any(c.isalpha() for c in text)

def to_base10(text):
    """將36進位（含字母）轉換為10進位"""
    result = 0
    for char in text.upper():
        if char.isdigit():
            value = int(char)
        else:
            value = ord(char) - ord('A') + 10
        result = result * 36 + value
    return result

def to_base36(number):
    """將10進位數字轉換為36進位字串"""
    if number == 0:
        return '0'
    
    chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    result = ''
    
    while number > 0:
        result = chars[number % 36] + result
        number //= 36
        
    return result

def find_closest_primes(number, count=10):
    """找出最接近指定數字的質數"""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to get database connection")
        return []
    
    try:
        logger.info(f"Finding closest primes to {number}")
        cursor = conn.cursor()
        
        # 檢查資料庫結構
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"Database tables: {[t['name'] for t in tables]}")
        
        # 假設表名為 'primes' 並且有 'value' 列
        # 找出小於目標數字的最大質數
        cursor.execute("SELECT value FROM primes WHERE value <= ? ORDER BY value DESC LIMIT ?", (number, count))
        lower_primes = cursor.fetchall()
        logger.info(f"Found {len(lower_primes)} lower primes")
        
        # 找出大於目標數字的最小質數
        cursor.execute("SELECT value FROM primes WHERE value >= ? ORDER BY value LIMIT ?", (number, count))
        higher_primes = cursor.fetchall()
        logger.info(f"Found {len(higher_primes)} higher primes")
        
        # 合併結果並計算距離
        results = []
        for row in lower_primes:
            prime = row['value']
            distance = number - prime
            results.append({
                'prime_base10': prime,
                'prime_base36': to_base36(prime),
                'distance': distance
            })
        
        for row in higher_primes:
            prime = row['value']
            distance = prime - number
            results.append({
                'prime_base10': prime,
                'prime_base36': to_base36(prime),
                'distance': distance
            })
        
        # 根據距離排序並限制結果數量
        results.sort(key=lambda x: x['distance'])
        return results[:count]
        
    except Exception as e:
        logger.error(f"Database query error: {e}")
        return []
    finally:
        conn.close()

@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>車牌號碼與質數的距離</title>
    <style>
        body {
            font-family: 'Microsoft JhengHei', Arial, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            width: 85%;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
        }
        
        .input-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
            gap: 10px;
        }
        
        .plate-input-group {
            display: flex;
            align-items: center;
        }
        
        .separator {
            font-size: 24px;
            margin: 0 10px;
            font-weight: bold;
        }
        
        input[type="text"], input[type="number"] {
            padding: 12px 15px;
            border: 2px solid #ddd;
            border-radius: 4px;
            font-size: 18px;
            width: 100px;
            text-align: center;
        }
        
        input[type="text"]:focus, input[type="number"]:focus {
            border-color: #3498db;
            outline: none;
        }
        
        .count-group {
            display: flex;
            align-items: center;
            margin-left: 20px;
        }
        
        .count-group label {
            margin-right: 10px;
            font-size: 16px;
        }
        
        .count-group input {
            width: 60px;
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
            margin-left: 20px;
        }
        
        button:hover {
            background-color: #2980b9;
        }
        
        .results {
            margin-top: 30px;
        }
        
        .result-section {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 8px;
        }
        
        .result-section h3 {
            margin-top: 0;
            color: #2c3e50;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
        }
        
        .plate-results {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }
        
        .plate-result-item {
            width: calc(20% - 16px);
            margin-bottom: 20px;
            background-color: white;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .plate-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .plate-table td {
            padding: 8px;
            text-align: center;
        }
        
        .plate-top-row {
            background-color: #f0f0f0;
            font-size: 24px;
            font-weight: bold;
        }
        
        .plate-table td.left {
            text-align: right;
        }
        
        .plate-table td.right {
            text-align: left;
        }
        
        .plate-bottom-row {
            font-size: 12px;
            color: #666;
        }
        
        .copyright {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #777;
            font-size: 14px;
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
            .input-container {
                flex-direction: column;
                align-items: center;
            }
            .count-group, button {
                margin-left: 0;
                margin-top: 10px;
            }
        }
        
        @media (max-width: 576px) {
            .plate-result-item {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>車牌號碼與質數的距離</h1>
        
        <div class="input-container">
            <div class="plate-input-group">
                <input type="text" id="part1" placeholder="前半部" maxlength="5">
                <span class="separator">-</span>
                <input type="text" id="part2" placeholder="後半部" maxlength="5">
            </div>
            
            <div class="count-group">
                <label for="count">顯示數量:</label>
                <input type="number" id="count" min="1" max="100" value="10">
            </div>
            
            <button id="search-button">查詢</button>
        </div>
        
        <div id="results" class="results"></div>
        
        <div class="copyright">
            <p>版權沒有，歡迎複製、改寫，期待更好的版本</p>
            <p>Yuktesha Zer @ 2025</p>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const part1Input = document.getElementById('part1');
            const part2Input = document.getElementById('part2');
            const countInput = document.getElementById('count');
            const searchButton = document.getElementById('search-button');
            const resultsDiv = document.getElementById('results');
            
            // 按下Enter鍵時觸發查詢
            [part1Input, part2Input, countInput].forEach(input => {
                input.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        searchButton.click();
                    }
                });
            });
            
            // 查詢按鈕點擊事件
            searchButton.addEventListener('click', function() {
                const part1 = part1Input.value.trim().toUpperCase();
                const part2 = part2Input.value.trim().toUpperCase();
                const count = parseInt(countInput.value) || 10;
                
                // 驗證輸入
                if (!isValidPlatePart(part1) || !isValidPlatePart(part2)) {
                    resultsDiv.innerHTML = '<div class="result-section"><h3>錯誤</h3><p>車牌號碼格式不正確，請確保前後半部各至少2個字元，最多5個字元。</p></div>';
                    return;
                }
                
                // 顯示載入中
                resultsDiv.innerHTML = '<div class="result-section"><h3>處理中...</h3><p>正在查詢最接近的質數，請稍候...</p></div>';
                
                // 使用表單數據
                const formData = new FormData();
                formData.append('part1', part1);
                formData.append('part2', part2);
                formData.append('count', count);
                
                // 發送查詢請求
                fetch('/search', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (!data.success) {
                        resultsDiv.innerHTML = `<div class="result-section"><h3>錯誤</h3><p>${data.error}</p></div>`;
                        return;
                    }
                    
                    displayResults(data);
                })
                .catch(error => {
                    console.error('Error:', error);
                    resultsDiv.innerHTML = `<div class="result-section"><h3>錯誤</h3><p>發生錯誤: ${error}</p></div>`;
                });
            });
            
            // 驗證車牌部分是否有效
            function isValidPlatePart(part) {
                return part && part.length >= 2 && part.length <= 5;
            }
            
            // 顯示結果
            function displayResults(data) {
                let html = '';
                
                // 顯示前後半部分結果
                html += `
                    <div class="result-section">
                        <h3>最接近的質數車牌</h3>
                `;
                
                if (data.part1.has_letters) {
                    html += `
                        <div class="result-info">
                            <p>前半部 (${data.part1.original}) 36進位轉換為10進位：${data.part1.base10}</p>
                        </div>
                    `;
                }
                
                if (data.part2.has_letters) {
                    html += `
                        <div class="result-info">
                            <p>後半部 (${data.part2.original}) 36進位轉換為10進位：${data.part2.base10}</p>
                        </div>
                    `;
                }
                
                html += `<div class="plate-results">`;
                
                // 整合前半部分和後半部分的結果
                for (let i = 0; i < Math.min(data.part1.closest_primes.length, data.part2.closest_primes.length); i++) {
                    const part1Item = data.part1.closest_primes[i];
                    const part2Item = data.part2.closest_primes[i];
                    
                    html += `
                        <div class="plate-result-item">
                            <table class="plate-table">
                                <tr class="plate-top-row">
                                    <td class="left">${part1Item.prime_base36}</td>
                                    <td>-</td>
                                    <td class="right">${part2Item.prime_base36}</td>
                                </tr>
                                <tr class="plate-bottom-row">
                                    <td>
                                        ${data.part1.has_letters ? `${part1Item.prime_base10}<br>` : ''}
                                        距離: ${part1Item.distance}
                                    </td>
                                    <td></td>
                                    <td>
                                        ${data.part2.has_letters ? `${part2Item.prime_base10}<br>` : ''}
                                        距離: ${part2Item.distance}
                                    </td>
                                </tr>
                            </table>
                        </div>
                    `;
                }
                
                html += `</div></div>`;
                
                // 顯示完整車牌結果
                html += `
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
                
                html += `<div class="plate-results">`;
                
                data.full.closest_primes.forEach(item => {
                    // 分割完整質數為前半部和後半部
                    const fullBase36 = item.prime_base36;
                    const part1Length = data.part1.original.length;
                    const part2Length = data.part2.original.length;
                    
                    let formattedPlate = '';
                    
                    // 確保正確分割並插入分隔符號
                    if (fullBase36.length <= part1Length) {
                        formattedPlate = fullBase36.padStart(part1Length, '0') + '-' + '0'.repeat(part2Length);
                    } else if (fullBase36.length <= part1Length + part2Length) {
                        const part1 = fullBase36.substring(0, Math.max(0, fullBase36.length - part2Length)).padStart(part1Length, '0');
                        const part2 = fullBase36.substring(Math.max(0, fullBase36.length - part2Length)).padStart(part2Length, '0');
                        formattedPlate = part1 + '-' + part2;
                    } else {
                        // 如果質數太長，只取最後的部分
                        const part1 = fullBase36.substring(0, part1Length);
                        const part2 = fullBase36.substring(part1Length, part1Length + part2Length);
                        formattedPlate = part1 + '-' + part2;
                    }
                    
                    html += `
                        <div class="plate-result-item">
                            <table class="plate-table">
                                <tr class="plate-top-row">
                                    <td>${formattedPlate}</td>
                                </tr>
                                <tr class="plate-bottom-row">
                                    <td>
                                        ${data.full.has_letters ? `${item.prime_base10}<br>` : ''}
                                        距離: ${item.distance}
                                    </td>
                                </tr>
                            </table>
                        </div>
                    `;
                });
                
                html += `</div></div>`;
                
                resultsDiv.innerHTML = html;
            }
        });
    </script>
</body>
</html>
''')

@app.route('/search', methods=['POST'])
def search():
    try:
        # 使用表單數據
        part1 = request.form.get('part1', '').strip().upper()
        part2 = request.form.get('part2', '').strip().upper()
        count = min(int(request.form.get('count', 10)), 100)
        
        logger.info(f"Search request: part1={part1}, part2={part2}, count={count}")
        
        # 驗證車牌部分
        if not (part1 and 2 <= len(part1) <= 5 and part2 and 2 <= len(part2) <= 5):
            return jsonify({
                'success': False,
                'error': '車牌號碼格式不正確，請確保前後半部各至少2個字元，最多5個字元。'
            })
        
        # 處理前半部
        part1_has_letters = contains_letters(part1)
        if part1_has_letters:
            part1_base10 = to_base10(part1)
        else:
            part1_base10 = int(part1)
        
        # 處理後半部
        part2_has_letters = contains_letters(part2)
        if part2_has_letters:
            part2_base10 = to_base10(part2)
        else:
            part2_base10 = int(part2)
        
        # 處理完整車牌
        full_plate = part1 + part2
        full_has_letters = contains_letters(full_plate)
        if full_has_letters:
            full_base10 = to_base10(full_plate)
        else:
            full_base10 = int(full_plate)
        
        logger.info(f"Converted values: part1={part1_base10}, part2={part2_base10}, full={full_base10}")
        
        # 找出最接近的質數
        part1_closest = find_closest_primes(part1_base10, count)
        part2_closest = find_closest_primes(part2_base10, count)
        full_closest = find_closest_primes(full_base10, count)
        
        logger.info(f"Found closest primes: part1={len(part1_closest)}, part2={len(part2_closest)}, full={len(full_closest)}")
        
        return jsonify({
            'success': True,
            'part1': {
                'original': part1,
                'has_letters': part1_has_letters,
                'base10': part1_base10,
                'closest_primes': part1_closest
            },
            'part2': {
                'original': part2,
                'has_letters': part2_has_letters,
                'base10': part2_base10,
                'closest_primes': part2_closest
            },
            'full': {
                'original': part1 + '-' + part2,  # 加入連字符號
                'has_letters': full_has_letters,
                'base10': full_base10,
                'closest_primes': full_closest
            }
        })
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({
            'success': False,
            'error': f'發生錯誤: {str(e)}'
        })

if __name__ == '__main__':
    logger.info("Starting 車牌號碼與質數的距離 v1.0.0")
    app.run(host='127.0.0.1', port=5002)
