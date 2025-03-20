import sqlite3
from typing import List, Dict, Set, Optional, Tuple
import time
from collections import defaultdict
import numpy as np

class PrimeSequenceFinder:
    def __init__(self, db_path: str = 'primes.db'):
        self.db_path = db_path
        self._load_primes()
        self.sum_to_sequences = defaultdict(list)
    
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
    
    def precompute_sums(self, max_length: int = 5):
        """預先計算所有可能的連續質數和"""
        print("預先計算所有可能的連續質數和...")
        start_time = time.time()
        
        # 使用 NumPy 的累加和加速計算
        cumsum = np.cumsum(self.primes)
        
        # 對每個可能的序列長度
        for length in range(2, max_length + 1):
            print(f"處理長度為 {length} 的序列...")
            seq_start = time.time()
            
            # 計算所有可能的窗口和
            for i in range(len(self.primes) - length + 1):
                if i == 0:
                    window_sum = cumsum[length-1]
                else:
                    window_sum = cumsum[i+length-1] - cumsum[i-1]
                
                # 如果和太大，就不用繼續了
                if window_sum > self.primes[-1]:
                    break
                
                sequence = self.primes[i:i+length].tolist()
                self.sum_to_sequences[window_sum].append(sequence)
            
            seq_elapsed = time.time() - seq_start
            print(f"完成長度 {length} 的序列，用時：{seq_elapsed:.2f}秒")
        
        total_sums = len(self.sum_to_sequences)
        elapsed = time.time() - start_time
        print(f"預計算完成，共 {total_sums:,} 個不同的和，用時：{elapsed:.2f}秒")
    
    def find_prime_with_n_sequences(self, n: int, min_length: int = 2, max_length: int = 5) -> Optional[Tuple[int, List[List[int]]]]:
        """找出第一個具有恰好 N 種不同連續質數和的質數"""
        print(f'搜尋具有 {n} 種連續質數和的質數...')
        start_time = time.time()
        
        # 預先計算所有可能的和
        self.precompute_sums(max_length)
        
        # 只需要檢查在和的集合中的質數
        candidates = sorted(set(self.sum_to_sequences.keys()) & self.prime_set)
        print(f"找到 {len(candidates):,} 個候選質數")
        
        # 檢查每個候選質數
        for i, prime in enumerate(candidates):
            sequences = self.sum_to_sequences[prime]
            valid_sequences = [seq for seq in sequences if min_length <= len(seq) <= max_length]
            
            if len(valid_sequences) == n:
                elapsed = time.time() - start_time
                print(f'找到目標質數：{prime}')
                print(f'用時：{elapsed:.2f}秒')
                return prime, valid_sequences
            
            if (i + 1) % 1000 == 0:
                elapsed = time.time() - start_time
                print(f'已檢查 {i+1:,} 個候選質數，當前：{prime}，用時：{elapsed:.2f}秒')
        
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
