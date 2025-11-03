# -*- coding: utf-8 -*-
"""
카카오톡 메시지 전송 테스트 스크립트
- 저장된 토큰으로 "안녕" 메시지 전송
- 토큰 만료 시 자동 갱신
"""

import requests
import json
from util.config_from_reference import get_kakao_config

# 카카오톡 설정 로드
kakao_config = get_kakao_config()
REST_API_KEY = kakao_config['rest_api_key']
TOKEN_FILE = "kakao_tokens.json"

def load_tokens():
    """저장된 토큰 로드"""
    try:
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
            tokens = json.load(f)
        print(f"토큰 로드 성공: {TOKEN_FILE}")
        return tokens
    except FileNotFoundError:
        print(f"❌ 토큰 파일을 찾을 수 없습니다: {TOKEN_FILE}")
        print("먼저 test_kakao_token.py를 실행하여 토큰을 발급받으세요.")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ 토큰 파일 파싱 실패: {e}")
        return None
    except Exception as e:
        print(f"❌ 토큰 로드 실패: {e}")
        return None

def refresh_access_token(refresh_token):
    """Refresh Token으로 Access Token 갱신"""
    token_url = "https://kauth.kakao.com/oauth/token"
    
    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": refresh_token
    }
    
    print("\nAccess Token 갱신 중...")
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        new_tokens = response.json()
        print("✅ Access Token 갱신 성공!")
        
        # 기존 Refresh Token이 있으면 유지, 없으면 새로운 것으로 대체
        if 'refresh_token' not in new_tokens:
            new_tokens['refresh_token'] = refresh_token
        
        # 토큰 저장
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_tokens, f, ensure_ascii=False, indent=2)
        
        return new_tokens['access_token']
    else:
        print(f"❌ Access Token 갱신 실패!")
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.text}")
        return None

def send_test_message(access_token):
    """"안녕" 메시지 전송 테스트"""
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # 메시지 템플릿 생성
    message_object = {
        "object_type": "text",
        "text": "안녕",
        "link": {
            "web_url": "https://developers.kakao.com",
            "mobile_web_url": "https://developers.kakao.com"
        }
    }
    
    data = {
        "template_object": json.dumps(message_object, ensure_ascii=False)
    }
    
    print("\n메시지 전송 중...")
    print(f"메시지 내용: 안녕")
    
    response = requests.post(url, headers=headers, data=data)
    
    return response

def main():
    """메인 함수"""
    print("\n카카오톡 메시지 전송 테스트를 시작합니다.")
    print("="*60)
    
    # 1. 토큰 로드
    tokens = load_tokens()
    if not tokens:
        return
    
    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')
    
    if not access_token:
        print("❌ Access Token이 없습니다.")
        return
    
    # 2. 메시지 전송 시도
    response = send_test_message(access_token)
    
    # 3. 결과 확인
    if response.status_code == 200:
        print("\n✅ 메시지 전송 성공!")
        print("="*60)
        print("카카오톡을 확인하세요!")
        print("="*60)
    elif response.status_code == 401:
        # 401 Unauthorized - 토큰 만료
        print("\n⚠️ Access Token이 만료되었습니다.")
        print("Refresh Token으로 갱신을 시도합니다...")
        
        if refresh_token:
            new_access_token = refresh_access_token(refresh_token)
            if new_access_token:
                # 갱신된 토큰으로 재전송
                print("\n갱신된 토큰으로 메시지 재전송...")
                response = send_test_message(new_access_token)
                
                if response.status_code == 200:
                    print("\n✅ 메시지 전송 성공!")
                    print("="*60)
                    print("카카오톡을 확인하세요!")
                    print("="*60)
                else:
                    print(f"\n❌ 메시지 전송 실패!")
                    print(f"상태 코드: {response.status_code}")
                    print(f"응답: {response.text}")
            else:
                print("\n❌ 토큰 갱신 실패. test_kakao_token.py를 다시 실행하세요.")
        else:
            print("❌ Refresh Token이 없습니다. test_kakao_token.py를 다시 실행하세요.")
    else:
        print(f"\n❌ 메시지 전송 실패!")
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.text}")

if __name__ == "__main__":
    main()

