import sqlite3
import math
import time
from typing import List, Optional

class PrimeGenerator:
    def __init__(self, db_path: str = 'primes.db'):
        """初始化質數生成器
        
        Args:
            db_path: SQLite 資料庫檔案路徑
        """
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """建立資料庫結構"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 建立質數表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS primes (
                    id INTEGER PRIMARY KEY,  -- 質數的序號（第幾個質數）
                    value INTEGER UNIQUE,    -- 質數值
                    created_at TIMESTAMP     -- 建立時間
                )
            ''')
            
            # 建立索引加速查詢
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_value ON primes(value)')
            
            # 建立狀態表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS status (
                    key TEXT PRIMARY KEY,
                    value INTEGER
                )
            ''')
            
            conn.commit()
    
    def is_prime(self, n: int) -> bool:
        """判斷一個數是否為質數"""
        if n < 2:
            return False
        for i in range(2, int(math.sqrt(n)) + 1):
            if n % i == 0:
                return False
        return True
    
    def get_max_prime(self) -> Optional[int]:
        """獲取資料庫中最大的質數"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM primes ORDER BY value DESC LIMIT 1')
            result = cursor.fetchone()
            return result[0] if result else None
    
    def get_prime_count(self) -> int:
        """獲取資料庫中質數的總數"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM primes')
            return cursor.fetchone()[0]
    
    def generate_primes(self, target_count: int, batch_size: int = 1000) -> None:
        """生成質數直到達到目標數量
        
        Args:
            target_count: 目標質數數量
            batch_size: 每次提交到資料庫的批次大小
        """
        current_count = self.get_prime_count()
        if current_count >= target_count:
            print(f'已有足夠的質數：{current_count} >= {target_count}')
            return
        
        print(f'開始生成質數，目前：{current_count}，目標：{target_count}')
        start_time = time.time()
        
        # 從最後一個質數開始繼續生成
        current_number = self.get_max_prime() or 1
        new_primes = []
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            while current_count < target_count:
                current_number += 1
                
                if self.is_prime(current_number):
                    current_count += 1
                    new_primes.append((current_count, current_number, time.time()))
                    
                    # 當累積足夠的質數時，批次插入資料庫
                    if len(new_primes) >= batch_size:
                        cursor.executemany(
                            'INSERT INTO primes (id, value, created_at) VALUES (?, ?, ?)',
                            new_primes
                        )
                        conn.commit()
                        new_primes = []
                        
                        # 顯示進度
                        elapsed = time.time() - start_time
                        print(f'進度：{current_count}/{target_count} ({current_count/target_count*100:.2f}%), '
                              f'耗時：{elapsed:.2f}秒')
            
            # 插入剩餘的質數
            if new_primes:
                cursor.executemany(
                    'INSERT INTO primes (id, value, created_at) VALUES (?, ?, ?)',
                    new_primes
                )
                conn.commit()
        
        total_time = time.time() - start_time
        print(f'完成！生成了 {target_count} 個質數，總耗時：{total_time:.2f}秒')
    
    def get_primes_range(self, start_id: int, end_id: int) -> List[int]:
        """獲取指定範圍的質數
        
        Args:
            start_id: 起始序號（從1開始）
            end_id: 結束序號
            
        Returns:
            指定範圍的質數列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT value FROM primes WHERE id BETWEEN ? AND ? ORDER BY id',
                (start_id, end_id)
            )
            return [row[0] for row in cursor.fetchall()]
    
    def get_prime_by_id(self, prime_id: int) -> Optional[int]:
        """根據序號獲取質數
        
        Args:
            prime_id: 質數序號（從1開始）
            
        Returns:
            對應的質數，如果不存在則返回 None
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM primes WHERE id = ?', (prime_id,))
            result = cursor.fetchone()
            return result[0] if result else None

if __name__ == '__main__':
    # 測試生成器
    generator = PrimeGenerator('primes.db')
    
    # 生成前100萬個質數
    target = 1_000_000
    generator.generate_primes(target)
    
    # 驗證結果
    total = generator.get_prime_count()
    max_prime = generator.get_max_prime()
    print(f'資料庫中共有 {total} 個質數')
    print(f'最大的質數是：{max_prime}')
