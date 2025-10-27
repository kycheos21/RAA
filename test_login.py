#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import logging
import re
import sqlite3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_logging():
    """로깅 설정"""
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_filename = f"login_test_log_{timestamp}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"로그인 테스트 로깅 시작 - 로그 파일: {log_filename}")
    return logger

def parse_address_unit(address, logger):
    """주소에서 동/호수 정보 추출"""
    try:
        # 패턴: "103동 303호" 또는 "103동" 또는 "303호"
        dong_match = re.search(r'(\d+)동', address)
        ho_match = re.search(r'(\d+)호', address)
        
        dong = dong_match.group(1) if dong_match else None
        ho = ho_match.group(1) if ho_match else None
        
        logger.info(f"주소 파싱 결과 - 동: {dong}, 호: {ho}")
        return dong, ho
        
    except Exception as e:
        logger.error(f"주소 파싱 오류: {e}")
        return None, None

def extract_unit_price(driver, logger, dong, ho):
    """동/호수별 AI 추정가 및 공시가 추출"""
    try:
        # 1. 동이 있으면 동 선택
        if dong:
            dong_button = driver.find_element(By.XPATH, f"//button[@data-dongnm='{dong}']")
            # 두 번 클릭
            dong_button.click()
            time.sleep(0.5)
            dong_button.click()
            time.sleep(2)
            logger.info(f"동 {dong} 선택 완료")
        
        # 2. "추정·공시" 탭 클릭
        driver.find_element(By.ID, "clickAsumGongPrice").click()
        time.sleep(2)
        logger.info("추정·공시 탭 클릭 완료")
        
        # 3. 호수가 없으면 해당 물건 처리 안 함
        if not ho:
            logger.warning("호수 정보 없음, 처리 건너뜀")
            return None, None
        
        # 4. 호수 클릭
        ho_element = driver.find_element(By.XPATH, f"//span[@data-honm='{ho}']")
        ho_element.click()
        time.sleep(2)
        logger.info(f"호수 {ho} 클릭 완료")
        
        # 5. 가격 추출
        # 클릭한 호수의 부모 div에서 가격 정보 추출
        parent_div = ho_element.find_element(By.XPATH, "./ancestor::div[contains(@class, 'clickSpan')]")
        price_span = parent_div.find_element(By.XPATH, ".//span[contains(@class, 'hoPrice')]")
        price_text = price_span.text.strip()
        
        logger.info(f"가격 텍스트: '{price_text}'")
        
        # "4,825만\n3,280만" 형식 파싱
        prices = price_text.split('\n')
        ai_price = prices[0].replace('만', '').replace(',', '').strip() if len(prices) > 0 and prices[0] else None
        public_price = prices[1].replace('만', '').replace(',', '').strip() if len(prices) > 1 and prices[1] else None
        
        logger.info(f"파싱된 가격 - AI가: {ai_price}, 공시가: {public_price}")
        return ai_price, public_price
        
    except Exception as e:
        logger.error(f"호별 가격 추출 실패 (동: {dong}, 호: {ho}): {e}")
        return None, None

def login_bdsplanet(driver, logger):
    """부동산플래닛 로그인"""
    try:
        logger.info("부동산플래닛 로그인 시작")
        
        # 간편 로그인 버튼 찾기 및 클릭
        try:
            # 여러 가지 선택자로 시도
            login_selectors = [
                "//a[@class='btns def-bt rpdNeedLogin']",
                "//a[contains(@class, 'rpdNeedLogin')]",
                "//a[contains(text(), '간편 로그인')]",
                "//span[contains(text(), '간편 로그인')]/parent::a"
            ]
            
            login_button = None
            for selector in login_selectors:
                try:
                    login_button = driver.find_element(By.XPATH, selector)
                    logger.info(f"로그인 버튼 발견: {selector}")
                    break
                except:
                    continue
            
            if login_button:
                # JavaScript로 클릭 시도
                driver.execute_script("arguments[0].click();", login_button)
                logger.info("간편 로그인 버튼 클릭 (JavaScript)")
                time.sleep(2)  # 팝업 로딩 대기
            else:
                logger.error("로그인 버튼을 찾을 수 없습니다.")
                return False
                
        except Exception as e:
            logger.error(f"로그인 버튼 클릭 실패: {e}")
            return False
        
        # 팝업이 모달로 열릴 때까지 대기
        wait = WebDriverWait(driver, 10)
        time.sleep(2)  # 팝업 로딩 대기
        logger.info("로그인 팝업이 모달로 열렸습니다.")
        
        # 이메일 입력
        email_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[data-logintype='email']")))
        email_input.clear()
        email_input.send_keys("goodauction24@gmail.com")
        logger.info("이메일 입력 완료")
        
        # 비밀번호 입력
        password_input = driver.find_element(By.CSS_SELECTOR, "input[data-logintype='password']")
        password_input.clear()
        password_input.send_keys("newstart-1017")
        logger.info("비밀번호 입력 완료")
        
        # 로그인 버튼 클릭
        submit_button = driver.find_element(By.CSS_SELECTOR, "a.btns.t23vaWrh18bbabduwz")
        submit_button.click()
        logger.info("로그인 버튼 클릭")
        time.sleep(3)  # 로그인 처리 대기
        
        # 모달 팝업이므로 창 전환 불필요
        logger.info("부동산플래닛 로그인 성공")
        
        # 로그인 후 페이지 새로고침하여 AI 가격 정보 로드
        driver.refresh()
        time.sleep(3)
        logger.info("로그인 후 페이지 새로고침 완료")
        
        return True
        
    except Exception as e:
        logger.error(f"부동산플래닛 로그인 실패: {e}")
        # 혹시 창이 여러개 열려있으면 원래 창으로 돌아가기
        try:
            windows = driver.window_handles
            if len(windows) > 1:
                driver.switch_to.window(windows[0])
        except:
            pass
        return False

