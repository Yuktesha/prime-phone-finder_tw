import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font as tkfont
import math
import csv
from io import StringIO
import re

def is_prime(n):
    """判斷一個數是否為質數"""
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def find_prime_sums(limit, min_length=1, max_length=None, start=2):
    """找出所有小於limit的連續質數相加為質數的組合"""
    if max_length is None:
        max_length = limit
    
    # 生成質數列表
    primes = []
    for n in range(2, limit + 1):
        if is_prime(n):
            primes.append(n)
    
    results = []
    prime_sums_dict = {}  # 用於記錄每個質數的所有連續質數序列
    
    # 對於每個可能的起始位置
    for i in range(len(primes)):
        sum_so_far = 0
        # 從起始位置開始累加
        for j in range(i, len(primes)):
            sum_so_far += primes[j]
            # 如果和超過限制，跳出內層循環
            if sum_so_far > limit:
                break
            # 如果和是質數且序列長度在範圍內
            sequence_length = j - i + 1
            if sequence_length >= min_length and sequence_length <= max_length:
                if sum_so_far >= start and is_prime(sum_so_far):
                    sequence = primes[i:j+1]
                    results.append((sequence, sum_so_far))
                    # 將序列加入到對應質數的列表中
                    if sum_so_far not in prime_sums_dict:
                        prime_sums_dict[sum_so_far] = []
                    prime_sums_dict[sum_so_far].append(sequence)
    
    return results, prime_sums_dict

