import sqlite3
from typing import List, Optional
import time
import random
from functools import lru_cache

class PrimePhoneGenerator:
    def __init__(self, db_path: str = 'prime_phones.db'):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """建立資料庫結構"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 建立質數表，包含前綴分類
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prime_phones (
                    value INTEGER PRIMARY KEY,
                    prefix TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            # 建立前綴索引
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_prefix ON prime_phones(prefix)')
            conn.commit()
    
    def _miller_rabin_pass(self, a: int, s: int, d: int, n: int) -> bool:
        """執行一次 Miller-Rabin 測試"""
        a_to_power = pow(a, d, n)
        if a_to_power == 1:
            return True
        for _ in range(s - 1):
            if a_to_power == n - 1:
                return True
            a_to_power = (a_to_power * a_to_power) % n
        return a_to_power == n - 1
    
    @lru_cache(maxsize=1024)
    def is_prime(self, n: int) -> bool:
        """使用 Miller-Rabin 質數測試"""
        if n < 2:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        
        # 計算 n - 1 = 2^s * d
        s = 0
        d = n - 1
        while d % 2 == 0:
            s += 1
            d //= 2
        
        # 對大數使用更多的測試輪次
        witnesses = [2, 3, 5, 7, 11, 13, 17] if n < 1_000_000_000 else \
                   [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
        
        return all(self._miller_rabin_pass(w, s, d, n) for w in witnesses)
    
    def generate_prime_phones(self, prefix: str = "09", progress_interval: int = 10000):
        """生成指定前綴的質數手機號碼"""
        print(f"開始生成 {prefix} 開頭的質數手機號碼...")
        start_time = time.time()
        
        # 計算範圍
        prefix_len = len(prefix)
        remaining_digits = 10 - prefix_len  # 手機號碼總長度為 10
        start_num = int(prefix + "0" * remaining_digits)
        end_num = int(prefix + "9" * remaining_digits)
        
        found_primes = []
        total_checked = 0
        current = start_num + (1 - (start_num % 2))  # 確保從奇數開始
        
        # 使用批次處理來提高效率
        batch = []
        batch_size = 1000
        
        while current <= end_num:
            if self.is_prime(current):
                batch.append((current, prefix))
                
                if len(batch) >= batch_size:
                    # 批量插入資料庫
                    with sqlite3.connect(self.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.executemany(
                            'INSERT OR IGNORE INTO prime_phones (value, prefix) VALUES (?, ?)',
                            batch
                        )
                        conn.commit()
                    found_primes.extend(batch)
                    batch = []
            
            total_checked += 1
            if total_checked % progress_interval == 0:
                elapsed = time.time() - start_time
                progress = (current - start_num) / (end_num - start_num) * 100
                print(f"進度：{progress:.1f}%，已檢查：{total_checked:,} 個數字，"
                      f"找到：{len(found_primes):,} 個質數，用時：{elapsed:.1f}秒")
            
            current += 2  # 只檢查奇數
        
        # 處理最後的批次
        if batch:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(
                    'INSERT OR IGNORE INTO prime_phones (value, prefix) VALUES (?, ?)',
                    batch
                )
                conn.commit()
            found_primes.extend(batch)
        
        total_elapsed = time.time() - start_time
        print(f"完成！共檢查 {total_checked:,} 個數字，找到 {len(found_primes):,} 個質數，"
              f"總用時：{total_elapsed:.1f}秒")
        return len(found_primes)
    
    def get_prime_phones(self, prefix: str = "09", limit: int = 10) -> List[int]:
        """獲取指定前綴的質數手機號碼"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT value 
                FROM prime_phones 
                WHERE prefix = ? 
                ORDER BY value
                LIMIT ?
            ''', (prefix, limit))
            return [row[0] for row in cursor.fetchall()]

if __name__ == '__main__':
    # 測試生成器
    generator = PrimePhoneGenerator()
    
    # 測試一些常見的前綴
    test_prefixes = ['0900', '0910', '0920', '0930', '0960']
    for prefix in test_prefixes:
        count = generator.generate_prime_phones(prefix)
        print(f"\n前綴 {prefix} 完成，找到 {count} 個質數")
        
        # 顯示找到的質數
        phones = generator.get_prime_phones(prefix)
        if phones:
            print(f"\n{prefix} 開頭的質數手機號碼（前5個）：")
            for phone in phones[:5]:
                print(phone)
            print()
