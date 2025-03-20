from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import re
import os

app = Flask(__name__)
CORS(app)

DB_PATH = os.path.join(os.path.dirname(__file__), 'prime_phones.db')

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

@app.route('/api/find_closest_prime')
def find_closest_prime():
    """尋找最接近輸入號碼的質數手機號碼"""
    try:
        # 獲取輸入的號碼並清理
        number_str = request.args.get('number', '')
        cleaned_number = re.sub(r'\D', '', number_str)  # 移除所有非數字字符
        
        # 獲取需要返回的質數數量
        count = request.args.get('count', '1')
        try:
            count = int(count)
            if count < 1 or count > 100:
                return jsonify({'error': '請輸入1-100之間的數量'}), 400
        except ValueError:
            return jsonify({'error': '數量必須是數字'}), 400
        
        # 檢查是否是有效的台灣手機號碼
        if not cleaned_number or not cleaned_number.startswith('09') or len(cleaned_number) != 10:
            return jsonify({'error': '請輸入有效的台灣手機號碼（09開頭，共10位數字）'}), 400
            
        number = int(cleaned_number)
        
        # 檢查輸入的號碼是否已經是質數
        is_input_prime = is_prime(number)
        
        # 尋找最接近的質數
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 查詢比輸入號碼大的質數
        cursor.execute(
            'SELECT number FROM prime_phones WHERE number >= ? ORDER BY number ASC LIMIT ?',
            (number, count)
        )
        larger_primes = [row[0] for row in cursor.fetchall()]
        
        # 查詢比輸入號碼小的質數
        cursor.execute(
            'SELECT number FROM prime_phones WHERE number <= ? ORDER BY number DESC LIMIT ?',
            (number, count)
        )
        smaller_primes = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        
        # 合併並按照與輸入號碼的距離排序
        all_primes = []
        
        # 如果輸入的號碼是質數，先添加它
        if is_input_prime:
            all_primes.append({
                'prime_number': str(number),
                'difference': 0,
                'direction': 'equal',
                'is_input_prime': True
            })
        
        # 添加較大的質數
        for prime in larger_primes:
            if prime != number:  # 避免重複添加輸入的質數
                all_primes.append({
                    'prime_number': str(prime),
                    'difference': prime - number,
                    'direction': 'larger'
                })
        
        # 添加較小的質數
        for prime in smaller_primes:
            if prime != number:  # 避免重複添加輸入的質數
                all_primes.append({
                    'prime_number': str(prime),
                    'difference': number - prime,
                    'direction': 'smaller'
                })
        
        # 按照差距排序
        all_primes.sort(key=lambda x: x['difference'])
        
        # 限制返回的數量
        result_primes = all_primes[:count]
        
        if not result_primes:
            return jsonify({'error': '未找到最接近的質數'}), 404
            
        return jsonify({
            'primes': result_primes,
            'count': len(result_primes)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/find_prime_phones')
def find_prime_phones():
    """查詢指定前綴的質數手機號碼"""
    try:
        prefix = request.args.get('prefix', '')
        if not prefix.isdigit() or len(prefix) != 2:
            return jsonify({'error': '前綴必須是 2 位數字'}), 400
            
        # 完整的前綴是 "09" + 輸入的兩位數，但資料庫中存儲的是 "9" + 兩位數 + "0" 格式
        full_prefix = '9' + prefix + '0'
            
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 使用 LIKE 查詢，以便找到所有以指定前綴開頭的號碼
        cursor.execute(
            'SELECT number FROM prime_phones WHERE prefix LIKE ? ORDER BY number LIMIT 1000',
            (full_prefix[:3] + '%',)
        )
        
        numbers = [str(row[0]) for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'prime_phones': numbers,
            'count': len(numbers)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/list_prime_phone_prefixes')
def list_prime_phone_prefixes():
    """列出所有可用的前綴及其數量"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 從前綴中提取後兩位數字
        cursor.execute('''
            SELECT SUBSTR(prefix, 2, 2) as short_prefix, COUNT(*) as count 
            FROM prime_phones 
            GROUP BY short_prefix 
            ORDER BY count DESC
        ''')
        
        # 將資料庫中的前綴格式轉換為顯示格式 (XX)
        prefixes = [{'prefix': row[0], 'count': row[1]} for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'data': {
                'prefixes': prefixes
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 獲取環境變量或使用默認值
    host = os.environ.get('HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'True').lower() == 'true'
    
    # 啟動 Flask 應用
    app.run(host=host, port=port, debug=debug)