class PrimeSumApp:
    def __init__(self, root):
        # 初始化設定
        self.font_size = 12
        self.tree_font = tkfont.Font(size=self.font_size)
        
        # 建立主視窗
        self.root = root
        self.root.title("由連續質數相加所得的質數搜索器")
        self.root.geometry("800x600")
        
        # 設定主視窗最小大小
        self.root.minsize(400, 300)
        
        # 配置主視窗grid
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # 初始化樣式
        self.style = ttk.Style()
        self.style.theme_use('default')
        
        # 定義明亮模式的顏色
        self.light_theme = {
            'bg': 'SystemButtonFace',
            'fg': 'SystemButtonText',
            'text_bg': 'white',
            'text_fg': 'black',
            'frame_bg': 'SystemButtonFace'
        }
        
        # 定義暗黑模式的顏色
        self.dark_theme = {
            'bg': '#2d2d2d',
            'fg': 'white',
            'text_bg': '#1e1e1e',
            'text_fg': '#ffffff',
            'frame_bg': '#2d2d2d'
        }
        
        # 預設使用明亮模式
        self.is_dark_mode = False
        self.current_theme = self.light_theme
        
        # 記錄上次存檔路徑
        self.last_save_dir = None
        
        # 引入re模組用於正則表達式
        self.re = re
        
        # 建立主框架
        main_frame = ttk.Frame(root, style='Custom.TFrame')
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(2, weight=1)  # 讓結果區域可以自動擴展
        
        # 建立工具列
        toolbar_frame = ttk.Frame(main_frame, style='Custom.TFrame')
        toolbar_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # 複製按鈕
        self.copy_btn = tk.Button(toolbar_frame, text="📋", width=3, command=self.copy_to_clipboard)
        self.copy_btn.pack(side="left", padx=2)
        self.create_tooltip(self.copy_btn, "複製到剪貼簿")
        
        # 儲存按鈕
        self.save_btn = tk.Button(toolbar_frame, text="💾", width=3, command=self.save_to_file)
        self.save_btn.pack(side="left", padx=2)
        self.create_tooltip(self.save_btn, "另存為CSV")
        
        # 暗黑模式切換按鈕
        self.theme_btn = tk.Button(toolbar_frame, text="🌓", width=3, command=self.toggle_theme)
        self.theme_btn.pack(side="left", padx=2)
        self.create_tooltip(self.theme_btn, "切換系統／暗黑模式")
        
        # 建立設定區域
        settings_frame = ttk.LabelFrame(main_frame, text="設定", style='Custom.TLabelframe')
        settings_frame.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        settings_frame.grid_columnconfigure(1, weight=1)  # 讓輸入框可以自動調整寬度
        
        # 建立搜尋範圍輸入框
        ttk.Label(settings_frame, text="搜尋範圍：").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        range_frame = ttk.Frame(settings_frame, style='Custom.TFrame')
        range_frame.grid(row=0, column=1, sticky="ew")
        range_frame.grid_columnconfigure(1, weight=1)
        
        self.start_var = tk.StringVar(value="1")
        self.end_var = tk.StringVar(value="10000")
        
        ttk.Entry(range_frame, textvariable=self.start_var).grid(row=0, column=0, sticky="ew", padx=(0,5))
        ttk.Label(range_frame, text="至").grid(row=0, column=1)
        ttk.Entry(range_frame, textvariable=self.end_var).grid(row=0, column=2, sticky="ew", padx=(5,0))
        
        range_frame.grid_columnconfigure(0, weight=1)
        range_frame.grid_columnconfigure(2, weight=1)
        
        # 序列數量範圍設定
        ttk.Label(settings_frame, text="序列數量範圍：").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        
        seq_range_frame = ttk.Frame(settings_frame, style='Custom.TFrame')
        seq_range_frame.grid(row=1, column=1, sticky="ew")
        seq_range_frame.grid_columnconfigure(1, weight=1)
        
        self.min_sequences_var = tk.StringVar(value="1")
        self.max_sequences_var = tk.StringVar(value="∞")
        
        ttk.Entry(seq_range_frame, textvariable=self.min_sequences_var).grid(row=0, column=0, sticky="ew", padx=(0,5))
        ttk.Label(seq_range_frame, text="至").grid(row=0, column=1)
        ttk.Entry(seq_range_frame, textvariable=self.max_sequences_var).grid(row=0, column=2, sticky="ew", padx=(5,0))
        
        seq_range_frame.grid_columnconfigure(0, weight=1)
        seq_range_frame.grid_columnconfigure(2, weight=1)
        
        ttk.Label(settings_frame, text="序列長度範圍：").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        
        length_frame = ttk.Frame(settings_frame, style='Custom.TFrame')
        length_frame.grid(row=2, column=1, sticky="ew")
        length_frame.grid_columnconfigure(1, weight=1)
        
        self.min_length_var = tk.StringVar(value="1")
        self.max_length_var = tk.StringVar(value="5")
        
        ttk.Entry(length_frame, textvariable=self.min_length_var).grid(row=0, column=0, sticky="ew", padx=(0,5))
        ttk.Label(length_frame, text="至").grid(row=0, column=1)
        ttk.Entry(length_frame, textvariable=self.max_length_var).grid(row=0, column=2, sticky="ew", padx=(5,0))
        
        length_frame.grid_columnconfigure(0, weight=1)
        length_frame.grid_columnconfigure(2, weight=1)
        
        # 計算按鈕
        self.calc_btn = tk.Button(settings_frame, text="計算", command=self.calculate)
        self.calc_btn.grid(row=3, column=0, columnspan=2, pady=10)
        
        # 結果顯示區域
        result_frame = ttk.LabelFrame(main_frame, text="結果", style='Custom.TLabelframe')
        result_frame.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")
        result_frame.grid_rowconfigure(1, weight=1)
        result_frame.grid_columnconfigure(0, weight=1)
        
        # 設定表格視圖樣式
        style = ttk.Style()
        style.configure('Treeview', 
            font=("TkDefaultFont", self.font_size),
            rowheight=int(self.tree_font.metrics()['linespace'] * 1.5)
        )
        style.configure('Treeview.Heading', 
            font=("TkDefaultFont", self.font_size),
            relief="flat"
        )
        style.map('Treeview.Heading',
            relief=[('pressed', 'sunken'), ('!pressed', 'flat')]
        )
        
        # 建立表格視圖
        self.tree = ttk.Treeview(result_frame, columns=("length", "result", "primes"), show="headings")
        self.tree.grid(row=1, column=0, sticky="nsew")
        
        # 設定欄位標題
        self.tree.heading("length", text="使用質數量", command=lambda: self.sort_column("length"))
        self.tree.heading("result", text="相加得到質數", command=lambda: self.sort_column("result"))
        self.tree.heading("primes", text="質數序列", command=lambda: self.sort_column("primes"))
        
        # 設定欄位寬度和對齊方式
        self.tree.column("length", width=100, anchor="center")
        self.tree.column("result", width=100, anchor="center")
        self.tree.column("primes", width=300, anchor="w")
        
        # 綁定右鍵選單事件
        self.tree.bind('<Button-3>', self.create_column_menu)
        
        # 建立捲軸
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # 統計資訊區域
        self.stats_var = tk.StringVar()
        ttk.Label(result_frame, textvariable=self.stats_var).grid(row=2, column=0, columnspan=2, pady=5)
        
        # 初始化排序狀態
        self.sort_states = {
            "primes": False,  # False 表示升序
            "result": False,
            "length": False
        }
        
        # 儲存欄位順序
        self.column_order = ["length", "result", "primes"]
        
        # 初始化表格資料
        self.all_results = []
        self.prime_sums_dict = {}
    
    def create_tooltip(self, widget, text):
        """為按鈕創建懸停提示"""
        tooltip = None
        
        def show_tooltip(event):
            nonlocal tooltip
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # 建立工具提示視窗
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            # 建立標籤
            label = tk.Label(tooltip, text=text, justify='left',
                           background="#ffffe0" if not self.is_dark_mode else "#2d2d2d",
                           foreground="black" if not self.is_dark_mode else "white",
                           relief='solid', borderwidth=1,
                           font=("TkDefaultFont", "9"))
            label.pack()
        
        def hide_tooltip(event):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None
        
        widget.bind('<Enter>', show_tooltip)
        widget.bind('<Leave>', hide_tooltip)

    def toggle_theme(self):
        """切換暗黑/明亮模式"""
        self.is_dark_mode = not self.is_dark_mode
        self.current_theme = self.dark_theme if self.is_dark_mode else self.light_theme
        
        # 更新按鈕顏色
        button_config = {
            'bg': self.current_theme['bg'],
            'fg': self.current_theme['fg'],
            'activebackground': self.dark_theme['text_bg'] if self.is_dark_mode else 'SystemButtonFace',
            'activeforeground': self.dark_theme['text_fg'] if self.is_dark_mode else 'SystemButtonText'
        }
        
        for btn in [self.calc_btn, self.copy_btn, self.save_btn, self.theme_btn]:
            btn.configure(**button_config)
        
        # 更新樣式
        self.style.configure('Custom.TFrame', background=self.current_theme['frame_bg'])
        self.style.configure('Custom.TLabelframe', background=self.current_theme['frame_bg'])
        self.style.configure('Custom.TLabelframe.Label', background=self.current_theme['frame_bg'],
                           foreground=self.current_theme['fg'])
        
        # 更新表格樣式
        if self.is_dark_mode:
            self.style.configure('Treeview',
                background=self.current_theme['text_bg'],
                fieldbackground=self.current_theme['text_bg'],
                foreground=self.current_theme['text_fg'])
            self.style.configure('Treeview.Heading',
                background=self.current_theme['bg'],
                foreground=self.current_theme['fg'])
            self.style.map('Treeview.Heading',
                background=[('active', self.dark_theme['text_bg'])],
                foreground=[('active', 'white')])
        else:
            self.style.configure('Treeview',
                background='white',
                fieldbackground='white',
                foreground='black')
            self.style.configure('Treeview.Heading',
                background='SystemButtonFace',
                foreground='SystemButtonText')
            self.style.map('Treeview.Heading',
                background=[('active', 'SystemButtonFace')],
                foreground=[('active', 'SystemButtonText')])
        
        # 遞迴更新所有子元件
        def update_frames(widget):
            for child in widget.winfo_children():
                if isinstance(child, (ttk.Frame, ttk.LabelFrame)):
                    child.configure(style='Custom.TFrame')
                elif isinstance(child, ttk.Label):
                    child.configure(foreground=self.current_theme['fg'])
                elif isinstance(child, tk.Label):
                    child.configure(
                        bg=self.current_theme['frame_bg'],
                        fg=self.current_theme['fg'])
                update_frames(child)
        
        update_frames(self.root)
    
    def optimize_column_width(self, column=None):
        """自動最佳化欄位寬度"""
        def get_max_width(col):
            # 取得標題寬度
            header = self.tree.heading(col)['text']
            max_width = self.tree_font.measure(header) + 20
            
            # 檢查所有項目的寬度
            for item in self.tree.get_children():
                cell_value = str(self.tree.set(item, col))
                width = self.tree_font.measure(cell_value) + 20
                max_width = max(max_width, width)
            
            return max_width
        
        if column and column[0] == "#":
            column = column[1:]  # 移除 # 字首
        
        if column:
            # 最佳化指定欄位
            width = get_max_width(column)
            self.tree.column(column, width=width)
        else:
            # 最佳化所有欄位
            for col in ["length", "result", "primes"]:
                width = get_max_width(col)
                self.tree.column(col, width=width)
    
    def create_column_menu(self, event):
        """建立欄位標題右鍵選單"""
        region = self.tree.identify_region(event.x, event.y)
        if region != "heading":
            return
            
        column = self.tree.identify_column(event.x)
        if not column:
            return
            
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="自動最佳化欄位寬度", 
                        command=lambda: self.optimize_column_width(column))
        menu.add_command(label="平均分配欄位寬度", 
                        command=self.distribute_column_widths)
        
        # 顯示選單
        menu.post(event.x_root, event.y_root)
    
    def distribute_column_widths(self):
        """平均分配欄位寬度"""
        # 取得表格可用寬度
        tree_width = self.tree.winfo_width()
        # 扣除垂直捲軸的寬度
        scrollbar_width = 20
        available_width = tree_width - scrollbar_width
        # 計算每個欄位的寬度
        column_count = len(self.tree["columns"])
        width_per_column = available_width // column_count
        
        # 設定每個欄位的寬度
        for col in self.tree["columns"]:
            self.tree.column(col, width=width_per_column)
    
    def sort_column(self, col):
        """排序指定欄位"""
        # 清空現有內容
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 取得所有資料
        data = []
        for primes, result in self.all_results:
            data.append({
                "length": len(primes),
                "result": result,
                "primes": str(primes)
            })
        
        # 根據欄位類型進行排序
        reverse = self.sort_states[col]
        
        if col == "primes":
            # 對質數序列進行數字排序
            def get_first_number(item):
                # 從字串中提取第一個數字
                match = self.re.search(r'\[(\d+)', item["primes"])
                return int(match.group(1)) if match else 0
            
            data.sort(key=get_first_number, reverse=reverse)
        else:
            # 數字排序
            data.sort(key=lambda x: x[col], reverse=reverse)
        
        # 更新排序狀態
        self.sort_states[col] = not reverse
        
        # 重新插入資料
        for item in data:
            values = (item["length"], item["result"], item["primes"])
            self.tree.insert("", "end", values=values)
        
        # 更新標題箭頭
        for c in self.tree["columns"]:
            if c == col:
                arrow = "↓" if reverse else "↑"
                text = self.tree.heading(c)["text"].split(" ")[0]  # 移除舊箭頭
                self.tree.heading(c, text=f"{text} {arrow}")
            else:
                text = self.tree.heading(c)["text"].split(" ")[0]  # 移除舊箭頭
                self.tree.heading(c, text=text)
    
    def copy_to_clipboard(self):
        """複製結果到剪貼簿"""
        if not self.tree.get_children():
            messagebox.showwarning("警告！", "沒有可複製的內容！")
            return
        
        # 獲取標題
        headers = []
        for col in self.tree["columns"]:
            header = self.tree.heading(col)['text']
            headers.append(header)
        
        # 獲取選中的項目
        selected_items = self.tree.selection()
        content = ['\t'.join(headers)]  # 加入標題行
        
        if selected_items:
            # 如果有選中項目，只複製選中的部分
            for item in selected_items:
                values = self.tree.item(item)['values']
                content.append('\t'.join(map(str, values)))
        else:
            # 如果沒有選中項目，複製全部
            for item in self.tree.get_children():
                values = self.tree.item(item)['values']
                content.append('\t'.join(map(str, values)))
        
        # 將內容複製到剪貼簿
        if content:
            self.root.clipboard_clear()
            self.root.clipboard_append('\n'.join(content))
            messagebox.showinfo("成功", "已複製到剪貼簿！")
    
    def save_to_file(self):
        """儲存結果為CSV檔"""
        if not self.tree.get_children():
            messagebox.showwarning("警告！", "沒有可儲存的內容！")
            return
        
        # 開啟檔案儲存對話框
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV檔案", "*.csv"), ("所有檔案", "*.*")],
            title="另存為CSV",
            initialdir=self.last_save_dir,
            initialfile="質數搜索結果.csv"
        )
        
        if file_path:  # 如果使用者沒有取消
            try:
                # 更新最後儲存路徑
                import os
                self.last_save_dir = os.path.dirname(file_path)
                
                with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    # 寫入標題列
                    headers = []
                    for col in self.tree["columns"]:
                        header = self.tree.heading(col)['text']
                        headers.append(header)
                    writer.writerow(headers)
                    
                    # 寫入資料列
                    for item in self.tree.get_children():
                        values = self.tree.item(item)['values']
                        writer.writerow(values)
                
                messagebox.showinfo("成功", "檔案已儲存！")
            except Exception as e:
                messagebox.showerror("錯誤", f"儲存失敗：{str(e)}")
    
    def calculate(self):
        """執行計算"""
        try:
            start = int(self.start_var.get())
            end = int(self.end_var.get())
            min_length = int(self.min_length_var.get())
            max_length = int(self.max_length_var.get())
            min_sequences = int(self.min_sequences_var.get())
            
            # 處理最大序列數量，∞ 表示無限制
            max_sequences_str = self.max_sequences_var.get()
            max_sequences = float('inf') if max_sequences_str == "∞" else int(max_sequences_str)
            
            if start < 1 or end < start:
                messagebox.showerror("錯誤", "請輸入有效的搜尋範圍！")
                return
            
            if min_length < 1 or max_length < min_length:
                messagebox.showerror("錯誤", "請輸入有效的序列長度範圍！")
                return
            
            if min_sequences < 1:
                messagebox.showerror("錯誤", "最小序列數量必須大於0！")
                return
            
            if max_sequences != float('inf') and max_sequences < min_sequences:
                messagebox.showerror("錯誤", "請輸入有效的序列數量範圍！")
                return
            
            # 執行搜索
            self.all_results, self.prime_sums_dict = find_prime_sums(end, min_length, max_length, start)
            
            # 篩選出符合序列數量要求的結果
            filtered_results = []
            for prime, sequences in self.prime_sums_dict.items():
                seq_count = len(sequences)
                if min_sequences <= seq_count <= max_sequences:
                    # 將所有序列都加入結果中
                    for sequence in sequences:
                        filtered_results.append((sequence, prime))
            self.all_results = filtered_results
            
            # 初始化排序狀態
            self.sort_states = {"primes": False, "result": False, "length": False}
            
            # 更新顯示
            self.update_display()
            
        except ValueError as e:
            if "invalid literal for int()" in str(e):
                messagebox.showerror("錯誤", "請輸入有效的數字！(序列數量可使用 ∞ 表示無限制)")
            else:
                messagebox.showerror("錯誤", str(e))
    
    def update_display(self):
        """更新顯示的結果"""
        # 清空現有內容
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 插入新的資料
        for primes, result in self.all_results:
            values = []
            for col in self.tree["columns"]:
                if col == "length":
                    values.append(len(primes))
                elif col == "result":
                    values.append(result)
                elif col == "primes":
                    values.append(str(primes))
            self.tree.insert("", "end", values=values)
        
        # 更新統計資訊
        total_count = len(self.all_results)
        if total_count > 0:
            min_length = min(len(primes) for primes, _ in self.all_results)
            max_length = max(len(primes) for primes, _ in self.all_results)
            self.stats_var.set(f"共找到 {total_count} 組結果，使用質數量範圍：{min_length} - {max_length}")
        else:
            self.stats_var.set("沒有找到符合條件的結果")

def main():
    root = tk.Tk()
    app = PrimeSumApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
