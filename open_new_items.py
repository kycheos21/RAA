# -*- coding: utf-8 -*-
"""
신규 항목 상세 페이지 열기
- test_data에서 신규 항목 tid 추출
- cntsViewPN 함수로 상세 페이지 열기
- 상세 정보 스크래핑
"""

import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

def get_new_items_from_db():
    """test_data에서 신규 항목 tid 가져오기"""
    conn = sqlite3.connect('tankauction.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT tid FROM test_data')
    new_items = cursor.fetchall()
    
    conn.close()
    
    tids = [row[0] for row in new_items]
    print(f"신규 항목 {len(tids)}개 발견: {tids}")
    return tids

def scrape_detail_info(driver):
    """상세 페이지에서 정보 스크래핑"""
    detail_info = {}
    
    try:
        # 사건번호
        case_number = driver.find_element(By.XPATH, "//td[contains(text(), '사건번호')]/following-sibling::td[1]")
        detail_info['case_number'] = case_number.text.strip()
    except:
        detail_info['case_number'] = "N/A"
    
    try:
        # 주소
        address = driver.find_element(By.XPATH, "//td[contains(text(), '소재지')]/following-sibling::td[1]")
        detail_info['address'] = address.text.strip()
    except:
        detail_info['address'] = "N/A"
    
    try:
        # 감정가
        appraisal = driver.find_element(By.XPATH, "//td[contains(text(), '감정가액')]/following-sibling::td[1]")
        detail_info['appraisal_amount'] = appraisal.text.strip()
    except:
        detail_info['appraisal_amount'] = "N/A"
    
    try:
        # 최저가
        minimum = driver.find_element(By.XPATH, "//td[contains(text(), '최저가')]/following-sibling::td[1]")
        detail_info['minimum_amount'] = minimum.text.strip()
    except:
        detail_info['minimum_amount'] = "N/A"
    
    try:
        # 유찰 횟수
        failure_count = driver.find_element(By.XPATH, "//td[contains(text(), '유찰')]/following-sibling::td[1]")
        detail_info['failure_count'] = failure_count.text.strip()
    except:
        detail_info['failure_count'] = "N/A"
    
    return detail_info

def open_detail_pages_in_new_tabs(driver, tids):
    """신규 항목 상세 페이지를 cntsViewPN 함수로 열기 및 스크래핑"""
    
    # 기본 탭 핸들 저장
    base_tab = driver.current_window_handle
    
    for i, tid in enumerate(tids):
        try:
            # 기본 탭으로 전환 (새 탭을 열기 위해)
            driver.switch_to.window(base_tab)
            
            print(f"\n[{i+1}/{len(tids)}] cntsViewPN 함수로 열기: tid={tid}")
            print(f"  - tids 리스트: {tids}")
            print(f"  - 현재 인덱스: {i}")
            print(f"  - 현재 tid: {tid}")
            
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
                
                # 상세 정보 스크래핑 (주석 처리됨)
                # detail_info = scrape_detail_info(driver)
                
                # 정보 출력 (주석 처리됨)
                # print("=" * 50)
                # print(f"사건번호: {detail_info['case_number']}")
                # print(f"주소: {detail_info['address']}")
                # print(f"감정가: {detail_info['appraisal_amount']}")
                # print(f"최저가: {detail_info['minimum_amount']}")
                # print(f"유찰 횟수: {detail_info['failure_count']}")
                # print("=" * 50)
                
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

def open_new_items_in_browser(driver):
    """기존 브라우저에서 신규 항목 상세 페이지를 새 탭으로 열기"""
    # 신규 항목 tid 가져오기
    tids = get_new_items_from_db()
    
    if not tids:
        print("신규 항목이 없습니다.")
        return
    
    print(f"\n총 {len(tids)}개의 신규 항목 상세 페이지를 열겠습니다.")
    
    # 새 탭으로 상세 페이지 열기
    open_detail_pages_in_new_tabs(driver, tids)
    
    print("\n모든 상세 페이지가 새 탭으로 열렸습니다.")
    print("브라우저를 확인해주세요.")
    print("\n60초 후 자동으로 브라우저가 닫힙니다...")
    time.sleep(60)

def main():
    """메인 함수 (독립 실행용)"""
    # 신규 항목 tid 가져오기
    tids = get_new_items_from_db()
    
    if not tids:
        print("신규 항목이 없습니다.")
        return
    
    print(f"\n총 {len(tids)}개의 신규 항목 상세 페이지를 열겠습니다.")
    print("\n주의: Chrome 브라우저가 자동으로 열립니다.")
    
    # Chrome 드라이버 설정 (tankauction_crawler.py와 동일)
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 탱크옥션 사이트 접속 (로그인 필요)
        driver.get("https://www.tankauction.com")
        print("\n로그인 페이지가 열렸습니다.")
        print("수동으로 로그인해주세요...")
        print("10초 후 자동으로 상세 페이지를 열겠습니다...")
        time.sleep(10)
        
        # 새 탭으로 상세 페이지 열기
        open_new_items_in_browser(driver)
        
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