def test_login():
    """로그인 테스트"""
    logger = setup_logging()
    
    print("부동산플래닛 로그인 테스트를 시작합니다.")
    print("주의: Chrome 브라우저가 자동으로 열립니다.")
    
    # Chrome 드라이버 설정
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 실제 부동산 데이터 페이지로 이동 (로그인 버튼이 있는 페이지)
        test_url = "https://www.bdsplanet.com/map/realprice_map/eAY9e2BehFG/N/A/1/60.ytp"
        driver.get(test_url)
        time.sleep(5)
        
        logger.info(f"현재 페이지 제목: {driver.title}")
        logger.info(f"현재 URL: {driver.current_url}")
        
        # 페이지 소스에서 로그인 관련 텍스트 확인
        page_source = driver.page_source
        if "간편 로그인" in page_source:
            logger.info("페이지에서 '간편 로그인' 텍스트 발견")
        else:
            logger.warning("페이지에서 '간편 로그인' 텍스트를 찾을 수 없음")
        
        if "rpdNeedLogin" in page_source:
            logger.info("페이지에서 'rpdNeedLogin' 클래스 발견")
        else:
            logger.warning("페이지에서 'rpdNeedLogin' 클래스를 찾을 수 없음")
        
        # AI 추정가 영역 확인
        if "asum-gong-view" in page_source:
            logger.info("페이지에서 'asum-gong-view' 클래스 발견")
        else:
            logger.warning("페이지에서 'asum-gong-view' 클래스를 찾을 수 없음")
        
        # 오늘 보지 않기 팝업 닫기
        try:
            # 오늘 하루 보지 않기 버튼 클릭
            today_hide_button = driver.find_element(By.XPATH, "//a[@class='adPop__utilArea__todayHide']")
            today_hide_button.click()
            logger.info("오늘 하루 보지 않기 클릭 완료")
            time.sleep(1)
        except:
            try:
                # 일반 팝업 닫기 버튼 클릭
                popup_close_button = driver.find_element(By.XPATH, "//a[@class='adPop__utilArea__popClose ui_pop_close']")
                popup_close_button.click()
                logger.info("팝업 닫기 버튼 클릭 완료")
                time.sleep(1)
            except:
                logger.info("팝업이 없거나 이미 닫혀있음")
        
        # 로그인 시도
        if login_bdsplanet(driver, logger):
            logger.info("로그인 성공!")
            print("✅ 로그인 성공!")
            
            # 로그인 후 AI 가격 영역 확인
            try:
                ai_elements = driver.find_elements(By.XPATH, "//div[@class='asum-gong-view']//dd[@class='asumPrice']")
                if ai_elements:
                    ai_text = ai_elements[0].text.strip()
                    logger.info(f"AI 추정가 발견: '{ai_text}'")
                    print(f"AI 추정가: {ai_text}")
                else:
                    logger.warning("AI 추정가 영역을 찾을 수 없음")
            except Exception as e:
                logger.warning(f"AI 가격 확인 실패: {e}")
            
            # valid_data에서 주소 정보 가져오기
            logger.info("호별 가격 추출 시작")
            conn = sqlite3.connect('tankauction.db')
            cursor = conn.cursor()
            cursor.execute('SELECT tid, address FROM valid_data')
            addresses = cursor.fetchall()
            conn.close()
            
            logger.info(f"총 {len(addresses)}개의 물건에서 호별 가격 추출")
            
            # 각 물건별 호별 가격 추출
            for i, (tid, address) in enumerate(addresses):
                try:
                    print(f"\n[{i+1}/{len(addresses)}] 호별 가격 추출: tid={tid}")
                    logger.info(f"tid: {tid}, 주소: {address}")
                    
                    dong, ho = parse_address_unit(address, logger)
                    
                    if not ho:
                        logger.warning(f"tid: {tid} - 호수 정보 없음, 건너뜀")
                        print(f"❌ 호수 정보 없음: tid={tid}")
                        continue
                    
                    ai_price, public_price = extract_unit_price(driver, logger, dong, ho)
                    
                    if ai_price or public_price:
                        # DB 업데이트
                        conn = sqlite3.connect('tankauction.db')
                        cursor = conn.cursor()
                        cursor.execute('''
                            UPDATE valid_data 
                            SET unit_ai_price = ?, unit_public_price = ? 
                            WHERE tid = ?
                        ''', (ai_price, public_price, tid))
                        conn.commit()
                        conn.close()
                        logger.info(f"tid: {tid} - AI가: {ai_price}만, 공시가: {public_price}만")
                        print(f"✅ 성공: tid={tid}, AI가: {ai_price}만, 공시가: {public_price}만")
                    else:
                        logger.warning(f"tid: {tid} - 가격 추출 실패")
                        print(f"❌ 가격 추출 실패: tid={tid}")
                    
                    # 다음 물건 처리를 위해 잠시 대기
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"tid: {tid} 처리 중 오류: {e}")
                    print(f"❌ 오류 발생: tid={tid}, {e}")
                    continue
                
        else:
            logger.error("로그인 실패!")
            print("❌ 로그인 실패!")
        
        print("\n호별 가격 추출 완료. 60초 후 종료됩니다.")
        time.sleep(60)
        
    finally:
        # driver.quit() 제거 - 브라우저를 열어둠
        pass

if __name__ == "__main__":
    test_login()
