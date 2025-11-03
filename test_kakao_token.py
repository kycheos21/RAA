# -*- coding: utf-8 -*-
"""
카카오톡 토큰 발급 테스트 스크립트
- OAuth 2.0 인증 코드 받기
- Access Token 및 Refresh Token 발급
- 토큰을 kakao_tokens.json에 저장
"""

import requests
import json
import webbrowser
from util.config_from_reference import get_kakao_config

# 카카오톡 설정 로드
kakao_config = get_kakao_config()
REST_API_KEY = kakao_config['rest_api_key']
REDIRECT_URI = kakao_config['redirect_uri']
TOKEN_FILE = "kakao_tokens.json"

def print_auth_url():
    """인증 URL을 생성하고 브라우저에서 열기"""
    auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?client_id={REST_API_KEY}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope=talk_message"
        f"&prompt=login"
        f"&require_consent=true"
    )
    
    print("="*60)
    print("카카오 로그인 URL을 생성했습니다.")
    print("="*60)
    print(f"URL: {auth_url}")
    print("="*60)
    print("\n브라우저가 자동으로 열립니다.")
    print("로그인 후 '카카오톡 메시지 전송' 권한에 반드시 동의하세요.")
    print("동의하지 않으면 다음 단계로 진행할 수 없습니다.")
    print("\n리다이렉트된 URL에서 'code=' 뒤의 값을 복사하세요.")
    print("예시: http://localhost:8080?code=XXXXXXX → XXXXXXX를 복사")
    print("\n브라우저를 엽니다...")
    print("="*60)
    
    # 브라우저 열기
    webbrowser.open(auth_url)
    
    return auth_url

def get_tokens_with_code(code):
    """인증 코드로 Access Token 및 Refresh Token 발급"""
    token_url = "https://kauth.kakao.com/oauth/token"
    
    data = {
        "grant_type": "authorization_code",
        "client_id": REST_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "code": code
    }
    
    print("\n토큰 발급 중...")
    print(f"요청 URL: {token_url}")
    print(f"요청 데이터: {data}")
    
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        tokens = response.json()
        print("\n토큰 발급 성공!")
        print("="*60)
        print(f"Access Token: {tokens.get('access_token', 'N/A')[:50]}...")
        print(f"Token Type: {tokens.get('token_type', 'N/A')}")
        print(f"Expires In: {tokens.get('expires_in', 'N/A')}초")
        print(f"Refresh Token: {tokens.get('refresh_token', 'N/A')[:50]}...")
        print("="*60)
        return tokens
    else:
        print(f"\n토큰 발급 실패!")
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.text}")
        return None

def save_tokens(tokens):
    """토큰을 파일에 저장"""
    try:
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, ensure_ascii=False, indent=2)
        print(f"\n토큰 저장 완료: {TOKEN_FILE}")
        return True
    except Exception as e:
        print(f"\n토큰 저장 실패: {e}")
        return False

def main():
    """메인 함수"""
    print("\n카카오톡 토큰 발급 테스트를 시작합니다.")
    print("="*60)
    
    # 1. 인증 URL 생성 및 브라우저 열기
    auth_url = print_auth_url()
    
    # 2. 사용자로부터 인증 코드 입력받기
    print("\n브라우저에서 로그인 및 동의를 완료하신 후,")
    print("리다이렉트된 URL의 'code=' 부분을 복사하여 입력하세요.")
    print("\n(취소하려면 엔터만 누르세요)")
    code = input("\n인증 코드 입력: ").strip()
    
    if not code:
        print("사용자가 취소했습니다.")
        return
    
    # 3. 토큰 발급
    tokens = get_tokens_with_code(code)
    
    if tokens:
        # 4. 토큰 저장
        if save_tokens(tokens):
            print("\n✅ 모든 작업이 완료되었습니다!")
            print("\n다음 단계:")
            print("1. test_kakao_message.py를 실행하여 메시지 전송 테스트를 진행하세요.")
        else:
            print("\n❌ 토큰 발급은 성공했지만 저장에 실패했습니다.")
    else:
        print("\n❌ 토큰 발급에 실패했습니다.")

if __name__ == "__main__":
    main()

