import sqlite3

def check_db_structure():
    try:
        conn = sqlite3.connect('backend/primes.db')
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"Tables in database: {tables}")
        
        # For each table, get its structure and a sample of data
        for table in tables:
            table_name = table[0]
            print(f"\nTable: {table_name}")
            
            # Get table structure
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print(f"Columns: {columns}")
            
            # Get sample data (first 5 rows)
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
            sample_data = cursor.fetchall()
            print(f"Sample data: {sample_data}")
            
            # Get count of 3-digit and 4-digit primes if this is a prime number table
            if table_name == 'primes':
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE value >= 100 AND value <= 999")
                three_digit_count = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT COUNT(*) FROM {table_name} WHERE value >= 1000 AND value <= 9999")
                four_digit_count = cursor.fetchone()[0]
                
                print(f"3-digit primes: {three_digit_count}")
                print(f"4-digit primes: {four_digit_count}")
                
                # Get a few samples of 3-digit and 4-digit primes
                cursor.execute(f"SELECT value FROM {table_name} WHERE value >= 100 AND value <= 999 LIMIT 5")
                three_digit_samples = cursor.fetchall()
                print(f"3-digit prime samples: {three_digit_samples}")
                
                cursor.execute(f"SELECT value FROM {table_name} WHERE value >= 1000 AND value <= 9999 LIMIT 5")
                four_digit_samples = cursor.fetchall()
                print(f"4-digit prime samples: {four_digit_samples}")
            
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_db_structure()
