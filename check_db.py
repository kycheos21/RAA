# -*- coding: utf-8 -*-
"""
DB 내용 확인 스크립트
"""

import sqlite3

def check_database():
    """DB 내용 확인"""
    try:
        conn = sqlite3.connect('auction_data.db')
        cursor = conn.cursor()
        
        # 테이블 존재 확인
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auction_items'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ auction_items 테이블 존재")
            
            # 데이터 개수 확인
            cursor.execute("SELECT COUNT(*) FROM auction_items")
            count = cursor.fetchone()[0]
            print(f"📊 총 데이터 개수: {count}개")
            
            # 최근 데이터 5개 확인
            cursor.execute("SELECT tid, sa_no, address, created_at FROM auction_items ORDER BY created_at DESC LIMIT 5")
            recent_data = cursor.fetchall()
            
            print("\n📋 최근 데이터 5개:")
            for i, data in enumerate(recent_data, 1):
                print(f"{i}. TID: {data[0]}, 사건번호: {data[1]}")
                print(f"   주소: {data[2][:50]}...")
                print(f"   생성일: {data[3]}")
                print()
        else:
            print("❌ auction_items 테이블이 존재하지 않습니다.")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ DB 확인 실패: {e}")

if __name__ == "__main__":
    check_database()
