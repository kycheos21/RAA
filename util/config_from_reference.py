# -*- coding: utf-8 -*-
"""
Reference.md에서 설정 정보를 로드하는 유틸리티 모듈
"""

import re
import os

def load_config_from_reference():
    """Reference.md에서 설정 정보 로드"""
    config = {}
    reference_path = os.path.join("docs", "Reference.md")
    
    try:
        with open(reference_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 탱크옥션 URL 추출
        tankauction_match = re.search(r'- \*\*탱크옥션\*\*: (https?://[^\s]+)', content)
        if tankauction_match:
            config['tankauction_url'] = tankauction_match.group(1)
        
        # 탱크옥션 API 엔드포인트 추출
        api_match = re.search(r'- \*\*API 엔드포인트\*\*: (https?://[^\s]+)', content)
        if api_match:
            config['tankauction_api_url'] = api_match.group(1)
        
        # 탱크옥션 경매검색 페이지 추출
        search_page_match = re.search(r'- \*\*경매검색 페이지\*\*: (https?://[^\s]+)', content)
        if search_page_match:
            config['tankauction_search_url'] = search_page_match.group(1)
        
        # 부동산플래닛 URL 추출
        bdsplanet_match = re.search(r'- \*\*부동산플래닛\*\*: (https?://[^\s]+)', content)
        if bdsplanet_match:
            config['bdsplanet_url'] = bdsplanet_match.group(1)
        
        # ID 추출
        id_match = re.search(r'- \*\*ID\*\*: ([^\n]+)', content)
        if id_match:
            config['username'] = id_match.group(1).strip()
            
        # PW 추출
        pw_match = re.search(r'- \*\*PW\*\*: ([^\n]+)', content)
        if pw_match:
            config['password'] = pw_match.group(1).strip()
        
        # 카카오톡 REST API 키 추출
        kakao_key_match = re.search(r'REST API 키.*?`([^`]+)`', content, re.DOTALL)
        if kakao_key_match:
            config['kakao_rest_api_key'] = kakao_key_match.group(1).strip()
        
        # 카카오톡 Redirect URI 추출
        kakao_redirect_match = re.search(r'Redirect URI.*?`([^`]+)`', content, re.DOTALL)
        if kakao_redirect_match:
            config['kakao_redirect_uri'] = kakao_redirect_match.group(1).strip()
            
    except Exception as e:
        print(f"Reference.md 파일 읽기 실패: {e}")
        # 기본값 설정
        config = {
            'tankauction_url': 'https://tankauction.com',
            'tankauction_api_url': 'https://www.tankauction.com/res/myRsntList.php?dataSize=100&lsType=0&iType=1&stat=0&ctgr=0&sDt=0&rDt=30',
            'tankauction_search_url': 'https://www.tankauction.com/ca/caList.php',
            'bdsplanet_url': 'https://bdsplanet.com',
            'username': 'goodauction24@gmail.com',
            'password': 'newstart-1017'
        }
    
    return config

def get_tankauction_config():
    """탱크옥션 관련 설정만 반환"""
    config = load_config_from_reference()
    return {
        'url': config.get('tankauction_url', 'https://tankauction.com'),
        'api_url': config.get('tankauction_api_url', 'https://www.tankauction.com/res/myRsntList.php?dataSize=100&lsType=0&iType=1&stat=0&ctgr=0&sDt=0&rDt=30'),
        'search_url': config.get('tankauction_search_url', 'https://www.tankauction.com/ca/caList.php'),
        'username': config.get('username', 'goodauction24@gmail.com'),
        'password': config.get('password', 'newstart-1017')
    }

def get_bdsplanet_config():
    """부동산플래닛 관련 설정만 반환"""
    config = load_config_from_reference()
    return {
        'url': config.get('bdsplanet_url', 'https://bdsplanet.com'),
        'username': config.get('username', 'goodauction24@gmail.com'),
        'password': config.get('password', 'newstart-1017')
    }

def get_kakao_config():
    """카카오톡 API 관련 설정만 반환"""
    config = load_config_from_reference()
    return {
        'rest_api_key': config.get('kakao_rest_api_key', '0ce58273ec367b2b8736e6fa34d7ef98'),
        'redirect_uri': config.get('kakao_redirect_uri', 'http://localhost:8080')
    }

if __name__ == "__main__":
    # 테스트 코드
    config = load_config_from_reference()
    print("전체 설정:", config)
    print("탱크옥션 설정:", get_tankauction_config())
    print("부동산플래닛 설정:", get_bdsplanet_config())

