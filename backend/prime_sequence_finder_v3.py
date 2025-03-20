import sqlite3
from typing import List, Dict, Set, Optional, Tuple
import time
from collections import defaultdict
import numpy as np

class PrimeSequenceFinder:
    def __init__(self, db_path: str = 'primes.db'):
        self.db_path = db_path
        self._load_primes()
    
    def _load_primes(self):
        """將所有質數載入記憶體"""
        print("載入質數到記憶體...")
        start_time = time.time()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM primes ORDER BY value')
            self.primes = np.array([row[0] for row in cursor.fetchall()])
            self.prime_set = set(self.primes)
        print(f"載入完成，共 {len(self.primes)} 個質數，用時：{time.time() - start_time:.2f}秒")
    
    def find_sequences_for_prime(self, target: int, min_length: int = 2, max_length: int = 5) -> List[List[int]]:
        """找出一個質數的所有連續質數和序列"""
        sequences = []
        
        # 只考慮小於目標數的質數
        smaller_primes = self.primes[self.primes < target]
        
        # 使用累加和加速計算
        cumsum = np.cumsum(smaller_primes)
        
        # 對每個可能的序列長度
        for length in range(min_length, max_length + 1):
            # 使用滑動窗口計算連續和
            for i in range(len(smaller_primes) - length + 1):
                if i == 0:
                    window_sum = cumsum[length-1]
                else:
                    window_sum = cumsum[i+length-1] - cumsum[i-1]
                
                if window_sum == target:
                    sequences.append(smaller_primes[i:i+length].tolist())
                elif window_sum > target:
                    break  # 如果和已經超過目標，可以跳過剩餘的窗口
        
        return sequences
    
    def find_prime_with_n_sequences(self, n: int, min_length: int = 2, max_length: int = 5,
                                  start_from: int = 0) -> Optional[Tuple[int, List[List[int]]]]:
        """找出第一個具有恰好 N 種不同連續質數和的質數"""
        print(f'搜尋具有 {n} 種連續質數和的質數...')
        start_time = time.time()
        total_checked = 0
        
        # 從質數表中逐個檢查
        for i, prime in enumerate(self.primes[start_from:], start=start_from):
            sequences = self.find_sequences_for_prime(prime, min_length, max_length)
            
            if len(sequences) == n:
                elapsed = time.time() - start_time
                print(f'找到目標質數：{prime}')
                print(f'用時：{elapsed:.2f}秒')
                return prime, sequences
            
            total_checked += 1
            if total_checked % 1000 == 0:
                elapsed = time.time() - start_time
                print(f'已檢查到 {prime}，共 {total_checked:,} 個質數，用時：{elapsed:.2f}秒')
        
        return None

if __name__ == '__main__':
    # 測試搜索器
    finder = PrimeSequenceFinder('primes.db')
    
    # 使用前10萬個質數
    finder.primes = finder.primes[:100000]
    finder.prime_set = set(finder.primes)
    
    print(f"搜索範圍：2 到 {finder.primes[-1]}")
    
    # 找出第一個具有正好 3 種不同連續質數和的質數
    result = finder.find_prime_with_n_sequences(3, min_length=2, max_length=5)
    
    if result:
        prime, sequences = result
        print(f'\n質數 {prime} 可以表示為以下 {len(sequences)} 種連續質數和：')
        for seq in sequences:
            print(f'{" + ".join(map(str, seq))} = {prime}')
