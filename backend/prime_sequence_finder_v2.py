import sqlite3
from typing import List, Dict, Set, Optional, Tuple
import time
from collections import defaultdict
import numpy as np

class PrimeSequenceFinder:
    def __init__(self, db_path: str = 'primes.db'):
        self.db_path = db_path
        self._prime_cache = {}
        self._sum_cache = {}
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
    
    def find_prime_with_n_sequences(self, n: int, min_length: int = 2, max_length: int = 5) -> Optional[Tuple[int, List[List[int]]]]:
        """找出第一個具有恰好 N 種不同連續質數和的質數"""
        print(f'搜尋具有 {n} 種連續質數和的質數...')
        start_time = time.time()
        
        # 使用字典記錄每個和的所有序列
        sum_sequences = defaultdict(list)
        
        # 對每個可能的長度
        for length in range(min_length, max_length + 1):
            print(f"檢查長度為 {length} 的序列...")
            seq_start_time = time.time()
            
            # 使用 NumPy 的累加和計算所有可能的窗口和
            cumsum = np.cumsum(self.primes)
            for i in range(len(self.primes) - length + 1):
                if i == 0:
                    window_sum = cumsum[length-1]
                else:
                    window_sum = cumsum[i+length-1] - cumsum[i-1]
                
                # 只檢查質數表中的數
                if window_sum in self.prime_set:
                    sequence = self.primes[i:i+length].tolist()
                    sum_sequences[window_sum].append(sequence)
                    
                    # 如果找到具有正好 n 種序列的質數
                    if len(sum_sequences[window_sum]) == n:
                        elapsed = time.time() - start_time
                        print(f'找到目標質數：{window_sum}')
                        print(f'用時：{elapsed:.2f}秒')
                        return window_sum, sum_sequences[window_sum]
                    elif len(sum_sequences[window_sum]) > n:
                        # 如果序列數超過 n，就不是我們要找的
                        sum_sequences.pop(window_sum)
                
                # 每處理 100萬個組合就顯示進度
                if (i + 1) % 1000000 == 0:
                    elapsed = time.time() - seq_start_time
                    print(f'長度 {length}: 已檢查 {i+1:,} 個組合，用時：{elapsed:.2f}秒')
            
            seq_elapsed = time.time() - seq_start_time
            print(f'完成長度 {length} 的檢查，用時：{seq_elapsed:.2f}秒')
        
        return None
    
    def analyze_prime(self, prime: int, max_length: int = 5) -> Dict[int, List[List[int]]]:
        """分析一個質數可以被分解為哪些連續質數和"""
        if prime not in self.prime_set:
            raise ValueError(f'{prime} 不是質數或超出資料庫範圍')
        
        sequences_by_length = defaultdict(list)
        
        # 使用 NumPy 的累加和優化搜索
        cumsum = np.cumsum(self.primes)
        
        # 對每個可能的長度
        for length in range(2, max_length + 1):
            # 使用向量化操作找出所有可能的序列
            for i in range(len(self.primes) - length + 1):
                if i == 0:
                    window_sum = cumsum[length-1]
                else:
                    window_sum = cumsum[i+length-1] - cumsum[i-1]
                
                if window_sum == prime:
                    sequences_by_length[length].append(self.primes[i:i+length].tolist())
                elif window_sum > prime:
                    break
        
        return dict(sequences_by_length)

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
