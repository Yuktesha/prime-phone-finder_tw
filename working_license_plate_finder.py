import os
import sqlite3
import logging
from flask import Flask, render_template_string, request, jsonify

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('LicensePlatePrimeFinder')

app = Flask(__name__)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'primes.db')

def get_db_connection():
    """連接到質數資料庫"""
    try:
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
        return []
    
    try:
        cursor = conn.cursor()
        
        # 找出小於目標數字的最大質數
        cursor.execute("SELECT prime FROM primes WHERE prime <= ? ORDER BY prime DESC LIMIT ?", (number, count))
        lower_primes = cursor.fetchall()
        
        # 找出大於目標數字的最小質數
        cursor.execute("SELECT prime FROM primes WHERE prime >= ? ORDER BY prime LIMIT ?", (number, count))
        higher_primes = cursor.fetchall()
        
        # 合併結果並計算距離
        results = []
        for row in lower_primes:
            prime = row['prime']
            distance = number - prime
            results.append({
                'prime_base10': prime,
                'prime_base36': to_base36(prime),
                'distance': distance
            })
        
        for row in higher_primes:
            prime = row['prime']
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
    <title>我的車牌號碼與質數的距離</title>
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
            font-size: 28px;
        }
        
        .input-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .plate-input-group {
            display: flex;
            align-items: center;
            margin-right: 20px;
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
            transition: border-color 0.3s;
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
        
        .plate-results {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            justify-content: flex-start;
        }
        
        .plate-result-item {
            width: calc(20% - 16px);
            margin-bottom: 20px;
            background-color: white;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .plate-result-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
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
        
        .plate-bottom-row {
            font-size: 12px;
            color: #666;
        }
        
        .action-buttons {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-top: 15px;
        }
        
        .action-button {
            background-color: #2ecc71;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background-color 0.3s;
        }
        
        .action-button:hover {
            background-color: #27ae60;
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
            .input-container {
                flex-direction: column;
                align-items: center;
            }
            .plate-input-group {
                margin-right: 0;
                margin-bottom: 15px;
            }
            .count-group {
                margin-left: 0;
                margin-top: 15px;
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
            h1 {
                font-size: 22px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>我的車牌號碼與質數的距離</h1>
        
        <div class="input-container">
            <div class="plate-input-group">
                <input type="text" id="part1" placeholder="前半部" maxlength="5" required>
                <span class="separator">-</span>
                <input type="text" id="part2" placeholder="後半部" maxlength="5" required>
            </div>
            
            <div class="count-group">
                <label for="count">顯示數量:</label>
                <input type="number" id="count" min="1" max="256" value="10">
            </div>
            
            <button type="button" id="search-button">查詢</button>
        </div>
        
        <div id="results" class="results"></div>
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
                    resultsDiv.innerHTML = '<div class="result-section"><h3>錯誤</h3><p>沒有這種車牌呢～</p></div>';
                    return;
                }
                
                // 顯示載入中
                resultsDiv.innerHTML = '<div class="result-section"><h3>處理中...</h3><p>正在查詢最接近的質數，請稍候...</p></div>';
                
                // 使用表單數據而非JSON
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
                
                // 整合前半部分和後半部分的結果，但只顯示指定數量的配對
                for (let i = 0; i < Math.min(data.part1.closest_primes.length, data.part2.closest_primes.length); i++) {
                    const part1Item = data.part1.closest_primes[i];
                    const part2Item = data.part2.closest_primes[i];
                    
                    html += `
                        <div class="plate-result-item">
                            <table class="plate-table">
                                <tr class="plate-top-row">
                                    <td>${part1Item.prime_base36}</td>
                                    <td>-</td>
                                    <td>${part2Item.prime_base36}</td>
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
                
                html += `</div>`;
                
                // 添加複製到剪貼簿和導出為CSV的按鈕
                html += `
                    <div class="action-buttons">
                        <button class="action-button" id="copy-parts-button">複製到剪貼簿</button>
                        <button class="action-button" id="export-parts-csv">導出為CSV</button>
                    </div>
                </div>`;
                
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
                            <table class="plate-table">
                                <tr class="plate-top-row">
                                    <td>${part1Prime}</td>
                                    <td>-</td>
                                    <td>${part2Prime}</td>
                                </tr>
                                <tr class="plate-bottom-row">
                                    <td colspan="3">
                                        ${data.full.has_letters ? `${item.prime_base10}<br>` : ''}
                                        距離: ${item.distance}
                                    </td>
                                </tr>
                            </table>
                        </div>
                    `;
                });
                
                html += `</div>`;
                
                // 添加複製到剪貼簿和導出為CSV的按鈕
                html += `
                    <div class="action-buttons">
                        <button class="action-button" id="copy-full-button">複製到剪貼簿</button>
                        <button class="action-button" id="export-full-csv">導出為CSV</button>
                    </div>
                </div>`;
                
                resultsDiv.innerHTML = html;
                
                // 設置複製到剪貼簿功能
                document.getElementById('copy-parts-button').addEventListener('click', function() {
                    copyToClipboard(formatPartsDataForClipboard(data));
                });
                
                document.getElementById('copy-full-button').addEventListener('click', function() {
                    copyToClipboard(formatFullDataForClipboard(data));
                });
                
                // 設置導出為CSV功能
                document.getElementById('export-parts-csv').addEventListener('click', function() {
                    exportCSV(formatPartsDataForCSV(data), `車牌部分_${data.part1.original}-${data.part2.original}.csv`);
                });
                
                document.getElementById('export-full-csv').addEventListener('click', function() {
                    exportCSV(formatFullDataForCSV(data), `完整車牌_${data.full.original}.csv`);
                });
            }
            
            // 複製到剪貼簿
            function copyToClipboard(text) {
                const textarea = document.createElement('textarea');
                textarea.value = text;
                document.body.appendChild(textarea);
                textarea.select();
                document.execCommand('copy');
                document.body.removeChild(textarea);
                alert('已複製到剪貼簿！');
            }
            
            // 導出為CSV
            function exportCSV(csvContent, filename) {
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                const url = URL.createObjectURL(blob);
                link.setAttribute('href', url);
                link.setAttribute('download', filename);
                link.style.visibility = 'hidden';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }
            
            // 格式化前後部分數據為剪貼簿格式
            function formatPartsDataForClipboard(data) {
                let result = `前半部: ${data.part1.original}, 後半部: ${data.part2.original}\n\n`;
                result += "前半部\t後半部\t前半部距離\t後半部距離\n";
                
                for (let i = 0; i < Math.min(data.part1.closest_primes.length, data.part2.closest_primes.length); i++) {
                    const part1 = data.part1.closest_primes[i];
                    const part2 = data.part2.closest_primes[i];
                    result += `${part1.prime_base36}\t${part2.prime_base36}\t${part1.distance}\t${part2.distance}\n`;
                }
                
                return result;
            }
            
            // 格式化完整車牌數據為剪貼簿格式
            function formatFullDataForClipboard(data) {
                let result = `完整車牌: ${data.full.original}\n\n`;
                result += "質數\t距離\n";
                
                data.full.closest_primes.forEach(item => {
                    result += `${item.prime_base36}\t${item.distance}\n`;
                });
                
                return result;
            }
            
            // 格式化前後部分數據為CSV格式
            function formatPartsDataForCSV(data) {
                let result = `前半部,${data.part1.original},後半部,${data.part2.original}\n`;
                result += "前半部,後半部,前半部距離,後半部距離\n";
                
                for (let i = 0; i < Math.min(data.part1.closest_primes.length, data.part2.closest_primes.length); i++) {
                    const part1 = data.part1.closest_primes[i];
                    const part2 = data.part2.closest_primes[i];
                    result += `${part1.prime_base36},${part2.prime_base36},${part1.distance},${part2.distance}\n`;
                }
                
                return result;
            }
            
            // 格式化完整車牌數據為CSV格式
            function formatFullDataForCSV(data) {
                let result = `完整車牌,${data.full.original}\n`;
                result += "質數,距離\n";
                
                data.full.closest_primes.forEach(item => {
                    result += `${item.prime_base36},${item.distance}\n`;
                });
                
                return result;
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
        count = min(int(request.form.get('count', 10)), 256)
        
        # 驗證車牌部分
        if not (part1 and 2 <= len(part1) <= 5 and part2 and 2 <= len(part2) <= 5):
            return jsonify({
                'success': False,
                'error': '沒有這種車牌呢～'
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
        
        # 找出最接近的質數
        part1_closest = find_closest_primes(part1_base10, count)
        part2_closest = find_closest_primes(part2_base10, count)
        full_closest = find_closest_primes(full_base10, count)
        
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
                'original': full_plate,
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
    logger.info("Starting 我的車牌號碼與質數的距離 v1.0.0")
    app.run(host='127.0.0.1', port=5002)
