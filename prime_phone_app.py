import os
import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re
import logging
import math
import csv
from datetime import datetime
import shutil
import tempfile
import urllib.parse
import urllib.request

# 設定日誌
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename="prime_app_log.txt",
    filemode="w"
)
logger = logging.getLogger("PrimePhoneApp")

# 應用程式標題和版本
APP_TITLE = "我的手機號碼與質數的距離"
APP_VERSION = "1.0.0"

# 數據庫路徑
DEFAULT_DB_PATH = "D:\\WinSurf\\backend\\prime_phones.db"
FALLBACK_DB_PATHS = [
    "prime_phones.db",  # 應用程式所在目錄
    "backend/prime_phones.db",  # 相對路徑
    "https://raw.githubusercontent.com/Yuktesha/prime-phone-finder_tw/main/backend/prime_phones.db"  # GitHub 路徑
]

class PrimePhoneApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("800x600")
        self.root.minsize(600, 500)
        
        # 設置應用程式圖標（如果有的話）
        try:
            if os.path.exists("app_icon.ico"):
                self.root.iconbitmap("app_icon.ico")
        except Exception as e:
            logger.error(f"無法設置圖標: {e}")
        
        # 數據庫連接
        self.db_path = None
        self.conn = None
        self.temp_db_path = None  # 用於存儲臨時下載的數據庫文件
        
        # 搜尋結果
        self.search_results = []
        
        # 創建 UI 元素
        self.create_ui()
        
        # 嘗試自動連接數據庫
        self.auto_connect_db()
        
        # 當應用程式關閉時清理臨時文件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 標題
        title_label = ttk.Label(main_frame, text=APP_TITLE, font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 數據庫設置區域
        db_frame = ttk.LabelFrame(main_frame, text="數據庫設置", padding="10")
        db_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 數據庫路徑
        db_path_frame = ttk.Frame(db_frame)
        db_path_frame.pack(fill=tk.X)
        
        ttk.Label(db_path_frame, text="數據庫路徑:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.db_path_var = tk.StringVar(value=self.db_path if self.db_path else "")
        db_path_entry = ttk.Entry(db_path_frame, textvariable=self.db_path_var, width=50)
        db_path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        browse_btn = ttk.Button(db_path_frame, text="瀏覽...", command=self.browse_db)
        browse_btn.pack(side=tk.LEFT)
        
        connect_btn = ttk.Button(db_frame, text="連接數據庫", command=self.connect_to_db)
        connect_btn.pack(pady=(10, 0))
        
        # 查詢區域
        query_frame = ttk.LabelFrame(main_frame, text="查詢", padding="10")
        query_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # 查詢設置
        settings_frame = ttk.Frame(query_frame)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 手機號碼輸入
        phone_frame = ttk.Frame(settings_frame)
        phone_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(phone_frame, text="手機號碼:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.phone_var = tk.StringVar()
        phone_entry = ttk.Entry(phone_frame, textvariable=self.phone_var, width=20)
        phone_entry.pack(side=tk.LEFT, padx=(0, 10))
        # 綁定Enter鍵
        phone_entry.bind("<Return>", lambda event: self.search_prime())
        
        # 搜尋數量設置
        ttk.Label(phone_frame, text="搜尋數量:").pack(side=tk.LEFT, padx=(10, 10))
        
        self.count_var = tk.StringVar(value="5")
        count_spinbox = ttk.Spinbox(phone_frame, from_=1, to=100, textvariable=self.count_var, width=5)
        count_spinbox.pack(side=tk.LEFT, padx=(0, 10))
        # 綁定Enter鍵
        count_spinbox.bind("<Return>", lambda event: self.search_prime())
        
        # 搜尋按鈕
        search_btn = ttk.Button(phone_frame, text="查詢", command=self.search_prime)
        search_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # 結果操作按鈕框架
        actions_frame = ttk.Frame(query_frame)
        actions_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 複製按鈕
        copy_btn = ttk.Button(actions_frame, text="複製結果", command=self.copy_results)
        copy_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 導出 CSV 按鈕
        export_btn = ttk.Button(actions_frame, text="導出 CSV", command=self.export_csv)
        export_btn.pack(side=tk.LEFT)
        
        # 結果顯示區域
        result_frame = ttk.Frame(query_frame)
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        # 結果表格
        columns = ("number", "is_prime", "distance", "closest_prime")
        self.result_tree = ttk.Treeview(result_frame, columns=columns, show="headings")
        
        # 設置列標題
        self.result_tree.heading("number", text="號碼")
        self.result_tree.heading("is_prime", text="是否為質數")
        self.result_tree.heading("distance", text="與最近質數的距離")
        self.result_tree.heading("closest_prime", text="最接近的質數")
        
        # 設置列寬
        self.result_tree.column("number", width=150)
        self.result_tree.column("is_prime", width=100)
        self.result_tree.column("distance", width=150)
        self.result_tree.column("closest_prime", width=150)
        
        # 添加滾動條
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        self.result_tree.configure(yscroll=scrollbar.set)
        
        # 放置表格和滾動條
        self.result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 狀態欄
        self.status_var = tk.StringVar(value="就緒")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def browse_db(self):
        """瀏覽並選擇數據庫文件"""
        file_path = filedialog.askopenfilename(
            title="選擇數據庫文件",
            filetypes=[("SQLite 數據庫", "*.db"), ("所有文件", "*.*")]
        )
        if file_path:
            self.db_path_var.set(file_path)
            self.db_path = file_path
    
    def is_url(self, path):
        """檢查路徑是否為 URL"""
        return path.startswith(('http://', 'https://', 'ftp://'))
    
    def is_network_path(self, path):
        """檢查路徑是否為網路路徑"""
        return path.startswith('\\\\')
    
    def download_db(self, url):
        """從 URL 下載數據庫文件到臨時目錄"""
        try:
            # 創建臨時文件
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"prime_phone_db_{datetime.now().strftime('%Y%m%d%H%M%S')}.db")
            
            # 下載文件
            self.status_var.set(f"正在從 {url} 下載數據庫...")
            self.root.update()
            
            urllib.request.urlretrieve(url, temp_file)
            
            # 清理之前的臨時文件（如果有）
            if self.temp_db_path and os.path.exists(self.temp_db_path):
                try:
                    os.remove(self.temp_db_path)
                except:
                    pass
            
            self.temp_db_path = temp_file
            logger.info(f"數據庫已下載到臨時文件: {temp_file}")
            self.status_var.set(f"數據庫已下載")
            
            return temp_file
        except Exception as e:
            logger.error(f"下載數據庫時發生錯誤: {e}", exc_info=True)
            messagebox.showerror("錯誤", f"下載數據庫時發生錯誤: {str(e)}")
            return None
    
    def copy_network_db(self, network_path):
        """將網路路徑的數據庫複製到臨時目錄"""
        try:
            # 創建臨時文件
            temp_dir = tempfile.gettempdir()
            temp_file = os.path.join(temp_dir, f"prime_phone_db_{datetime.now().strftime('%Y%m%d%H%M%S')}.db")
            
            # 複製文件
            self.status_var.set(f"正在從 {network_path} 複製數據庫...")
            self.root.update()
            
            shutil.copy2(network_path, temp_file)
            
            # 清理之前的臨時文件（如果有）
            if self.temp_db_path and os.path.exists(self.temp_db_path):
                try:
                    os.remove(self.temp_db_path)
                except:
                    pass
            
            self.temp_db_path = temp_file
            logger.info(f"數據庫已複製到臨時文件: {temp_file}")
            self.status_var.set(f"數據庫已複製")
            
            return temp_file
        except Exception as e:
            logger.error(f"複製數據庫時發生錯誤: {e}", exc_info=True)
            messagebox.showerror("錯誤", f"複製數據庫時發生錯誤: {str(e)}")
            return None
    
    def auto_connect_db(self):
        """自動嘗試連接數據庫"""
        try:
            # 嘗試連接默認路徑
            if os.path.exists(DEFAULT_DB_PATH):
                logger.info(f"找到默認數據庫路徑: {DEFAULT_DB_PATH}")
                self.db_path_var.set(DEFAULT_DB_PATH)
                return self.connect_to_db()
            
            # 嘗試連接備用路徑
            for path in FALLBACK_DB_PATHS:
                if self.is_url(path):
                    logger.info(f"嘗試從URL下載數據庫: {path}")
                    local_path = self.download_db(path)
                    if local_path:
                        self.db_path_var.set(local_path)
                        return self.connect_to_db()
                elif os.path.exists(path):
                    logger.info(f"找到備用數據庫路徑: {path}")
                    self.db_path_var.set(path)
                    return self.connect_to_db()
            
            # 如果都找不到，提示用戶選擇數據庫文件
            messagebox.showinfo("提示", "找不到數據庫文件，請手動選擇數據庫文件")
            return self.browse_db()
        except Exception as e:
            logger.error(f"自動連接數據庫時發生錯誤: {e}", exc_info=True)
            messagebox.showerror("錯誤", f"自動連接數據庫時發生錯誤: {str(e)}")
            return False
    
    def check_db_structure(self):
        """檢查數據庫結構並創建必要的表"""
        try:
            cursor = self.conn.cursor()
            
            # 檢查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='primes'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                # 如果表不存在，提示用戶選擇正確的數據庫
                messagebox.showerror("錯誤", "所選數據庫不包含必要的表結構，請選擇正確的數據庫文件")
                logger.error("數據庫中不存在 primes 表")
                self.conn.close()
                self.conn = None
                return False
            else:
                # 檢查表結構
                cursor.execute("PRAGMA table_info(primes)")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                
                # 確保必要的列存在
                if "number" not in column_names or "is_prime" not in column_names:
                    logger.warning("primes 表缺少必要的列")
                    messagebox.showwarning("警告", "數據庫結構不完整，請選擇正確的數據庫文件")
                    self.conn.close()
                    self.conn = None
                    return False
            
            cursor.close()
            return True
        except Exception as e:
            logger.error(f"檢查數據庫結構時發生錯誤: {e}", exc_info=True)
            messagebox.showerror("錯誤", f"檢查數據庫結構時發生錯誤: {str(e)}")
            return False
    
    def connect_to_db(self):
        """連接到數據庫"""
        try:
            db_path = self.db_path_var.get()
            if not db_path:
                messagebox.showwarning("警告", "請先選擇數據庫文件")
                return False
            
            # 檢查是否為 URL
            if self.is_url(db_path):
                logger.info(f"檢測到 URL 路徑: {db_path}")
                db_path = self.download_db(db_path)
                if not db_path:
                    return False
            
            # 檢查是否為網路路徑
            elif self.is_network_path(db_path):
                logger.info(f"檢測到網路路徑: {db_path}")
                db_path = self.copy_network_db(db_path)
                if not db_path:
                    return False
            
            # 檢查文件是否存在
            if not os.path.exists(db_path):
                messagebox.showerror("錯誤", f"數據庫文件不存在: {db_path}")
                logger.error(f"數據庫文件不存在: {db_path}")
                self.status_var.set(f"錯誤: 數據庫文件不存在")
                return False
            
            # 關閉現有連接（如果有）
            if self.conn:
                self.conn.close()
            
            # 連接數據庫
            self.conn = sqlite3.connect(db_path)
            logger.info(f"成功連接到數據庫: {db_path}")
            
            # 檢查數據庫結構
            if not self.check_db_structure():
                return False
            
            self.status_var.set(f"已連接到數據庫: {os.path.basename(db_path)}")
            self.db_path = db_path
            return True
        except Exception as e:
            messagebox.showerror("錯誤", f"連接數據庫時發生錯誤: {str(e)}")
            logger.error(f"連接數據庫時發生錯誤: {e}", exc_info=True)
            self.status_var.set("數據庫連接失敗")
            return False
    
    def on_closing(self):
        """應用程式關閉時的清理工作"""
        try:
            # 關閉數據庫連接
            if self.conn:
                self.conn.close()
            
            # 刪除臨時文件
            if self.temp_db_path and os.path.exists(self.temp_db_path):
                try:
                    os.remove(self.temp_db_path)
                    logger.info(f"已刪除臨時數據庫文件: {self.temp_db_path}")
                except Exception as e:
                    logger.error(f"刪除臨時文件時發生錯誤: {e}")
        except Exception as e:
            logger.error(f"應用程式關閉時發生錯誤: {e}")
        
        # 關閉應用程式
        self.root.destroy()
    
    def is_prime(self, n):
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
    
    def find_closest_prime(self, number):
        """查找最接近的質數"""
        try:
            # 嘗試從數據庫查詢
            if self.conn:
                cursor = self.conn.cursor()
                
                # 假設數據庫中有一個名為 primes 的表，包含 number 和 is_prime 列
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                if tables:
                    table_name = tables[0][0]  # 使用第一個表
                    
                    # 檢查表結構
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = [col[1] for col in cursor.fetchall()]
                    
                    # 根據表結構構建查詢
                    if 'number' in columns and 'is_prime' in columns:
                        # 查詢這個數字是否為質數
                        cursor.execute(f"SELECT is_prime FROM {table_name} WHERE number = ?", (number,))
                        result = cursor.fetchone()
                        
                        is_prime_value = False
                        if result:
                            is_prime_value = bool(result[0])
                        else:
                            # 如果數據庫中沒有這個數字，手動計算
                            is_prime_value = self.is_prime(number)
                        
                        # 查找最接近的質數
                        if is_prime_value:
                            closest_prime = number
                            distance = 0
                        else:
                            # 在數據庫中查找最接近的質數
                            cursor.execute(f"""
                                SELECT number FROM {table_name} 
                                WHERE is_prime = 1 AND number > ? 
                                ORDER BY number ASC LIMIT 1
                            """, (number,))
                            higher_prime = cursor.fetchone()
                            
                            cursor.execute(f"""
                                SELECT number FROM {table_name} 
                                WHERE is_prime = 1 AND number < ? 
                                ORDER BY number DESC LIMIT 1
                            """, (number,))
                            lower_prime = cursor.fetchone()
                            
                            # 計算距離
                            higher_distance = higher_prime[0] - number if higher_prime else float('inf')
                            lower_distance = number - lower_prime[0] if lower_prime else float('inf')
                            
                            if higher_distance <= lower_distance:
                                closest_prime = higher_prime[0]
                                distance = higher_distance
                            else:
                                closest_prime = lower_prime[0]
                                distance = lower_distance
                        
                        return {
                            "number": number,
                            "is_prime": is_prime_value,
                            "distance": distance,
                            "closest_prime": closest_prime
                        }
            
            # 如果數據庫查詢失敗或沒有連接，使用算法計算
            return self.calculate_closest_prime(number)
        
        except Exception as e:
            logger.error(f"查詢最接近質數時發生錯誤: {e}", exc_info=True)
            # 出錯時使用算法計算
            return self.calculate_closest_prime(number)
    
    def calculate_closest_prime(self, number):
        """使用算法計算最接近的質數"""
        # 向下查找
        lower = number - 1
        while lower > 1 and not self.is_prime(lower):
            lower -= 1
        
        # 向上查找
        upper = number + 1
        while upper < 1000000000 and not self.is_prime(upper):
            upper += 1
        
        # 計算距離
        lower_distance = number - lower if lower > 1 else float('inf')
        upper_distance = upper - number if upper < 1000000000 else float('inf')
        
        # 返回最接近的質數
        if lower_distance <= upper_distance:
            return lower, lower_distance
        else:
            return upper, upper_distance
    
    def find_next_primes(self, start_number, count):
        """查找從給定數字開始的多個質數（數據庫方法）"""
        try:
            cursor = self.conn.cursor()
            
            # 查詢後續的質數
            cursor.execute(
                "SELECT number FROM primes WHERE number >= ? AND is_prime = 1 ORDER BY number LIMIT ?",
                (start_number, count)
            )
            
            primes = [row[0] for row in cursor.fetchall()]
            cursor.close()
            
            # 如果數據庫中找不到足夠的質數，使用算法補充
            if len(primes) < count:
                additional_count = count - len(primes)
                last_prime = primes[-1] if primes else start_number
                additional_primes = self.find_next_n_primes_algorithm(last_prime, additional_count)
                primes.extend(additional_primes)
            
            return primes
        except Exception as e:
            logger.error(f"查找後續質數時發生錯誤: {e}", exc_info=True)
            # 如果數據庫查詢失敗，使用算法
            return self.find_next_n_primes_algorithm(start_number, count)
    
    def find_next_n_primes_algorithm(self, start_number, count):
        """使用算法查找從給定數字開始的n個質數"""
        primes = []
        current = start_number
        
        # 如果起始數字不是質數，找到下一個質數
        if not self.is_prime(current):
            current += 1
            while not self.is_prime(current):
                current += 1
        
        # 找到起始質數後，繼續查找後續的質數
        while len(primes) < count:
            if self.is_prime(current):
                primes.append(current)
            current += 1
            # 避免無限循環
            if current > 1000000000:
                break
        
        return primes
    
    def search_prime(self):
        """搜尋質數手機號碼"""
        try:
            # 獲取輸入
            phone_number = self.phone_var.get().strip()
            
            # 檢查手機號碼格式
            if not phone_number:
                messagebox.showwarning("警告", "請輸入手機號碼")
                return
            
            # 移除前導的0（如果有）
            if phone_number.startswith("0"):
                phone_number_int = int(phone_number[1:])
            else:
                phone_number_int = int(phone_number)
            
            # 檢查是否為台灣手機號碼格式
            if not (900000000 <= phone_number_int <= 999999999):
                messagebox.showwarning("警告", "請輸入有效的台灣手機號碼 (09xxxxxxxx)")
                return
            
            # 獲取搜尋數量
            try:
                count = int(self.count_var.get())
                if count < 1:
                    count = 1
                elif count > 100:
                    count = 100
            except ValueError:
                count = 5
                self.count_var.set("5")
            
            # 檢查數據庫連接
            if not self.conn:
                if not self.auto_connect_db():
                    return
            
            # 清空結果表格
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)
            
            # 清空搜尋結果列表
            self.search_results = []
            
            # 更新狀態
            self.status_var.set(f"正在搜尋 {phone_number} 的質數...")
            self.root.update()
            
            # 查詢數據庫
            cursor = self.conn.cursor()
            
            # 檢查輸入的號碼是否為質數
            cursor.execute("SELECT is_prime FROM primes WHERE number = ?", (phone_number_int,))
            result = cursor.fetchone()
            
            is_prime = False
            if result:
                is_prime = bool(result[0])
            else:
                # 如果數據庫中沒有這個號碼的記錄，使用算法判斷
                is_prime = self.is_prime(phone_number_int)
            
            # 查詢最接近的質數
            closest_prime = None
            distance = None
            
            if is_prime:
                closest_prime = phone_number_int
                distance = 0
            else:
                # 查詢小於給定號碼的最大質數
                cursor.execute("SELECT MAX(number) FROM primes WHERE number < ? AND is_prime = 1", (phone_number_int,))
                result = cursor.fetchone()
                lower_prime = result[0] if result and result[0] is not None else None
                
                # 查詢大於給定號碼的最小質數
                cursor.execute("SELECT MIN(number) FROM primes WHERE number > ? AND is_prime = 1", (phone_number_int,))
                result = cursor.fetchone()
                upper_prime = result[0] if result and result[0] is not None else None
                
                # 計算距離
                if lower_prime is not None and upper_prime is not None:
                    lower_distance = phone_number_int - lower_prime
                    upper_distance = upper_prime - phone_number_int
                    
                    if lower_distance <= upper_distance:
                        closest_prime = lower_prime
                        distance = lower_distance
                    else:
                        closest_prime = upper_prime
                        distance = upper_distance
                elif lower_prime is not None:
                    closest_prime = lower_prime
                    distance = phone_number_int - lower_prime
                elif upper_prime is not None:
                    closest_prime = upper_prime
                    distance = upper_prime - phone_number_int
                else:
                    # 如果數據庫中沒有找到質數，使用算法尋找
                    closest_prime, distance = self.calculate_closest_prime(phone_number_int)
            
            # 添加原始號碼到結果
            original_result = {
                "number": phone_number_int,
                "is_prime": is_prime,
                "distance": distance if distance is not None else "N/A",
                "closest_prime": closest_prime if closest_prime is not None else "N/A"
            }
            self.search_results.append(original_result)
            
            # 添加到表格
            self.result_tree.insert("", "end", values=(
                f"0{phone_number_int}",
                "是" if is_prime else "否",
                distance if distance is not None else "N/A",
                f"0{closest_prime}" if closest_prime is not None else "N/A"
            ))
            
            # 查找後續的質數（不包括原始號碼）
            # 先確定起始點
            start_number = None
            if is_prime:
                # 如果輸入號碼是質數，從下一個數字開始查找
                start_number = phone_number_int + 1
            else:
                # 如果輸入號碼不是質數，從最接近的質數+1開始查找
                if closest_prime is not None:
                    if closest_prime < phone_number_int:
                        # 如果最接近的質數小於輸入號碼，從輸入號碼+1開始
                        start_number = phone_number_int + 1
                    else:
                        # 如果最接近的質數大於輸入號碼，從最接近質數+1開始
                        start_number = closest_prime + 1
                else:
                    # 如果沒有找到最接近的質數，從輸入號碼+1開始
                    start_number = phone_number_int + 1
            
            # 使用SQL查詢找到後續的質數
            next_primes = []
            if start_number is not None:
                # 查詢後續的質數
                cursor.execute(
                    "SELECT number FROM primes WHERE number >= ? AND is_prime = 1 ORDER BY number LIMIT ?",
                    (start_number, count)
                )
                db_results = cursor.fetchall()
                
                # 將結果轉換為整數列表
                next_primes = [row[0] for row in db_results]
                
                # 如果數據庫中找不到足夠的質數，使用算法補充
                if len(next_primes) < count:
                    # 從最後一個已知質數開始查找
                    last_prime = next_primes[-1] if next_primes else start_number
                    
                    # 使用算法找到剩餘的質數
                    current = last_prime + 1
                    while len(next_primes) < count and current < 1000000000:
                        if self.is_prime(current):
                            next_primes.append(current)
                        current += 1
            
            # 添加後續質數到結果
            for prime in next_primes:
                if prime != phone_number_int:  # 避免重複添加原始號碼
                    # 計算與原始號碼的距離
                    prime_distance = abs(prime - phone_number_int)
                    
                    result_item = {
                        "number": prime,
                        "is_prime": True,
                        "distance": prime_distance,
                        "closest_prime": prime
                    }
                    self.search_results.append(result_item)
                    
                    # 添加到表格
                    self.result_tree.insert("", "end", values=(
                        f"0{prime}",
                        "是",
                        prime_distance,
                        f"0{prime}"
                    ))
            
            # 更新狀態
            self.status_var.set(f"找到 {len(self.search_results)} 個結果")
            
            cursor.close()
        except Exception as e:
            messagebox.showerror("錯誤", f"搜尋時發生錯誤: {str(e)}")
            logger.error(f"搜尋時發生錯誤: {e}", exc_info=True)
            self.status_var.set("搜尋失敗")
    
    def copy_results(self):
        """將結果複製到剪貼簿"""
        if not self.search_results:
            messagebox.showinfo("提示", "沒有可複製的結果")
            return
        
        try:
            # 構建要複製的文本
            result_text = "號碼\t是否為質數\t與最近質數的距離\t最接近的質數\n"
            
            for result in self.search_results:
                result_text += f"0{result['number']}\t"
                result_text += "是" if result['is_prime'] else "否"
                result_text += f"\t{result['distance']}\t"
                
                if result['closest_prime'] != "N/A":
                    result_text += f"0{result['closest_prime']}\n"
                else:
                    result_text += "N/A\n"
            
            # 複製到剪貼簿
            self.root.clipboard_clear()
            self.root.clipboard_append(result_text)
            
            # 更新狀態
            self.status_var.set("結果已複製到剪貼簿")
            logger.info("結果已複製到剪貼簿")
        except Exception as e:
            messagebox.showerror("錯誤", f"複製結果時發生錯誤: {str(e)}")
            logger.error(f"複製結果時發生錯誤: {e}", exc_info=True)
    
    def export_csv(self):
        """將結果導出為 CSV 文件"""
        if not self.search_results:
            messagebox.showinfo("提示", "沒有可導出的結果")
            return
        
        try:
            # 選擇保存位置
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            default_filename = f"prime_phone_results_{timestamp}.csv"
            
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV 文件", "*.csv"), ("所有文件", "*.*")],
                initialfile=default_filename
            )
            
            if not file_path:
                return
            
            # 寫入 CSV 文件
            with open(file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = ['號碼', '是否為質數', '與最近質數的距離', '最接近的質數']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in self.search_results:
                    writer.writerow({
                        '號碼': f"0{result['number']}",
                        '是否為質數': "是" if result['is_prime'] else "否",
                        '與最近質數的距離': result['distance'],
                        '最接近的質數': f"0{result['closest_prime']}" if result['closest_prime'] != "N/A" else "N/A"
                    })
            
            # 更新狀態
            self.status_var.set(f"結果已導出到 {file_path}")
            logger.info(f"結果已導出到 {file_path}")
            
            # 詢問是否打開文件
            if messagebox.askyesno("導出成功", f"結果已導出到 {file_path}\n是否打開文件？"):
                os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("錯誤", f"導出結果時發生錯誤: {str(e)}")
            logger.error(f"導出結果時發生錯誤: {e}", exc_info=True)

def main():
    """主函數"""
    try:
        # 創建主窗口
        root = tk.Tk()
        app = PrimePhoneApp(root)
        
        # 設置樣式
        style = ttk.Style()
        style.theme_use('clam')  # 使用 clam 主題，在 Windows 上看起來更現代
        
        # 啟動應用程式
        root.mainloop()
    except Exception as e:
        logger.error(f"應用程式啟動失敗: {e}", exc_info=True)
        messagebox.showerror("錯誤", f"應用程式啟動失敗: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
