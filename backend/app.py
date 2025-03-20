from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import time
import math
import numpy as np
import json
import os

app = Flask(__name__)
CORS(app)

# 資料庫配置
PRIME_DB = 'primes.db'
PHONE_DB = 'prime_phones.db'

# 全局變量：儲存所有質數
ALL_PRIMES = []
PRIME_SET = set()

def init_databases():
    """初始化所有數據庫"""
    # 初始化質數手機號碼數據庫
    conn = sqlite3.connect(PHONE_DB)
    cursor = conn.cursor()
    
    # 只在表格不存在時創建
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS prime_phones (
        phone_number TEXT PRIMARY KEY
    )
    ''')
    
    conn.commit()
    conn.close()
    
    # 初始化質數數據庫
    conn = sqlite3.connect(PRIME_DB)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS primes (
        value INTEGER PRIMARY KEY
    )
    ''')
    
    # 檢查是否需要生成初始質數
    cursor.execute('SELECT COUNT(*) FROM primes')
    count = cursor.fetchone()[0]
    
    if count == 0:
        # 生成初始質數
        values = []
        for n in range(2, 1000001):
            if all(n % i != 0 for i in range(2, int(math.sqrt(n)) + 1)):
                values.append((n,))
        
        # 批量插入
        cursor.executemany('INSERT INTO primes (value) VALUES (?)', values)
        conn.commit()
    
    conn.close()

def load_primes(limit=1000000):
    """從數據庫載入質數到記憶體"""
    global ALL_PRIMES, PRIME_SET
    
    conn = sqlite3.connect(PRIME_DB)
    cursor = conn.cursor()
    
    # 載入所有小於等於 limit 的質數
    cursor.execute('SELECT value FROM primes WHERE value <= ? ORDER BY value', (limit,))
    ALL_PRIMES = [row[0] for row in cursor.fetchall()]
    PRIME_SET = set(ALL_PRIMES)
    
    conn.close()
    
    print(f'已載入 {len(ALL_PRIMES)} 個質數')

def is_prime(n):
    """判斷一個數是否為質數"""
    if n < 2:
        return False
    if n in PRIME_SET:
        return True
    if n <= ALL_PRIMES[-1]:
        return False
        
    # 對於超出預先計算範圍的數字，使用試除法
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def find_prime_sequences(prime, min_length, max_length):
    """找出所有可以組成目標質數的連續質數序列"""
    sequences = []
    max_length = float('inf') if max_length == -1 else max_length
    
    # 只考慮小於目標數的質數，並按照升序排序
    smaller_primes = sorted([p for p in ALL_PRIMES if p < prime])
    if not smaller_primes:
        return []
    
    # 使用滑動窗口尋找連續質數序列
    for start_idx in range(len(smaller_primes)):
        current_sum = smaller_primes[start_idx]
        current_sequence = [smaller_primes[start_idx]]
        
        # 向後擴展窗口
        for next_idx in range(start_idx + 1, len(smaller_primes)):
            # 檢查是否為連續質數（差值為 2 或更小）
            if smaller_primes[next_idx] - smaller_primes[next_idx - 1] > 2:
                break
                
            current_sequence.append(smaller_primes[next_idx])
            current_sum += smaller_primes[next_idx]
            
            # 檢查序列長度和總和
            if len(current_sequence) >= min_length:
                if current_sum == prime:
                    if len(current_sequence) <= max_length:
                        sequences.append(current_sequence[:])
                elif current_sum > prime:
                    break
    
    return sequences

def find_primes_with_sequences(start=2, end=100, min_sequences=1, max_sequences=-1, min_length=2, max_length=5):
    """找出具有特定數量連續質數和的質數"""
    try:
        # 參數驗證
        if start < 2:
            raise ValueError('起始值必須大於等於 2')
        if end > 100000:
            raise ValueError('結束值不能超過 100,000')
        if end < start:
            raise ValueError('結束值必須大於起始值')
        if min_length < 2:
            raise ValueError('最小序列長度必須大於等於 2')
        if max_length != -1 and max_length < min_length:
            raise ValueError('最大序列長度必須大於等於最小序列長度（或為 -1 表示無限制）')
        if min_sequences < 1:
            raise ValueError('最小序列數量必須大於等於 1')
        if max_sequences != -1 and max_sequences < min_sequences:
            raise ValueError('最大序列數量必須大於等於最小序列數量（或為 -1 表示無限制）')

        # 在範圍內搜索質數
        primes_in_range = [p for p in ALL_PRIMES if start <= p <= end]
        results = []
        start_time = time.time()
        
        for prime in primes_in_range:
            sequences = find_prime_sequences(prime, min_length, max_length)
            if sequences:
                seq_count = len(sequences)
                if (max_sequences == -1 or seq_count <= max_sequences) and seq_count >= min_sequences:
                    results.append({
                        'prime': prime,
                        'sequences': sequences
                    })

        total_time = time.time() - start_time
        return {
            'results': results,
            'total_time': total_time,
            'total_primes': len(results)
        }

    except Exception as e:
        raise ValueError(f'搜索質數時發生錯誤：{str(e)}')

