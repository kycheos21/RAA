#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DB 스키마 확인
"""

import sqlite3

def check_db_schema():
    """DB 스키마 확인"""
    conn = sqlite3.connect('auction_data.db')
    cursor = conn.cursor()
    
    # 테이블 정보 확인
    cursor.execute("PRAGMA table_info(auction_items)")
    columns = cursor.fetchall()
    
    print("📋 현재 auction_items 테이블 컬럼:")
    print("-" * 50)
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # 데이터 확인
    cursor.execute('SELECT COUNT(*) FROM auction_items')
    count = cursor.fetchone()[0]
    print(f"\n📊 총 레코드 수: {count}")
    
    conn.close()

if __name__ == "__main__":
    check_db_schema()
