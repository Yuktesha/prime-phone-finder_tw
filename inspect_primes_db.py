import sqlite3
import os

# 使用絕對路徑
DB_PATH = 'D:/WinSurf/backend/primes.db'

def check_db():
    print(f"Checking database at: {DB_PATH}")
    print(f"Database exists: {os.path.exists(DB_PATH)}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 檢查資料庫中的表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables in database: {tables}")
        
        # 檢查每個表的結構
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"Columns: {columns}")
            
            # 獲取表中的行數
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"Row count: {count}")
            
            # 獲取表中的前5行
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            rows = cursor.fetchall()
            print(f"Sample data: {rows}")
            
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db()