def generate_prime_phones(prefix):
    """生成質數手機號碼"""
    try:
        # 驗證前綴
        if not prefix.isdigit() or len(prefix) != 2:
            raise ValueError('前綴必須是 2 位數字')
            
        # 完整的前綴應該是 "09" + 輸入的兩位數
        full_prefix = '09' + prefix
            
        # 連接數據庫
        conn = sqlite3.connect(PHONE_DB)
        cursor = conn.cursor()
        
        # 檢查是否已經生成過
        cursor.execute('SELECT phone_number FROM prime_phones WHERE phone_number LIKE ?', (full_prefix + '%',))
        existing = cursor.fetchall()
        
        if existing:
            # 返回已存在的號碼
            prime_phones = [row[0] for row in existing]
            conn.close()
            return prime_phones
            
        # 生成新的號碼
        prime_phones = []
        for i in range(10000000):  # 0000000 到 9999999
            number = f"{full_prefix}{i:07d}"  # 補零到 7 位
            if is_prime(int(number)):
                prime_phones.append(number)
                
        # 儲存到數據庫
        cursor.executemany(
            'INSERT INTO prime_phones (phone_number) VALUES (?)',
            [(phone,) for phone in prime_phones]
        )
        conn.commit()
        conn.close()
        
        return prime_phones
        
    except Exception as e:
        raise ValueError(f'生成質數手機號碼時發生錯誤：{str(e)}')

@app.route('/api/find_primes_with_sequences')
def find_primes_with_sequences_route():
    """API路由：找出具有特定數量連續和的質數"""
    try:
        start = int(request.args.get('start', 2))
        end = int(request.args.get('end', 100))
        min_sequences = int(request.args.get('min_sequences', 1))
        max_sequences = int(request.args.get('max_sequences', -1))
        min_length = int(request.args.get('min_length', 2))
        max_length = int(request.args.get('max_length', 5))
        
        result = find_primes_with_sequences(
            start, end, min_sequences, max_sequences,
            min_length, max_length
        )
        
        return jsonify(result)
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'未預期的錯誤：{str(e)}'}), 500

@app.route('/api/find_prime_phones')
def find_prime_phones_route():
    """API路由：生成質數手機號碼"""
    try:
        prefix = request.args.get('prefix', '')
        prime_phones = generate_prime_phones(prefix)
        return jsonify({'prime_phones': prime_phones})
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'未預期的錯誤：{str(e)}'}), 500

@app.route('/api/list_prime_phone_prefixes')
def list_prime_phone_prefixes_route():
    """API路由：列出所有可用的前綴"""
    try:
        conn = sqlite3.connect(PHONE_DB)
        cursor = conn.cursor()
        
        # 查詢所有已存在的前綴
        cursor.execute('''
            SELECT DISTINCT substr(phone_number, 1, 4) as prefix
            FROM prime_phones
            GROUP BY prefix
            ORDER BY prefix ASC
        ''')
        
        prefixes = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        # 如果數據庫為空，生成一些初始前綴
        if not prefixes:
            valid_prefixes = []
            for i in range(100):  # 00-99
                prefix = f"09{i:02d}"
                # 生成一個測試號碼
                test_number = prefix + "0000000"
                if is_prime(int(test_number)):
                    valid_prefixes.append(prefix)
            return jsonify({'prefixes': valid_prefixes})
        
        return jsonify({'prefixes': prefixes})
        
    except Exception as e:
        return jsonify({'error': f'獲取前綴列表失敗：{str(e)}'}), 500

# 設定 CORS
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# 啟動時初始化數據庫
init_databases()

# 啟動時載入質數到記憶體
load_primes(limit=1000000)

if __name__ == '__main__':
    app.run(debug=True)
