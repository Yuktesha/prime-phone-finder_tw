import tkinter as tk
from tkinter import ttk
import math

def is_prime(n):
    """判斷一個數是否為質數"""
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def find_prime_sums(limit, min_length=1, max_length=None):
    """找出所有小於limit的連續質數相加為質數的組合"""
    primes = [n for n in range(2, limit) if is_prime(n)]
    results = []
    
    for start in range(len(primes)):
        current_sum = 0
        for end in range(start, len(primes)):
            current_sum += primes[end]
            if current_sum >= limit:
                break
            length = end - start + 1
            if length < min_length:
                continue
            if max_length and length > max_length:
                break
            if is_prime(current_sum):
                results.append((primes[start:end+1], current_sum))
    
    return results

class PrimeSumApp:
    def __init__(self, root):
        self.root = root
        self.root.title("質數連加計算器")
        
        # 設定主視窗最小大小
        self.root.minsize(400, 300)
        
        # 配置主grid以支援自動調整大小
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 創建輸入框架
        input_frame = ttk.LabelFrame(root, text="設定", padding="5")
        input_frame.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        # 配置input_frame的列自動調整
        input_frame.grid_columnconfigure(1, weight=1)
        
        # 上限設定
        ttk.Label(input_frame, text="搜尋範圍上限:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.limit_var = tk.StringVar(value="100")
        ttk.Entry(input_frame, textvariable=self.limit_var).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 組合長度設定
        ttk.Label(input_frame, text="最小組合長度:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.min_length_var = tk.StringVar(value="1")
        ttk.Entry(input_frame, textvariable=self.min_length_var).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        ttk.Label(input_frame, text="最大組合長度:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.max_length_var = tk.StringVar(value="")
        ttk.Entry(input_frame, textvariable=self.max_length_var).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # 計算按鈕
        ttk.Button(input_frame, text="計算", command=self.calculate).grid(row=3, column=0, columnspan=2, pady=10)
        
        # 結果顯示區域
        result_frame = ttk.LabelFrame(root, text="結果", padding="5")
        result_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        # 配置result_frame的行和列自動調整
        result_frame.grid_rowconfigure(1, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        
        # 字體大小調整區域
        font_frame = ttk.Frame(result_frame)
        font_frame.grid(row=0, column=0, columnspan=2, pady=(0, 5), sticky="ew")
        
        ttk.Label(font_frame, text="字體大小:").pack(side="left", padx=5)
        self.font_size = 12
        ttk.Button(font_frame, text="-", command=self.decrease_font).pack(side="left", padx=2)
        ttk.Button(font_frame, text="+", command=self.increase_font).pack(side="left", padx=2)
        
        # 結果文字區域
        self.result_text = tk.Text(result_frame, width=50, height=20, font=("TkDefaultFont", self.font_size))
        self.result_text.grid(row=1, column=0, sticky="nsew")
        
        # 捲軸
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.result_text.configure(yscrollcommand=scrollbar.set)
        
        # 分頁控制區域
        page_frame = ttk.Frame(result_frame)
        page_frame.grid(row=2, column=0, columnspan=2, pady=5, sticky="ew")
        
        self.current_page = 1
        self.items_per_page = 20
        self.all_results = []
        
        ttk.Button(page_frame, text="上一頁", command=self.prev_page).pack(side="left", padx=5)
        self.page_label = ttk.Label(page_frame, text="第 1 頁")
        self.page_label.pack(side="left", padx=5)
        ttk.Button(page_frame, text="下一頁", command=self.next_page).pack(side="left", padx=5)
        
        # 統計資訊區域
        self.stats_var = tk.StringVar()
        ttk.Label(result_frame, textvariable=self.stats_var).grid(row=3, column=0, columnspan=2, pady=5)
    
    def increase_font(self):
        self.font_size = min(32, self.font_size + 2)
        self.result_text.configure(font=("TkDefaultFont", self.font_size))
    
    def decrease_font(self):
        self.font_size = max(8, self.font_size - 2)
        self.result_text.configure(font=("TkDefaultFont", self.font_size))
    
    def display_page(self):
        start_idx = (self.current_page - 1) * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = self.all_results[start_idx:end_idx]
        
        self.result_text.delete(1.0, tk.END)
        for primes, prime_sum in page_items:
            self.result_text.insert(tk.END, f"{' + '.join(map(str, primes))} = {prime_sum}\n")
        
        total_pages = math.ceil(len(self.all_results) / self.items_per_page)
        self.page_label.config(text=f"第 {self.current_page} 頁 / 共 {total_pages} 頁")
    
    def next_page(self):
        total_pages = math.ceil(len(self.all_results) / self.items_per_page)
        if self.current_page < total_pages:
            self.current_page += 1
            self.display_page()
    
    def prev_page(self):
        if self.current_page > 1:
            self.current_page -= 1
            self.display_page()
        
    def calculate(self):
        try:
            limit = int(self.limit_var.get())
            min_length = int(self.min_length_var.get())
            max_length = int(self.max_length_var.get()) if self.max_length_var.get() else None
            
            self.all_results = find_prime_sums(limit, min_length, max_length)
            self.current_page = 1
            
            # 顯示結果
            self.display_page()
            
            # 更新統計資訊
            max_length_found = max(len(primes) for primes, _ in self.all_results) if self.all_results else 0
            self.stats_var.set(
                f"統計資訊：共找到 {len(self.all_results)} 組組合，最長組合長度：{max_length_found}"
            )
            
        except ValueError as e:
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "請輸入有效的數字！")
            self.stats_var.set("")

def main():
    root = tk.Tk()
    app = PrimeSumApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
