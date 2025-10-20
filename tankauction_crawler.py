# -*- coding: utf-8 -*-
"""
탱크옥션 크롤링 기본 코드
- Chrome 드라이버 설정
- 탱크옥션 사이트 열기
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sys
from util.config_from_reference import get_tankauction_config
import requests
import json
import sqlite3
from datetime import datetime

def setup_chrome_driver():
    """Chrome 드라이버 설정"""
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-password-manager") # 비밀번호 저장 기능 비활성화
    chrome_options.add_argument("--disable-save-password-bubble") # 비밀번호 저장 팝업 비활성화
    chrome_options.add_argument("--disable-autofill") # 자동완성 비활성화
    chrome_options.add_argument("--disable-password-generation") # 비밀번호 생성 비활성화
    chrome_options.add_argument("--disable-single-click-autofill") # 단일 클릭 자동완성 비활성화
    #chrome_options.add_argument("--disable-credit-card-autofill") # 신용카드 자동완성 비활성화
    chrome_options.add_experimental_option("prefs", {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0
    })
    chrome_options.add_argument("--disable-prompt-on-repost") # 재전송 확인 팝업 비활성화
    chrome_options.add_argument("--disable-background-timer-throttling") # 백그라운드 타이머 제한 비활성화
    chrome_options.add_argument("--disable-backgrounding-occluded-windows") # 가려진 창 백그라운드 처리 비활성화
    chrome_options.add_argument("--disable-renderer-backgrounding") # 렌더러 백그라운드 처리 비활성화
    chrome_options.add_argument("--disable-features=TranslateUI") # 번역 UI 비활성화
    chrome_options.add_argument("--disable-ipc-flooding-protection") # IPC 플러딩 보호 비활성화
    chrome_options.add_argument("--disable-popup-blocking") # 팝업 차단 비활성화
    chrome_options.add_argument("--disable-notifications") # 알림 비활성화
    chrome_options.add_argument("--disable-infobars") # 정보 표시줄 비활성화
    chrome_options.add_argument("--disable-extensions") # 확장 프로그램 비활성화
    chrome_options.add_argument("--disable-plugins") # 플러그인 비활성화
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Chrome 드라이버 자동 관리 (webdriver-manager 사용하지 않고 기본 경로 사용)
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def open_tankauction(driver, config):
    """탱크옥션 사이트 열기"""
    try:
        print("탱크옥션 사이트에 접속 중...")
        # util/config_from_reference.py에서 로드한 URL 사용
        driver.get(config['url'])
        
        # 페이지 로딩 대기
        wait = WebDriverWait(driver, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        
        print("탱크옥션 사이트 접속 완료")
        print(f"현재 페이지 제목: {driver.title}")
        
        return True
        
    except Exception as e:
        print(f"탱크옥션 사이트 접속 실패: {e}")
        return False

def login_tankauction(driver, config):
    """탱크옥션 로그인"""
    try:
        print("로그인 시도 중...")
        wait = WebDriverWait(driver, 10)
        
        # 로그인 버튼 클릭 (JavaScript로 강제 클릭)
        login_button = wait.until(EC.presence_of_element_located((By.XPATH, "//span[@onclick='floating_div(400);']")))
        driver.execute_script("arguments[0].click();", login_button)
        print("로그인 버튼 클릭 완료")
        
        # 로그인 팝업 로딩 대기 (팝업이 나타날 때까지)
        wait.until(EC.presence_of_element_located((By.ID, "client_id")))
        
        # 팝업이 나타났는지 확인
        try:
            # 아이디 입력 필드 찾기 및 입력
            username_field = wait.until(EC.presence_of_element_located((By.ID, "client_id")))
            username_field.clear()
            username_field.send_keys(config['username'])
            print(f"아이디 입력 완료: {config['username']}")
            
            # 비밀번호 입력 필드 찾기 및 입력
            password_field = driver.find_element(By.ID, "passwd")
            password_field.clear()
            password_field.send_keys(config['password'])
            print("비밀번호 입력 완료")
            
            # 로그인 버튼 클릭
            login_submit = driver.find_element(By.XPATH, "//a[@onclick='login();']")
            login_submit.click()
            print("로그인 시도 완료")
                
        except Exception as e:
            print(f"로그인 팝업 처리 실패: {e}")
            return False
        
        # 로그인 성공 확인 (페이지 리다이렉트 또는 특정 요소 로딩 대기)
        wait.until(lambda driver: "login" not in driver.current_url.lower() or 
                   EC.presence_of_element_located((By.XPATH, "//a[contains(text(), '로그아웃')] | //span[contains(text(), '환영')] | //div[contains(@class, 'user-info')]")))
        
        # 로그인 성공 여부 확인 (URL 변경 또는 특정 요소 존재 확인)
        current_url = driver.current_url
        if "login" not in current_url.lower():
            print("로그인 성공!")
            return True
        else:
            print("로그인 실패")
            return False
            
    except Exception as e:
        print(f"로그인 실패: {e}")
        return False

def extract_cookies_from_driver(driver):
    """Selenium 드라이버에서 쿠키 추출"""
    cookies = driver.get_cookies()
    cookie_dict = {}
    for cookie in cookies:
        cookie_dict[cookie['name']] = cookie['value']
    return cookie_dict

def create_requests_session(cookies):
    """requests 세션 생성 및 쿠키 설정"""
    session = requests.Session()
    for name, value in cookies.items():
        session.cookies.set(name, value)
    return session

def get_auction_data_via_api(session, config):
    """API를 통해 경매 데이터 가져오기"""
    try:
        url = config['api_url']
        
        # 요청 헤더 추가
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.77 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
            'Referer': config['search_url']
        }
        
        print(f"API 요청 URL: {url}")
        print(f"요청 헤더: {headers}")
        
        # Network 탭에서 찾은 정확한 POST 요청 재현
        headers.update({
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.tankauction.com',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
        
        # Network 탭에서 확인한 정확한 데이터
        data = {
            'srchCase': 'srchAll',
            'pageNo': '1',
            'dataSize': '20',
            'pageSize': '10'
        }
        
        print(f"POST 데이터: {data}")
        print(f"업데이트된 헤더: {headers}")
        
        response = session.post(url, data=data, headers=headers)
        response.raise_for_status()
        
        print(f"API 응답 상태: {response.status_code}")
        print(f"응답 헤더: {dict(response.headers)}")
        print(f"응답 내용 길이: {len(response.text)}")
        print(f"응답 내용 (처음 500자): {response.text[:500]}")
        
        # JSON 파싱 시도
        try:
            data = response.json()
            print(f"JSON 데이터 타입: {type(data)}")
            print(f"데이터 키: {list(data.keys()) if isinstance(data, dict) else '리스트 데이터'}")
            return data
        except json.JSONDecodeError:
            print("JSON 파싱 실패, HTML 응답일 수 있음")
            return response.text
            
    except Exception as e:
        print(f"API 호출 실패: {e}")
        return None

def create_database():
    """SQLite 데이터베이스 생성"""
    conn = sqlite3.connect('auction_data.db')
    cursor = conn.cursor()
    
    # 경매물건 테이블 생성
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS auction_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tid INTEGER UNIQUE,
            sa_no TEXT,
            case_number TEXT,
            court_dept TEXT,
            appraisal_amount TEXT,
            minimum_amount TEXT,
            success_amount INTEGER,
            minimum_percent INTEGER,
            success_percent INTEGER,
            address TEXT,
            area_info TEXT,
            important_charge TEXT,
            disposal_type TEXT,
            category TEXT,
            special_condition TEXT,
            status_name TEXT,
            bid_date TEXT,
            bid_time TEXT,
            d_day TEXT,
            img_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("SQLite 데이터베이스 생성 완료")

def save_auction_data_to_db(auction_data):
    """경매 데이터를 SQLite에 저장"""
    if not auction_data:
        print("저장할 경매 데이터가 없습니다.")
        return False
    
    conn = sqlite3.connect('auction_data.db')
    cursor = conn.cursor()
    
    saved_count = 0
    skipped_count = 0
    
    # 리스트 형태의 데이터 처리
    for i, row_data in enumerate(auction_data):
        try:
            # row_data는 ['', '', '아파트\n2024-16379\n주소...', '가격정보', '상태', '날짜', '조회수'] 형태
            if len(row_data) < 4:  # 최소 4개 컬럼 필요
                continue
                
            # 데이터 파싱 (사건번호 추출 포함)
            address_info = row_data[2] if len(row_data) > 2 else ""
            price_info = row_data[3] if len(row_data) > 3 else ""
            status_info = row_data[4] if len(row_data) > 4 else ""
            date_info = row_data[5] if len(row_data) > 5 else ""
            view_count = row_data[6] if len(row_data) > 6 else "0"
            
            # 사건번호 추출 (정규식 사용) - 물건번호까지 포함
            import re
            case_number = ""
            if address_info:
                # 2024-16379, 2025-50976, 2023-1809(7) 등의 패턴 추출
                # 물건번호가 있는 경우: 2023-1809(7) → 2023-1809(7)
                # 물건번호가 없는 경우: 2024-16379 → 2024-16379
                case_match = re.search(r'(\d{4}-\d+(?:\(\d+\))?)', address_info)
                if case_match:
                    case_number = case_match.group(1)
            
            # 중복 체크 (사건번호로)
            if case_number:
                cursor.execute('SELECT id FROM auction_items WHERE case_number = ?', (case_number,))
                if cursor.fetchone():
                    skipped_count += 1
                    continue
            else:
                # 사건번호가 없으면 주소로 중복 체크
                cursor.execute('SELECT id FROM auction_items WHERE address = ?', (address_info,))
                if cursor.fetchone():
                    skipped_count += 1
                    continue
            
            # 데이터 삽입
            cursor.execute('''
                INSERT INTO auction_items (
                    tid, sa_no, case_number, court_dept, appraisal_amount, minimum_amount,
                    success_amount, minimum_percent, success_percent, address,
                    area_info, important_charge, disposal_type, category,
                    special_condition, status_name, bid_date, bid_time, d_day, img_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                i + 1,  # tid (순번)
                f"ITEM_{i+1:03d}",  # sa_no (사건번호)
                case_number,  # case_number (실제 사건번호)
                "",  # court_dept
                price_info,  # appraisal_amount
                "",  # minimum_amount
                0,  # success_amount
                0,  # minimum_percent
                0,  # success_percent
                address_info,  # address
                "",  # area_info
                "",  # important_charge
                "",  # disposal_type
                "",  # category
                "",  # special_condition
                status_info,  # status_name
                date_info,  # bid_date
                "",  # bid_time
                "",  # d_day
                ""  # img_url
            ))
            
            saved_count += 1
            
        except Exception as e:
            print(f"데이터 저장 오류 (행 {i+1}): {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"데이터 저장 완료: {saved_count}개 저장, {skipped_count}개 건너뜀")
    return True

def navigate_to_favorite_search(driver, config):
    """탱크옥션 경매검색 > 즐겨쓰는 검색열기 > 안전소액경매로 이동"""
    try:
        wait = WebDriverWait(driver, 10)
        
        # 1. 로그인 후 직접 caList.php 접속
        print("경매검색 페이지로 이동 중...")
        driver.get(config['search_url'])
        time.sleep(2)  # 페이지 로딩 대기
        print("경매검색 페이지 접속 완료")
        
        # 팝업창 닫기 (로그인 정보 저장 팝업 등)
        try:
            # 일반적인 팝업 닫기 버튼들 시도
            popup_selectors = [
                "//button[contains(text(), '닫기')]",
                "//button[contains(text(), '취소')]",
                "//button[contains(text(), '나중에')]",
                "//div[@class='close']",
                "//span[@class='close']",
                "//button[@class='close']",
                "//div[contains(@class, 'popup')]//button",
                "//div[contains(@class, 'modal')]//button"
            ]
            
            for selector in popup_selectors:
                try:
                    popup_close = driver.find_element(By.XPATH, selector)
                    if popup_close.is_displayed():
                        popup_close.click()
                        print("팝업창 닫기 완료")
                        time.sleep(1)
                        break
                except:
                    continue
        except Exception as e:
            print(f"팝업창 닫기 시도 완료 (팝업 없음 또는 다른 형태): {e}")
        
        # 2. 즐겨쓰는 검색열기 클릭
        print("즐겨쓰는 검색열기 클릭 중...")
        favorite_search = wait.until(EC.element_to_be_clickable((By.ID, "fv_view1")))
        favorite_search.click()
        print("즐겨쓰는 검색열기 클릭 완료")
        
        # 3. 안전소액경매 클릭
        print("안전소액경매 클릭 중...")
        safe_search = wait.until(EC.element_to_be_clickable((By.XPATH, "//span[@onclick=\"FvMySrch('106099','1')\"]")))
        safe_search.click()
        print("안전소액경매 클릭 완료")
        
        # 4. 검색 결과 페이지 로딩 완료 대기
        wait.until(EC.presence_of_element_located((By.XPATH, "//table | //div[contains(@class, 'list')] | //div[contains(@class, 'result')]")))
        print("안전소액경매 검색 페이지로 이동 완료")
        return True
        
    except Exception as e:
        print(f"즐겨쓰는 검색열기 이동 실패: {e}")
        return False
def main():
    """메인 함수"""
    driver = None
    try:
        # util/config_from_reference.py에서 탱크옥션 설정 로드
        config = get_tankauction_config()
        print(f"설정 정보 로드 완료: {config['url']}")
        
        # Chrome 드라이버 설정
        driver = setup_chrome_driver()
        
        # 탱크옥션 사이트 열기
        if open_tankauction(driver, config):
            print("탱크옥션 사이트가 성공적으로 열렸습니다.")
            
            # 로그인 시도
            if login_tankauction(driver, config):
                print("로그인까지 완료되었습니다.")
                
                # 데이터베이스 생성
                create_database()
                
                # 로그인 후 세션 안정화를 위한 대기
                print("로그인 세션 안정화 대기 중... (5초)")
                time.sleep(5)
                
                # 팝업 닫기
                print("팝업 닫기 시도 중...")
                try:
                    # 정확한 닫기 버튼 선택자
                    close_button = driver.find_element(By.XPATH, "//div[@class='hand' and @onclick='mySectionToggle(1)']")
                    if close_button.is_displayed():
                        close_button.click()
                        print("팝업 닫기 성공")
                        time.sleep(1)  # 닫기 후 대기
                    else:
                        print("팝업이 없거나 닫을 수 없습니다.")
                except Exception as e:
                    print(f"팝업 닫기 실패: {e}")
                
                # 경매검색 클릭
                print("경매검색 클릭 중...")
                try:
                    auction_search = driver.find_element(By.XPATH, "//li[@class='menu_on']//a[@href='/ca/caList.php' and contains(text(), '경매검색')]")
                    if auction_search.is_displayed():
                        auction_search.click()
                        print("경매검색 클릭 성공")
                        time.sleep(2)  # 페이지 로딩 대기
                    else:
                        print("경매검색 버튼이 보이지 않습니다.")
                except Exception as e:
                    print(f"경매검색 클릭 실패: {e}")
                
                # 즐겨쓰는 검색열기 클릭
                print("즐겨쓰는 검색열기 클릭 중...")
                try:
                    favorite_search = driver.find_element(By.ID, "fv_view1")
                    if favorite_search.is_displayed():
                        favorite_search.click()
                        print("즐겨쓰는 검색열기 클릭 성공")
                        time.sleep(2)  # 메뉴 표시 대기
                    else:
                        print("즐겨쓰는 검색열기 버튼이 보이지 않습니다.")
                except Exception as e:
                    print(f"즐겨쓰는 검색열기 클릭 실패: {e}")
                
                # 안전소액경매 클릭 (Network 탭에서 URL 확인용)
                print("안전소액경매 클릭 중...")
                try:
                    safe_auction = driver.find_element(By.XPATH, "//span[@onclick=\"FvMySrch('106099','1')\"]")
                    if safe_auction.is_displayed():
                        # Network 탭에서 URL 확인을 위해 현재 URL 기록
                        print(f"클릭 전 URL: {driver.current_url}")
                        
                        safe_auction.click()
                        print("안전소액경매 클릭 성공")
                        
                        # 클릭 후 URL 확인
                        time.sleep(3)  # 페이지 로딩 대기
                        print(f"클릭 후 URL: {driver.current_url}")
                        
                        # Network 요청 로그 확인을 위한 추가 대기
                        time.sleep(2)
                        
                    else:
                        print("안전소액경매 버튼이 보이지 않습니다.")
                except Exception as e:
                    print(f"안전소액경매 클릭 실패: {e}")
                
                # 목록수 100개로 변경
                print("목록수 100개로 변경 중...")
                try:
                    # 현재 페이지 정보 출력
                    print(f"현재 URL: {driver.current_url}")
                    print(f"현재 페이지 제목: {driver.title}")
                    
                    # dataSize_s 요소 찾기
                    print("dataSize_s 요소 찾기 시도...")
                    data_size_select = driver.find_element(By.ID, "dataSize_s")
                    print(f"dataSize_s 요소 발견: {data_size_select}")
                    print(f"요소 표시 여부: {data_size_select.is_displayed()}")
                    print(f"요소 텍스트: {data_size_select.text}")
                    
                    if data_size_select.is_displayed():
                        from selenium.webdriver.support.ui import Select
                        select = Select(data_size_select)
                        print("Select 객체 생성 완료")
                        
                        # 현재 선택된 값 확인
                        current_value = select.first_selected_option.get_attribute("value")
                        print(f"현재 선택된 값: {current_value}")
                        
                        select.select_by_value("100")
                        print("목록수 100개로 변경 성공")
                        sys.stdout.flush()
                        time.sleep(3)  # 페이지 로딩 대기
                    else:
                        print("목록수 선택 박스가 보이지 않습니다.")
                except Exception as e:
                    print(f"목록수 변경 실패: {e}")
                    print(f"오류 타입: {type(e)}")
                    print(f"오류 상세: {str(e)}")
                
                # 검색결과 스크래핑
                print("검색결과 스크래핑 중...")
                auction_data = []  # 메인 함수에서 초기화
                try:
                    # 경매 데이터 테이블 찾기
                    auction_table = driver.find_element(By.ID, "tblLst")
                    if auction_table.is_displayed():
                        print("경매 데이터 테이블 발견")
                        
                        # 테이블 행들 추출
                        rows = auction_table.find_elements(By.TAG_NAME, "tr")
                        print(f"총 {len(rows)}개의 행 발견")
                        
                        for i, row in enumerate(rows):
                            try:
                                cells = row.find_elements(By.TAG_NAME, "td")
                                if len(cells) > 0:
                                    row_data = [cell.text.strip() for cell in cells]
                                    auction_data.append(row_data)
                                    print(f"행 {i+1}: {row_data}")
                            except Exception as e:
                                print(f"행 {i+1} 처리 실패: {e}")
                        
                        print(f"총 {len(auction_data)}개의 경매 데이터 추출 완료")
                        
                    else:
                        print("경매 데이터 테이블을 찾을 수 없습니다.")
                        
                except Exception as e:
                    print(f"검색결과 스크래핑 실패: {e}")
                
                print("스크래핑 완료. 브라우저를 확인해주세요.")
                # input("Enter 키를 누르면 계속 진행됩니다...")  # 자동 실행을 위해 주석 처리
                if auction_data:
                    print("API를 통한 경매 데이터 수집 완료")
                    
                    # SQLite에 데이터 저장
                    save_auction_data_to_db(auction_data)
                else:
                    print("API를 통한 경매 데이터 수집 실패")
            else:
                print("로그인 실패")
        else:
            print("탱크옥션 사이트 열기 실패")
            
    except Exception as e:
        print(f"오류 발생: {e}")
        

if __name__ == "__main__":
    main()
