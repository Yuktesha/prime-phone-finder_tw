from flask import Blueprint, jsonify, request
import sqlite3
import time
from typing import List, Dict, Tuple, Optional
import numpy as np
import bisect

class PrimeAPI:
    def __init__(self):
        """初始化質數 API"""
        self._blueprint = Blueprint('prime_api', __name__)
        self.primes = []
        self.prime_set = set()  # 用於快速查找
        self.prime_sums_cache = {}  # 快取常用的序列和
        self.phone_db = 'prime_phones.db'
        self._generate_primes(1000000)
        self._setup_phone_database()

    def _generate_primes(self, n: int):
        """生成質數"""
        print("生成質數...")
        start_time = time.time()
        
        self.primes = []
        sieve = [True] * (n + 1)
        sieve[0:2] = [False, False]
        
        for current_prime in range(2, int(n ** 0.5) + 1):
            if sieve[current_prime]:
                sieve[current_prime*2::current_prime] = [False] * len(sieve[current_prime*2::current_prime])
        
        self.primes = [num for num, is_prime in enumerate(sieve) if is_prime]
        self.prime_set = set(self.primes)
        
        print(f"生成完成，共 {len(self.primes)} 個質數，用時：{time.time() - start_time:.2f}秒")

    def _setup_phone_database(self):
        """初始化手機號碼數據庫"""
        conn = sqlite3.connect(self.phone_db)
        cursor = conn.cursor()
        
        # 創建表格（如果不存在）
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS prime_phones (
            number TEXT PRIMARY KEY,
            prefix TEXT NOT NULL
        )
        ''')
        
        # 創建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prefix ON prime_phones(prefix)')
        
        conn.commit()
        conn.close()

    def is_prime(self, n: int) -> bool:
        """判斷一個數是否為質數"""
        if n < 2:
            return False
        if n in self.prime_set:
            return True
            
        # 使用 Miller-Rabin 質數測試
        def miller_rabin_test(n: int, k: int = 5) -> bool:
            if n == 2 or n == 3:
                return True
            if n < 2 or n % 2 == 0:
                return False

            # 將 n - 1 寫成 2^r * d 的形式
            r, d = 0, n - 1
            while d % 2 == 0:
                r += 1
                d //= 2

            # 進行 k 次測試
            for _ in range(k):
                a = np.random.randint(2, n - 1)
                x = pow(a, d, n)
                if x == 1 or x == n - 1:
                    continue
                for _ in range(r - 1):
                    x = (x * x) % n
                    if x == n - 1:
                        break
                else:
                    return False
            return True

        return miller_rabin_test(n)

    def find_prime_sequences(self, prime, min_length, max_length):
        """找出所有可以組成目標質數的質數序列"""
        sequences = []
        cache_key = (prime, min_length, max_length)
        
        # 檢查快取
        if cache_key in self.prime_sums_cache:
            return self.prime_sums_cache[cache_key]
        
        # 找到第一個可能的起始位置
        max_idx = bisect.bisect_right(self.primes, prime)
        min_prime = self.primes[0]
        
        # 對每個可能的序列長度進行檢查
        for length in range(min_length, max_length + 1 if max_length > 0 else min_length * 2):
            # 如果最小的質數乘以長度已經超過目標，可以提前結束
            if min_prime * length > prime:
                break
                
            # 找到這個長度下最大可能的起始位置
            max_start = bisect.bisect_right(self.primes, prime // length)
            
            # 從每個可能的起始位置開始檢查
            for start_idx in range(max_start):
                if self.primes[start_idx] * length > prime:
                    break
                    
                current_sum = 0
                sequence = []
                
                # 檢查從這個位置開始的序列
                for j in range(start_idx, min(start_idx + length, max_idx)):
                    current_sum += self.primes[j]
                    sequence.append(self.primes[j])
                    
                    # 如果和已經超過目標，提前結束
                    if current_sum > prime:
                        break
                        
                    # 如果找到符合條件的序列
                    if current_sum == prime and len(sequence) >= min_length:
                        sequences.append([int(x) for x in sequence])
        
        # 儲存到快取
        self.prime_sums_cache[cache_key] = sequences
        return sequences

    def estimate_search_time(self, start, end, min_sequences, max_sequences, min_length, max_length):
        """預估搜索時間"""
        # 先用小範圍做基準測試
        sample_size = 1000
        sample_start = start
        sample_end = min(start + sample_size, end)
        
        sample_start_time = time.time()
        sample_results = self.find_primes_with_sequences(
            sample_start, sample_end,
            min_sequences, max_sequences,
            min_length, max_length
        )
        sample_time = time.time() - sample_start_time
        
        # 計算預估時間
        total_range = end - start
        estimated_time = (total_range / sample_size) * sample_time
        
        return {
            'sample_time': sample_time,
            'sample_size': sample_size,
            'estimated_time': estimated_time,
            'sample_results': len(sample_results['results'])
        }

    def find_primes_with_sequences(
        self,
        start: int = 2,
        end: int = 100,
        min_sequences: int = 1,
        max_sequences: int = -1,
        min_length: int = 2,
        max_length: int = 100
    ) -> List[Dict]:
        """找出具有特定數量連續和的質數"""
        # 如果搜索範圍大於 10000，先進行時間預估
        if end - start > 10000:
            estimate = self.estimate_search_time(
                start, min(start + 1000, end),
                min_sequences, max_sequences,
                min_length, max_length
            )
            total_range = end - start
            estimated_total_time = (total_range / estimate['sample_size']) * estimate['sample_time']
            
            if estimated_total_time > 30:  # 如果預估時間超過 30 秒
                return {
                    'error': f'預估搜索時間為 {estimated_total_time:.1f} 秒，建議縮小搜索範圍。\n' +
                            f'參考：搜索 {estimate["sample_size"]} 個數字用了 {estimate["sample_time"]:.3f} 秒，' +
                            f'找到 {estimate["sample_results"]} 個結果。'
                }
        
        start_time = time.time()
        
        # 參數驗證
        if start < 2:
            return {'error': '起始值必須大於等於 2'}
        if end > 100000:
            return {'error': '結束值不能超過 100,000'}
        if end < start:
            return {'error': '結束值必須大於起始值'}
        if min_length < 2:
            return {'error': '最小序列長度必須大於等於 2'}
        if max_length > 0 and max_length < min_length:
            return {'error': '最大序列長度必須大於等於最小序列長度'}
        
        # 使用二分搜索找到範圍內的質數
        start_pos = bisect.bisect_left(self.primes, start)
        end_pos = bisect.bisect_right(self.primes, end)
        target_primes = self.primes[start_pos:end_pos]
        
        # 根據搜索範圍大小決定分段大小
        segment_size = 1000 if end - start > 10000 else len(target_primes)
        segments = [target_primes[i:i + segment_size] for i in range(0, len(target_primes), segment_size)]
        
        results = []
        total_segments = len(segments)
        processed_count = 0
        last_progress_time = time.time()
        
        for segment_idx, segment in enumerate(segments):
            segment_start_time = time.time()
            segment_results = []
            
            for prime in segment:
                sequences = self.find_prime_sequences(prime, min_length, max_length)
                if min_sequences <= len(sequences) and (max_sequences == -1 or len(sequences) <= max_sequences):
                    segment_results.append({
                        'prime': int(prime),
                        'sequences': sequences,
                        'length': len(sequences)
                    })
                    processed_count += 1
            
            results.extend(segment_results)
            
            # 每秒最多更新一次進度
            current_time = time.time()
            if current_time - last_progress_time >= 1.0:
                elapsed_time = current_time - start_time
                progress = (segment_idx + 1) / total_segments
                estimated_total = elapsed_time / progress if progress > 0 else 0
                remaining_time = estimated_total - elapsed_time
                
                print(f"Progress: {progress:.1%}, Found {processed_count} results, " +
                      f"Elapsed: {elapsed_time:.1f}s, Remaining: {remaining_time:.1f}s")
                last_progress_time = current_time
        
        total_time = time.time() - start_time
        return {
            'results': results,
            'total_time': total_time,
            'total_segments': total_segments,
            'processed_segments': total_segments,
            'total_results': len(results)
        }

    def generate_prime_phones(self, prefix: str) -> List[str]:
        """生成指定前綴的質數手機號碼"""
        if not prefix or len(prefix) != 4 or not prefix.isdigit():
            raise ValueError('前綴必須是4位數字')

        conn = sqlite3.connect(self.phone_db)
        cursor = conn.cursor()
        
        # 檢查是否已經生成過
        cursor.execute('SELECT number FROM prime_phones WHERE prefix = ?', (prefix,))
        existing = cursor.fetchall()
        
        if existing:
            numbers = [row[0] for row in existing]
            conn.close()
            return sorted(numbers)
        
        # 生成新的質數手機號碼
        numbers = []
        base = int(prefix) * 1000000  # 將前綴轉換為基數
        
        # 測試所有可能的後綴
        for i in range(1000000):
            number = base + i
            if len(str(number)) == 10 and self.is_prime(number):  # 確保是10位數
                numbers.append(str(number))
        
        # 儲存到數據庫
        cursor.executemany(
            'INSERT OR IGNORE INTO prime_phones (number, prefix) VALUES (?, ?)',
            [(num, prefix) for num in numbers]
        )
        
        conn.commit()
        conn.close()
        
        return sorted(numbers)

    def list_prime_phone_prefixes(self) -> Dict[str, int]:
        """列出所有已生成的質數手機號碼前綴及其數量"""
        conn = sqlite3.connect(self.phone_db)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT prefix, COUNT(*) as count
        FROM prime_phones
        GROUP BY prefix
        ORDER BY count DESC, prefix
        ''')
        
        prefixes = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        return prefixes

    @property
    def blueprint(self):
        """獲取 Flask Blueprint"""
        return self._blueprint

    @blueprint.setter
    def blueprint(self, value):
        """設置 Flask Blueprint"""
        self._blueprint = value
