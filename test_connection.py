# -*- coding: utf-8 -*-
"""
탱크옥션 연결 테스트 스크립트
"""

import requests
import time

def test_connection():
    """다양한 방법으로 탱크옥션 연결 테스트"""
    
    urls_to_test = [
        "https://tankauction.com",
        "http://tankauction.com", 
        "https://www.tankauction.com",
        "http://www.tankauction.com"
    ]
    
    for url in urls_to_test:
        print(f"\n테스트 URL: {url}")
        try:
            response = requests.get(url, timeout=10)
            print(f"상태 코드: {response.status_code}")
            print(f"응답 시간: {response.elapsed.total_seconds():.2f}초")
            print(f"서버: {response.headers.get('Server', 'Unknown')}")
            if response.status_code == 200:
                print("✅ 연결 성공!")
                return url
        except requests.exceptions.ConnectTimeout:
            print("❌ 연결 시간 초과")
        except requests.exceptions.ConnectionError as e:
            print(f"❌ 연결 오류: {e}")
        except Exception as e:
            print(f"❌ 기타 오류: {e}")
    
    return None

if __name__ == "__main__":
    print("탱크옥션 연결 테스트 시작...")
    working_url = test_connection()
    
    if working_url:
        print(f"\n✅ 작동하는 URL 발견: {working_url}")
    else:
        print("\n❌ 모든 URL 연결 실패")
        print("가능한 원인:")
        print("1. 탱크옥션 사이트가 일시적으로 다운됨")
        print("2. 방화벽이나 보안 프로그램이 차단")
        print("3. 네트워크 설정 문제")
        print("4. 지역적 접속 제한")
