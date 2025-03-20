import sqlite3
import math
import os
from tqdm import tqdm

def is_prime(n):
    """判斷一個數是否為質數"""
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def init_phone_db():
    """初始化手機號碼資料庫"""
    # 刪除舊的資料庫文件（如果存在）
    if os.path.exists('prime_phones.db'):
        os.remove('prime_phones.db')
    
    conn = sqlite3.connect('prime_phones.db')
    cursor = conn.cursor()
    
    # 創建資料表，包含完整號碼和前綴
    cursor.execute('''
    CREATE TABLE prime_phones (
        number INTEGER PRIMARY KEY,
        prefix TEXT NOT NULL
    )
    ''')
    
    # 建立前綴索引以加速查詢
    cursor.execute('CREATE INDEX idx_prefix ON prime_phones(prefix)')
    
    conn.commit()
    return conn, cursor

def generate_prime_phones():
    """生成所有可能的質數手機號碼"""
    conn, cursor = init_phone_db()
    
    try:
        # 檢查是否已有資料
        cursor.execute('SELECT COUNT(*) FROM prime_phones')
        if cursor.fetchone()[0] > 0:
            print('資料庫已存在資料，跳過生成步驟')
            return
        
        start = 900000000
        end = 999999999
        batch_size = 1000
        current_batch = []
        
        print('開始生成質數手機號碼...')
        for n in tqdm(range(start, end + 1)):
            if is_prime(n):
                prefix = str(n)[:4]  # 取前4位數字作為前綴
                current_batch.append((n, prefix))
                
                if len(current_batch) >= batch_size:
                    cursor.executemany(
                        'INSERT OR IGNORE INTO prime_phones (number, prefix) VALUES (?, ?)',
                        current_batch
                    )
                    conn.commit()
                    current_batch = []
        
        # 處理最後一批
        if current_batch:
            cursor.executemany(
                'INSERT OR IGNORE INTO prime_phones (number, prefix) VALUES (?, ?)',
                current_batch
            )
            conn.commit()
        
        print('完成！')
        
        # 顯示統計資訊
        cursor.execute('SELECT COUNT(*) FROM prime_phones')
        total = cursor.fetchone()[0]
        print(f'總共找到 {total} 個質數手機號碼')
        
        cursor.execute('SELECT prefix, COUNT(*) FROM prime_phones GROUP BY prefix')
        print('\n各前綴的數量：')
        for prefix, count in cursor.fetchall():
            print(f'{prefix}: {count}')
            
    finally:
        conn.close()

if __name__ == '__main__':
    generate_prime_phones()
