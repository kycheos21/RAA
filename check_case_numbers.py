#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
사건번호 추출 결과 확인
"""

import sqlite3

def check_case_numbers():
    """사건번호 추출 결과 확인"""
    conn = sqlite3.connect('auction_data.db')
    cursor = conn.cursor()
    
    # 전체 레코드 수
    cursor.execute('SELECT COUNT(*) FROM auction_items')
    total_count = cursor.fetchone()[0]
    print(f"📊 전체 레코드 수: {total_count}")
    
    # 사건번호가 있는 레코드 수
    cursor.execute('SELECT COUNT(*) FROM auction_items WHERE case_number IS NOT NULL AND case_number != ""')
    case_count = cursor.fetchone()[0]
    print(f"📊 사건번호가 있는 레코드 수: {case_count}")
    
    # 사건번호 샘플 확인
    cursor.execute('SELECT case_number, address FROM auction_items WHERE case_number IS NOT NULL AND case_number != "" LIMIT 10')
    samples = cursor.fetchall()
    
    print("\n🔍 사건번호 샘플:")
    print("-" * 80)
    for case_number, address in samples:
        print(f"사건번호: {case_number}")
        print(f"주소: {address[:100]}...")
        print("-" * 80)
    
    # 연도별 사건번호 통계
    cursor.execute('''
        SELECT SUBSTR(case_number, 1, 4) as year, COUNT(*) as count 
        FROM auction_items 
        WHERE case_number IS NOT NULL AND case_number != "" 
        GROUP BY SUBSTR(case_number, 1, 4) 
        ORDER BY year
    ''')
    year_stats = cursor.fetchall()
    
    print("\n📈 연도별 사건번호 통계:")
    for year, count in year_stats:
        print(f"  {year}년: {count}개")
    
    conn.close()

if __name__ == "__main__":
    check_case_numbers()
