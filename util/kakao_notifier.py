# -*- coding: utf-8 -*-
"""
카카오톡 알림 유틸리티 모듈
- 토큰 로드/저장 함수
- 토큰 갱신 함수
- 메시지 전송 함수
- 에러 처리 및 로깅
"""

import requests
import json
import os
import sys
import logging
from datetime import datetime
from util.config_from_reference import get_kakao_config

# 카카오톡 설정 로드
kakao_config = get_kakao_config()
REST_API_KEY = kakao_config['rest_api_key']
TOKEN_FILE = "kakao_tokens.json"

def setup_logger():
    """로거 생성 - logs 폴더에 kakao_notifier 로그 파일 생성"""
    import glob
    
    # logs/ 폴더 생성
    logs_dir = "logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # 7일 이상 된 로그 파일 삭제
    try:
        cutoff_time = datetime.now().timestamp() - (7 * 24 * 60 * 60)  # 7일 전
        log_pattern = os.path.join(logs_dir, "kakao_notifier_log_*.log")
        old_logs = glob.glob(log_pattern)
        
        for log_file in old_logs:
            if os.path.getmtime(log_file) < cutoff_time:
                os.remove(log_file)
                print(f"오래된 로그 파일 삭제: {log_file}")
    except Exception as e:
        print(f"로그 파일 정리 중 오류: {e}")
    
    # 로그 파일명에 현재 날짜와 시간 포함
    log_filename = os.path.join(logs_dir, f"kakao_notifier_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"카카오톡 알림 로깅 시작 - 로그 파일: {log_filename}")
    return logger

def load_tokens():
    """저장된 토큰 로드"""
    try:
        if not os.path.exists(TOKEN_FILE):
            logger = setup_logger()
            logger.error(f"토큰 파일을 찾을 수 없습니다: {TOKEN_FILE}")
            logger.error("먼저 test_kakao_token.py를 실행하여 토큰을 발급받으세요.")
            return None
            
        with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
            tokens = json.load(f)
        logger = setup_logger()
        logger.info(f"토큰 로드 성공: {TOKEN_FILE}")
        return tokens
    except json.JSONDecodeError as e:
        logger = setup_logger()
        logger.error(f"토큰 파일 파싱 실패: {e}")
        return None
    except Exception as e:
        logger = setup_logger()
        logger.error(f"토큰 로드 실패: {e}")
        return None

def save_tokens(tokens):
    """토큰을 파일에 저장"""
    try:
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            json.dump(tokens, f, ensure_ascii=False, indent=2)
        logger = setup_logger()
        logger.info(f"토큰 저장 완료: {TOKEN_FILE}")
        return True
    except Exception as e:
        logger = setup_logger()
        logger.error(f"토큰 저장 실패: {e}")
        return False

def refresh_access_token(refresh_token):
    """Refresh Token으로 Access Token 갱신"""
    token_url = "https://kauth.kakao.com/oauth/token"
    
    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": refresh_token
    }
    
    logger = setup_logger()
    logger.info("Access Token 갱신 중...")
    
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        new_tokens = response.json()
        logger.info("Access Token 갱신 성공!")
        
        # 기존 Refresh Token이 있으면 유지, 없으면 새로운 것으로 대체
        if 'refresh_token' not in new_tokens:
            new_tokens['refresh_token'] = refresh_token
        
        # 토큰 저장
        if save_tokens(new_tokens):
            return new_tokens['access_token']
        else:
            logger.error("토큰 저장 실패")
            return None
    else:
        logger.error(f"Access Token 갱신 실패! 상태 코드: {response.status_code}")
        logger.error(f"응답: {response.text}")
        return None

def send_kakao_message(message, link_url=None):
    """
    카카오톡 메시지 전송
    
    Args:
        message (str): 전송할 메시지 내용
        link_url (str, optional): 첨부할 링크 URL
    
    Returns:
        bool: 전송 성공 여부
    """
    logger = setup_logger()
    logger.info("카카오톡 메시지 전송 시작")
    
    # 1. 토큰 로드
    tokens = load_tokens()
    if not tokens:
        return False
    
    access_token = tokens.get('access_token')
    refresh_token = tokens.get('refresh_token')
    
    if not access_token:
        logger.error("Access Token이 없습니다.")
        return False
    
    # 2. 메시지 전송 시도
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    # 메시지 템플릿 생성
    message_object = {
        "object_type": "text",
        "text": message
    }
    
    # 링크가 있으면 추가
    if link_url:
        message_object["link"] = {
            "web_url": link_url,
            "mobile_web_url": link_url
        }
    
    data = {
        "template_object": json.dumps(message_object, ensure_ascii=False)
    }
    
    logger.info(f"메시지 전송 중... 메시지: {message[:50]}...")
    
    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        
        # 3. 결과 확인
        if response.status_code == 200:
            logger.info("메시지 전송 성공!")
            return True
        elif response.status_code == 401:
            # 401 Unauthorized - 토큰 만료
            logger.warning("Access Token이 만료되었습니다. 갱신을 시도합니다...")
            
            if refresh_token:
                new_access_token = refresh_access_token(refresh_token)
                if new_access_token:
                    # 갱신된 토큰으로 재전송
                    headers["Authorization"] = f"Bearer {new_access_token}"
                    logger.info("갱신된 토큰으로 메시지 재전송...")
                    response = requests.post(url, headers=headers, data=data, timeout=10)
                    
                    if response.status_code == 200:
                        logger.info("메시지 전송 성공!")
                        return True
                    else:
                        logger.error(f"메시지 전송 실패! 상태 코드: {response.status_code}")
                        logger.error(f"응답: {response.text}")
                        return False
                else:
                    logger.error("토큰 갱신 실패. test_kakao_token.py를 다시 실행하세요.")
                    return False
            else:
                logger.error("Refresh Token이 없습니다. test_kakao_token.py를 다시 실행하세요.")
                return False
        else:
            logger.error(f"메시지 전송 실패! 상태 코드: {response.status_code}")
            logger.error(f"응답: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("메시지 전송 타임아웃 발생")
        return False
    except Exception as e:
        logger.error(f"메시지 전송 중 예외 발생: {e}")
        return False

def send_new_items_notification(new_items, excel_link=None):
    """
    신규 항목 알림 메시지 전송
    
    Args:
        new_items (list): 신규 항목 리스트 [{'case_number': 'xxx', 'tid': 'xxx'}, ...]
        excel_link (str, optional): 엑셀 파일 링크
    
    Returns:
        bool: 전송 성공 여부
    """
    logger = setup_logger()
    
    if not new_items or len(new_items) == 0:
        logger.info("신규 항목이 없어 알림을 보내지 않습니다.")
        return False
    
    # 메시지 내용 구성
    item_count = len(new_items)
    message_lines = [f"새로운 경매 항목 {item_count}개가 발견되었습니다."]
    message_lines.append("")  # 빈 줄
    
    # 사건번호, tid 리스트 추가
    for idx, item in enumerate(new_items, 1):
        case_number = item.get('case_number', 'N/A')
        tid = item.get('tid', 'N/A')
        message_lines.append(f"{idx}. 사건번호: {case_number} / TID: {tid}")
    
    # 엑셀 링크 추가
    if excel_link:
        message_lines.append("")
        message_lines.append(f"엑셀 파일: {excel_link}")
    
    message = "\n".join(message_lines)
    
    logger.info(f"신규 항목 알림 메시지 생성 완료: {item_count}개 항목")
    return send_kakao_message(message, link_url=excel_link)

