import sqlite3
import os

# 獲取數據庫路徑
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'primes.db')
print(f"Database path: {db_path}")
print(f"Database exists: {os.path.exists(db_path)}")

try:
    # 連接到數據庫
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 獲取表格列表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables in database: {tables}")
    
    # 獲取primes表的結構
    cursor.execute("PRAGMA table_info(primes)")
    columns = cursor.fetchall()
    print(f"Columns in primes table: {columns}")
    
    # 獲取primes表的前5條記錄
    cursor.execute("SELECT * FROM primes LIMIT 5")
    rows = cursor.fetchall()
    print(f"First 5 rows in primes table: {rows}")
    
    # 獲取primes表的記錄數
    cursor.execute("SELECT COUNT(*) FROM primes")
    count = cursor.fetchone()[0]
    print(f"Total number of rows in primes table: {count}")
    
    # 關閉連接
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
