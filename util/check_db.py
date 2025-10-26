import sqlite3

try:
    conn = sqlite3.connect('tankauction.db')
    cursor = conn.cursor()
    
    # 테이블 목록 확인
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("테이블 목록:", tables)
    
    # 각 테이블의 레코드 수 확인
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"{table[0]} 테이블 레코드 수: {count}")
    
    conn.close()
    print("DB 확인 완료")
    
except Exception as e:
    print(f"DB 확인 실패: {e}")
