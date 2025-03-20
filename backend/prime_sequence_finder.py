import sqlite3
from typing import List, Dict, Set, Optional, Tuple
import time
from collections import defaultdict

class PrimeSequenceFinder:
    def __init__(self, db_path: str = 'primes.db'):
        """初始化質數序列搜索器
        
        Args:
            db_path: SQLite 資料庫路徑
        """
        self.db_path = db_path
        self._cache = {}  # 緩存查詢結果
    
    def get_primes_range(self, start_id: int, end_id: int) -> List[int]:
        """從資料庫獲取指定範圍的質數"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT value FROM primes WHERE id BETWEEN ? AND ? ORDER BY id',
                (start_id, end_id)
            )
            return [row[0] for row in cursor.fetchall()]
    
    def find_prime_with_n_sequences(self, n: int, min_length: int = 2, max_length: int = 100,
                                  batch_size: int = 1000) -> Optional[Tuple[int, List[List[int]]]]:
        """找出第一個具有恰好 N 種不同連續質數和的質數
        
        Args:
            n: 需要的連續質數和的數量
            min_length: 最小序列長度
            max_length: 最大序列長度
            batch_size: 每次從資料庫讀取的質數數量
            
        Returns:
            (目標質數, 其所有連續質數序列) 的元組，如果找不到則返回 None
        """
        print(f'搜尋具有 {n} 種連續質數和的質數...')
        start_time = time.time()
        
        # 獲取資料庫中質數的總數
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM primes')
            total_primes = cursor.fetchone()[0]
        
        # 用於追蹤已經檢查過的和
        checked_sums = set()
        # 用於存儲每個和的序列數量
        sum_sequences = defaultdict(list)
        
        # 分批處理質數
        for batch_start in range(1, total_primes, batch_size):
            batch_end = min(batch_start + batch_size, total_primes)
            primes = self.get_primes_range(batch_start, batch_end)
            
            # 對每個可能的序列長度
            for length in range(min_length, min(max_length + 1, len(primes) + 1)):
                # 計算第一個窗口的和
                window_sum = sum(primes[:length])
                
                # 檢查每個窗口
                for i in range(len(primes) - length + 1):
                    if i > 0:
                        # 更新窗口和：減去移出的數，加上移入的數
                        window_sum = window_sum - primes[i - 1] + primes[i + length - 1]
                    
                    # 如果這個和是質數且還沒檢查過
                    if window_sum not in checked_sums:
                        checked_sums.add(window_sum)
                        
                        # 檢查這個和是否在資料庫中
                        with sqlite3.connect(self.db_path) as conn:
                            cursor = conn.cursor()
                            cursor.execute('SELECT 1 FROM primes WHERE value = ?', (window_sum,))
                            if cursor.fetchone():
                                # 找到一個新的質數和
                                sequence = primes[i:i + length]
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
            
            # 顯示進度
            progress = (batch_end / total_primes) * 100
            elapsed = time.time() - start_time
            print(f'進度：{progress:.2f}%, 已處理 {batch_end} 個質數, 用時：{elapsed:.2f}秒')
        
        return None
    
    def analyze_prime_sequences(self, prime: int) -> Dict[int, List[List[int]]]:
        """分析一個質數可以被分解為哪些連續質數和
        
        Args:
            prime: 要分析的質數
            
        Returns:
            一個字典，鍵是序列長度，值是該長度的所有可能序列
        """
        # 檢查這個數是否在資料庫中
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM primes WHERE value = ?', (prime,))
            if not cursor.fetchone():
                raise ValueError(f'{prime} 不是質數或超出資料庫範圍')
        
        # 用緩存加速重複查詢
        cache_key = f'analyze_{prime}'
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        sequences_by_length = defaultdict(list)
        checked_sequences = set()
        
        # 獲取所有小於目標數的質數
        cursor.execute('SELECT value FROM primes WHERE value < ? ORDER BY value', (prime,))
        smaller_primes = [row[0] for row in cursor.fetchall()]
        
        # 對每個可能的起始位置
        for start in range(len(smaller_primes)):
            current_sum = 0
            sequence = []
            
            # 從起始位置開始累加
            for p in smaller_primes[start:]:
                current_sum += p
                sequence.append(p)
                
                # 如果和等於目標數，且這個序列還沒記錄過
                sequence_key = tuple(sequence)
                if current_sum == prime and sequence_key not in checked_sequences:
                    checked_sequences.add(sequence_key)
                    sequences_by_length[len(sequence)].append(list(sequence))
                
                # 如果和已經超過目標數，換下一個起始位置
                if current_sum > prime:
                    break
        
        # 儲存到緩存
        self._cache[cache_key] = dict(sequences_by_length)
        return self._cache[cache_key]

if __name__ == '__main__':
    # 測試搜索器
    finder = PrimeSequenceFinder('primes.db')
    
    # 找出第一個具有正好 5 種不同連續質數和的質數
    result = finder.find_prime_with_n_sequences(5, min_length=2, max_length=5)
    
    if result:
        prime, sequences = result
        print(f'\n質數 {prime} 可以表示為以下 {len(sequences)} 種連續質數和：')
        for seq in sequences:
            print(f'{" + ".join(map(str, seq))} = {prime}')
