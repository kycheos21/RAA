#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DB 마이그레이션 스크립트 - case_number 컬럼 추가
"""

import sqlite3
import re

def migrate_database():
    """기존 DB에 case_number 컬럼 추가 및 데이터 마이그레이션"""
    conn = sqlite3.connect('auction_data.db')
    cursor = conn.cursor()
    
    try:
        # case_number 컬럼 추가
        cursor.execute('ALTER TABLE auction_items ADD COLUMN case_number TEXT')
        print("✅ case_number 컬럼 추가 완료")
        
        # 기존 데이터에서 사건번호 추출하여 업데이트
        cursor.execute('SELECT id, address FROM auction_items WHERE case_number IS NULL OR case_number = ""')
        rows = cursor.fetchall()
        
        updated_count = 0
        for row_id, address in rows:
            if address:
                # 2024-16379, 2025-50976 등의 패턴 추출
                case_match = re.search(r'(\d{4}-\d+)', address)
                if case_match:
                    case_number = case_match.group(1)
                    cursor.execute('UPDATE auction_items SET case_number = ? WHERE id = ?', (case_number, row_id))
                    updated_count += 1
        
        conn.commit()
        print(f"✅ {updated_count}개 레코드의 사건번호 추출 완료")
        
        # 결과 확인
        cursor.execute('SELECT COUNT(*) FROM auction_items WHERE case_number IS NOT NULL AND case_number != ""')
        count = cursor.fetchone()[0]
        print(f"✅ 총 {count}개 레코드에 사건번호가 설정됨")
        
    except Exception as e:
        print(f"❌ 마이그레이션 오류: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔄 DB 마이그레이션 시작...")
    migrate_database()
    print("✅ 마이그레이션 완료!")
