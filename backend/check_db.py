import sqlite3

# 連接到資料庫
conn = sqlite3.connect('prime_phones.db')
cursor = conn.cursor()

# 獲取資料表結構
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='prime_phones'")
schema = cursor.fetchone()[0]
print("資料表結構:")
print(schema)

# 檢查前幾筆資料
cursor.execute("SELECT * FROM prime_phones LIMIT 5")
rows = cursor.fetchall()
print("\n前 5 筆資料:")
for row in rows:
    print(row)

# 檢查索引
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='prime_phones'")
indexes = cursor.fetchall()
print("\n索引:")
for idx in indexes:
    print(f"索引名稱: {idx[0]}")
    print(f"索引定義: {idx[1]}")

# 關閉連接
conn.close()
