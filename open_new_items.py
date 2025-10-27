# -*- coding: utf-8 -*-
"""
신규 항목 상세 페이지 열기 (간소화 버전)
- test_data에서 신규 항목 tid 추출
- cntsViewPN 함수로 상세 페이지 열기
- auction_data에서 이미 스크래핑된 정보 활용
"""

import sqlite3
import time
import logging
import sys
import re
import json
import os
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def setup_logging():
    """로깅 설정"""
    # 로그 파일명에 현재 날짜와 시간 포함
    log_filename = f"scraping_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)  # 명시적으로 stdout 지정
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"로깅 시작 - 로그 파일: {log_filename}")
    return logger

def get_new_items_from_db(logger):
    """new_data에서 신규 항목 tid 가져오기"""
    logger.info("데이터베이스에서 신규 항목 조회 시작")
    conn = sqlite3.connect('tankauction.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT tid FROM new_data')
    new_items = cursor.fetchall()
    
    conn.close()
    
    tids = [row[0] for row in new_items]
    logger.info(f"신규 항목 {len(tids)}개 발견: {tids}")
    print(f"신규 항목 {len(tids)}개 발견: {tids}")
    return tids

def create_valid_data_table():
    """valid_data 테이블 생성"""
    conn = sqlite3.connect('tankauction.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS valid_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tid TEXT NOT NULL,
            case_number TEXT,
            address TEXT,
            land_area TEXT,
            building_area TEXT,
            appraisal_amount TEXT,
            minimum_amount TEXT,
            failure_count TEXT,
            yearly_transaction_count INTEGER,
            naver_link TEXT,
            bdsplanet_link TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def clear_valid_data_table(logger):
    """valid_data 테이블 초기화 (프로세스 시작 시 이전 데이터 삭제)"""
    try:
        conn = sqlite3.connect('tankauction.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM valid_data')
        conn.commit()
        conn.close()
        
        logger.info("valid_data 테이블 초기화 완료")
        print("✅ valid_data 테이블 초기화 완료")
        
    except Exception as e:
        logger.error(f"valid_data 테이블 초기화 실패: {e}")
        print(f"❌ valid_data 테이블 초기화 실패: {e}")

def save_to_valid_data_table(tid, case_number, address, land_area, building_area, 
                           appraisal_amount, minimum_amount, failure_count, yearly_count, naver_link, bdsplanet_link, logger):
    """valid_data 테이블에 데이터 저장"""
    try:
        conn = sqlite3.connect('tankauction.db')
        cursor = conn.cursor()
        
        # 데이터 삽입
        cursor.execute('''
            INSERT INTO valid_data 
            (tid, case_number, address, land_area, building_area, 
             appraisal_amount, minimum_amount, failure_count, yearly_transaction_count, naver_link, bdsplanet_link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (str(tid), case_number, address, land_area, building_area,
              appraisal_amount, minimum_amount, failure_count, yearly_count, naver_link, bdsplanet_link))
        
        conn.commit()
        conn.close()
        
        logger.info(f"valid_data 테이블에 저장 완료: tid={tid}")
        print(f"✅ valid_data 테이블에 저장 완료: tid={tid}")
        
    except Exception as e:
        logger.error(f"valid_data 테이블 저장 실패: {e}")
        print(f"❌ valid_data 테이블 저장 실패: {e}")

def scrape_naver_link(driver, logger):
    """상세페이지에서 네이버부동산 링크 스크래핑"""
    try:
        # 네이버부동산 링크 찾기
        naver_elements = driver.find_elements(By.XPATH, "//span[@onclick and contains(@onclick, 'outLink') and contains(@onclick, 'land.naver.com')]")
        
        if naver_elements:
            onclick_attr = naver_elements[0].get_attribute('onclick')
            # outLink('https://...')에서 URL 추출
            import re
            match = re.search(r"outLink\('([^']+)'\)", onclick_attr)
            if match:
                naver_link = match.group(1)
                logger.info(f"네이버부동산 링크 발견: {naver_link}")
                return naver_link
        
        logger.info("네이버부동산 링크를 찾을 수 없습니다")
        return None
        
    except Exception as e:
        logger.error(f"네이버부동산 링크 스크래핑 오류: {e}")
        return None

def scrape_bdsplanet_link(driver, logger):
    """상세페이지에서 부동산플래닛 링크 스크래핑"""
    try:
        # 부동산플래닛 링크 찾기
        bdsplanet_elements = driver.find_elements(By.XPATH, "//span[@onclick and contains(@onclick, 'outLink') and contains(@onclick, 'bdsplanet.com')]")
        
        if bdsplanet_elements:
            onclick_attr = bdsplanet_elements[0].get_attribute('onclick')
            # outLink('https://...')에서 URL 추출
            import re
            match = re.search(r"outLink\('([^']+)'\)", onclick_attr)
            if match:
                bdsplanet_link = match.group(1)
                logger.info(f"부동산플래닛 링크 발견: {bdsplanet_link}")
                return bdsplanet_link
        
        logger.info("부동산플래닛 링크를 찾을 수 없습니다")
        return None
        
    except Exception as e:
        logger.error(f"부동산플래닛 링크 스크래핑 오류: {e}")
        return None

def scrape_land_transaction_data(driver, logger):
    """국토부 실거래가 테이블에서 매매 데이터 스크래핑 (1년간 매매건수 계산)"""
    logger.info("국토부 실거래가 테이블 스크래핑 시작")
    try:
        # 매매 테이블 찾기
        sales_table = driver.find_element(By.XPATH, '//table[@id="qtLst"]//div[contains(text(), "매매(만원)")]/following-sibling::table')
        logger.info("매매 테이블 발견")
        
        # 테이블 행들 가져오기 (헤더 제외)
        rows = sales_table.find_elements(By.XPATH, './/tr[position()>1]')
        
        transaction_data = []
        yearly_count = 0
        one_year_ago = datetime.now() - timedelta(days=365)
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if len(cells) >= 5:
                year_month = cells[0].text.strip()
                min_price = cells[1].text.strip()
                avg_price = cells[2].text.strip()
                max_price = cells[3].text.strip()
                count = int(cells[4].text.strip())
                
                # 년월을 파싱하여 날짜 객체 생성
                try:
                    year = int(year_month[:4])
                    month = int(year_month[4:6])
                    
                    # 년월을 datetime 객체로 변환
                    transaction_date = datetime(year, month, 1)
                    
                    # 1년 이내 거래인지 확인 (거래일이 1년 전 이후여야 함)
                    if transaction_date >= one_year_ago:
                        yearly_count += count
                        transaction_data.append({
                            'year_month': year_month,
                            'min_price': min_price,
                            'avg_price': avg_price,
                            'max_price': max_price,
                            'count': count,
                            'year': year,
                            'month': month,
                            'date': transaction_date
                        })
                except ValueError as e:
                    logger.warning(f"날짜 파싱 오류: {year_month}, 오류: {e}")
                    continue
        
        logger.info(f"국토부 실거래가 데이터 {len(transaction_data)}개 추출 완료")
        logger.info(f"1년간 매매건수: {yearly_count}건")
        return transaction_data, yearly_count
        
    except Exception as e:
        logger.error(f"국토부 실거래가 테이블 스크래핑 오류: {e}")
        return [], 0

def open_detail_pages_in_new_tabs(driver, tids, logger, auction_data):
    """신규 항목 상세 페이지를 cntsViewPN 함수로 열기 (auction_data 활용)"""
    logger.info(f"신규 항목 {len(tids)}개 상세 페이지 열기 시작")
    
    # 기본 탭 핸들 저장
    base_tab = driver.current_window_handle
    
    for i, tid in enumerate(tids):
        try:
            # 기본 탭으로 전환 (새 탭을 열기 위해)
            driver.switch_to.window(base_tab)
            
            print(f"\n[{i+1}/{len(tids)}] cntsViewPN 함수로 열기: tid={tid}")
            
            # cntsViewPN 함수 직접 호출 (서버에서 세션 유지하며 열기)
            driver.execute_script(f"cntsViewPN({tid}, 1, 1, 0);")
            
            # 새 창/탭이 열릴 때까지 대기
            time.sleep(3)
            
            # 새 탭으로 전환
            if len(driver.window_handles) > 1:
                # 마지막으로 열린 탭으로 전환
                new_tab = driver.window_handles[-1]
                driver.switch_to.window(new_tab)
                print(f"페이지 제목: {driver.title}")
                
                # 국토부 실거래가 데이터 스크래핑 (1년간 매매건수 계산)
                transaction_data, yearly_count = scrape_land_transaction_data(driver, logger)
                
                print("=" * 50)
                print(f"상세 페이지 열기 완료: tid={tid}")
                print("=" * 50)
                
                print(f"\n1년간 매매건수: {yearly_count}건")
                
                # 매매 데이터 상세 출력
                if transaction_data:
                    print("\n[국토부 실거래가 매매 데이터]")
                    for data in transaction_data:
                        print(f"  {data['year_month']}: 최저가 {data['min_price']}만원, 평균가 {data['avg_price']}만원, 최고가 {data['max_price']}만원, 건수 {data['count']}건")
                
                # 1년간 매매건수가 0건이면 프로세스 중지
                if yearly_count == 0:
                    driver.close()
                    driver.switch_to.window(base_tab)
                    continue
                
                # 네이버부동산 링크 스크래핑
                naver_link = scrape_naver_link(driver, logger)
                
                # 부동산플래닛 링크 스크래핑
                bdsplanet_link = scrape_bdsplanet_link(driver, logger)
                
                # 기본값 설정 (auction_data가 없어도 저장 가능하도록)
                case_number = "N/A"
                address = "N/A"
                land_area = "N/A"
                building_area = "N/A"
                appraisal_amount = "N/A"
                minimum_amount = "N/A"
                failure_count = "N/A"
                
                # auction_data가 있으면 상세 정보 추출
                if auction_data:
                    print("\n[auction_data 정보]")
                    for i, row_data in enumerate(auction_data):
                        if len(row_data) >= 8:  # tid가 있는 경우
                            tid_from_data = str(row_data[7])  # 마지막 요소가 tid
                            if tid_from_data == str(tid):  # 현재 처리 중인 tid와 일치하는 경우
                                # 사건번호 추출
                                if len(row_data) > 2 and '\n' in row_data[2]:
                                    parts = row_data[2].split('\n')
                                    if len(parts) > 1:
                                        case_number = parts[1].strip()
                                
                                # 주소 추출
                                if len(row_data) > 2:
                                    lines = row_data[2].split('\n')
                                    if len(lines) > 2:
                                        address = lines[2].strip()  # 세 번째 줄이 주소
                                
                                # 대지권 추출
                                if len(row_data) > 2 and '대지권' in row_data[2]:
                                    land_match = re.search(r'대지권\s+([0-9.]+)㎡', row_data[2])
                                    if land_match:
                                        land_area = f"{land_match.group(1)}㎡"
                                
                                # 건물면적 추출
                                if len(row_data) > 2 and '건물' in row_data[2]:
                                    building_match = re.search(r'건물\s+([0-9.]+)㎡', row_data[2])
                                    if building_match:
                                        building_area = f"{building_match.group(1)}㎡"
                                
                                # 감정가 추출
                                if len(row_data) > 3:
                                    prices = row_data[3].split('\n')
                                    if len(prices) > 0:
                                        appraisal_amount = prices[0].strip()
                                
                                # 최저가 추출
                                if len(row_data) > 3:
                                    prices = row_data[3].split('\n')
                                    if len(prices) > 1:
                                        minimum_amount = prices[1].strip()
                                
                                # 유찰 횟수 추출
                                if len(row_data) > 4 and '유찰' in row_data[4]:
                                    failure_match = re.search(r'유찰\s+(\d+)회', row_data[4])
                                    if failure_match:
                                        failure_count = f"{failure_match.group(1)}회"
                                
                                print(f"  사건번호: {case_number}")
                                print(f"  주소: {address}")
                                print(f"  대지권: {land_area}")
                                print(f"  건물면적: {building_area}")
                                print(f"  감정가: {appraisal_amount}")
                                print(f"  최저가: {minimum_amount}")
                                print(f"  유찰 횟수: {failure_count}")
                                break
                else:
                    print("\n[auction_data 정보] 없음 - 기본값으로 저장")
                
                # valid_data 테이블에 데이터 저장 (1년간 매매건수가 1건 이상일 때만)
                save_to_valid_data_table(tid, case_number, address, land_area, building_area, 
                                      appraisal_amount, minimum_amount, failure_count, yearly_count, naver_link, bdsplanet_link, logger)
                
                # 링크 정보만 로그에 기록
                if naver_link:
                    logger.info(f"네이버부동산 링크: {naver_link}")
                    print(f"네이버부동산 링크: {naver_link}")
                
                if bdsplanet_link:
                    logger.info(f"부동산플래닛 링크: {bdsplanet_link}")
                    print(f"부동산플래닛 링크: {bdsplanet_link}")
                
                print("=" * 50)
                
                # 3초 후 탭 닫기
                print("3초 후 탭을 닫습니다...")
                time.sleep(3)
                driver.close()
                
                # 기본 탭으로 돌아가기
                driver.switch_to.window(base_tab)
                print("기본 탭으로 돌아왔습니다.")
            else:
                print("새 탭이 열리지 않았습니다.")
                
        except Exception as e:
            print(f"오류 발생 (tid={tid}): {e}")
            # 오류 발생 시에도 기본 탭으로 복귀 시도
            try:
                driver.switch_to.window(base_tab)
            except:
                pass
            continue

def open_new_items_in_browser(driver, logger, auction_data):
    """기존 브라우저에서 신규 항목 상세 페이지를 새 탭으로 열기"""
    # valid_data 테이블 생성
    create_valid_data_table()
    
    # 이전 프로세스 데이터 초기화
    clear_valid_data_table(logger)
    
    # 신규 항목 tid 가져오기
    tids = get_new_items_from_db(logger)
    
    if not tids:
        print("신규 항목이 없습니다.")
        return
    
    print(f"\n총 {len(tids)}개의 신규 항목 상세 페이지를 열겠습니다.")
    
    # 새 탭으로 상세 페이지 열기
    open_detail_pages_in_new_tabs(driver, tids, logger, auction_data)
    
    print("\n모든 상세 페이지가 새 탭으로 열렸습니다.")
    print("브라우저를 확인해주세요.")
    print("\n브라우저를 열어둔 채로 프로세스를 종료합니다.")
    print("브라우저를 수동으로 닫아주세요.")

def load_session_cookies(driver):
    """저장된 쿠키를 로드하여 세션 복원"""
    if os.path.exists('session_cookies.json'):
        with open('session_cookies.json', 'r') as f:
            cookies = json.load(f)
            for cookie in cookies:
                driver.add_cookie(cookie)
        driver.refresh()  # 쿠키 적용
        print("세션 복원 완료")
        
        # 안전소액경매 페이지로 이동
        driver.get("https://tankauction.com/ca/caList.php?page=1")
        print("안전소액경매 페이지로 이동 완료")
        return True
    else:
        print("세션 쿠키 파일이 없습니다. 수동 로그인이 필요합니다.")
        print("10초 후 자동으로 상세 페이지를 열겠습니다...")
        time.sleep(10)
        return False

def main():
    """메인 함수 (독립 실행용)"""
    # 로깅 설정
    logger = setup_logging()
    
    # valid_data 테이블 생성 및 초기화
    create_valid_data_table()
    clear_valid_data_table(logger)
    
    # 신규 항목 tid 가져오기
    tids = get_new_items_from_db(logger)
    
    if not tids:
        print("신규 항목이 없습니다.")
        return
    
    print(f"\n총 {len(tids)}개의 신규 항목 상세 페이지를 열겠습니다.")
    print("\n주의: Chrome 브라우저가 자동으로 열립니다.")
    
    # Chrome 드라이버 설정 (SSA.py와 동일)
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 탱크옥션 사이트 접속
        driver.get("https://www.tankauction.com")
        
        # 세션 쿠키 로드 (테스트용 - 전체 테스트 시 주석 처리)
        load_session_cookies(driver)
        
        # 1단계: 기본 정보 수집 (경매 정보, 링크 추출)
        open_new_items_in_browser(driver, logger, [])  # auction_data는 빈 리스트로 전달
        
        print("\n" + "="*50)
        print("1단계 완료: 기본 정보 수집")
        print("  - 경매 상세 정보")
        print("  - 국토부 실거래가 (1년간)")
        print("  - 네이버/부동산플래닛 링크")
        print("  - 주소 정보")
        print("="*50)
        
        # 2단계: 부동산플래닛 상세 스크래핑
        print("\n부동산플래닛 상세 정보 수집을 시작합니다...")
        from bdsplanet_scraper import scrape_bdsplanet_details
        scrape_bdsplanet_details(driver, logger)
        
        print("\n" + "="*50)
        print("2단계 완료: 부동산플래닛 상세 스크래핑")
        print("  - 평수별 실거래 데이터 (최저/최고/평균가)")
        print("  - 호별 AI 추정가")
        print("  - 호별 공시가")
        print("="*50)
        
        print("\n" + "="*50)
        print("✅ 전체 프로세스 완료!")
        print("="*50)
        input("엔터를 눌러서 종료하세요...")
        
    finally:
        # driver.quit() 제거 - 브라우저를 열어둠
        pass

if __name__ == "__main__":
    main()
