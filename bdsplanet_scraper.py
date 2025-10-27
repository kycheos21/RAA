# -*- coding: utf-8 -*-
"""
부동산플래닛 스크래퍼
- valid_data에서 부동산플래닛 링크 추출
- 평수별 실거래 데이터 스크래핑
- 로그인 후 호별 AI 추정가/공시가 추출
"""

import sqlite3
import time
import logging
import sys
import re
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_logging():
    """로깅 설정"""
    log_filename = f"bdsplanet_test_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"부동산플래닛 테스트 로깅 시작 - 로그 파일: {log_filename}")
    return logger

def get_bdsplanet_links_from_db(logger):
    """valid_data에서 부동산플래닛 링크 가져오기"""
    logger.info("데이터베이스에서 부동산플래닛 링크 조회 시작")
    conn = sqlite3.connect('tankauction.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT tid, building_area, bdsplanet_link, address FROM valid_data WHERE bdsplanet_link IS NOT NULL')
    links = cursor.fetchall()
    
    conn.close()
    
    logger.info(f"부동산플래닛 링크 {len(links)}개 발견")
    for tid, building_area, link, address in links:
        logger.info(f"tid: {tid}, 건물면적: {building_area}, 주소: {address}, 링크: {link}")
    
    return links

def update_valid_data_with_transaction_info(logger, tid, transaction_data, building_area_pyung=None):
    """valid_data에 실거래 정보 업데이트"""
    try:
        conn = sqlite3.connect('tankauction.db')
        cursor = conn.cursor()
        
        # 실거래 데이터가 있으면 업데이트
        if transaction_data:
            min_transaction = transaction_data['min_transaction']
            max_transaction = transaction_data['max_transaction']
            avg_price = transaction_data['avg_price']
            transaction_count = transaction_data['transaction_count']
            
            # JSON 형식으로 데이터 저장
            min_price_json = json.dumps({
                'price': min_transaction['price'],
                'floor': min_transaction['floor'],
                'date': min_transaction['date']
            }, ensure_ascii=False)
            
            max_price_json = json.dumps({
                'price': max_transaction['price'],
                'floor': max_transaction['floor'],
                'date': max_transaction['date']
            }, ensure_ascii=False)
            
            # 새로운 컬럼에 실거래 정보 저장 (평수 정보 포함)
            cursor.execute('''
                UPDATE valid_data 
                SET real_estate_min_price = ?, 
                    real_estate_max_price = ?, 
                    real_estate_avg_price = ?,
                    building_area_pyung = ?,
                    yearly_transaction_count = ?,
                    created_at = CURRENT_TIMESTAMP
                WHERE tid = ?
            ''', (min_price_json, max_price_json, str(avg_price), str(building_area_pyung) if building_area_pyung else None, transaction_count, tid))
            
            logger.info(f"실거래 정보 업데이트 완료 - tid: {tid}")
            logger.info(f"  최저가: {min_transaction['price']:,}만원 - {min_transaction['floor']} ({min_transaction['date']})")
            logger.info(f"  최고가: {max_transaction['price']:,}만원 - {max_transaction['floor']} ({max_transaction['date']})")
            logger.info(f"  평균가: {avg_price:,}만원")
            logger.info(f"  평수: {building_area_pyung}평" if building_area_pyung else "  평수: 정보 없음")
            logger.info(f"  거래건수: {transaction_count}건")
        else:
            logger.warning(f"실거래 데이터가 없어서 업데이트하지 않음 - tid: {tid}")
            
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"실거래 정보 업데이트 오류 - tid: {tid}, 오류: {e}")
        return False

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
        
        # 4. 호수 클릭 (더보기 버튼 처리 포함)
        
        # Step 1: 더보기 버튼이 있으면 무조건 클릭
        try:
            # 확장된 XPath 선택자들로 더보기 버튼 찾기
            more_selectors = [
                "//a[@class='more']//span[@class='moretxt']",  # 정확한 매치
                "//a[@class='more']",  # 정확한 클래스
                "//span[@class='moretxt']",  # 정확한 클래스
                "//a[contains(@class, 'more')]//span[@class='moretxt']",  # 부분 매치
                "//a[contains(@class, 'more')]//span[contains(@class, 'moretxt')]",  # 부분 매치
                "//a[contains(@class, 'more')]",  # 부분 매치
                "//span[contains(@class, 'moretxt')]",  # 부분 매치
                "//span[contains(text(), '더보기')]",  # 텍스트로 찾기
                "//a[contains(text(), '더보기')]",  # 링크 텍스트로 찾기
                "//span[text()='더보기']",  # 정확한 텍스트
                "//a[@href='#' and contains(@class, 'more')]",  # href 조합
                "//a[contains(@class, 'more')]/span[@class='moretxt']",  # 부모-자식 관계
                "//a[contains(@class, 'more')]/span",  # 부모-자식 관계
                "//*[contains(@class, 'more')]//*[contains(text(), '더보기')]",  # 유연한 패턴
                "//a[contains(@class, 'more')]//*[contains(text(), '더보기')]",  # 유연한 패턴
                "//span[contains(text(), '더 보기')]",  # 공백 포함
                "//a[contains(@class, 'more') and not(@disabled)]",  # 클릭 가능성 확인
            ]
            
            more_button = None
            for i, selector in enumerate(more_selectors):
                try:
                    more_button = driver.find_element(By.XPATH, selector)
                    if more_button and more_button.is_displayed():
                        logger.info(f"더보기 버튼 발견 (XPath {i+1}): {selector}")
                        break
                except:
                    continue
            
            if more_button:
                driver.execute_script("arguments[0].click();", more_button)
                time.sleep(2)
                logger.info("더보기 버튼 클릭 완료")
            else:
                logger.info("더보기 버튼이 없거나 이미 펼쳐진 상태")
        except Exception as e:
            logger.info(f"더보기 버튼 처리 중 오류: {e}")
        
        # Step 2: 호수 찾기 및 클릭
        try:
            ho_element = driver.find_element(By.XPATH, f"//span[@data-honm='{ho}']")
            
            # 일반 클릭 먼저 시도
            try:
                ho_element.click()
                logger.info(f"호수 {ho} 클릭 완료")
            except:
                # 실패하면 JavaScript 클릭
                driver.execute_script("arguments[0].click();", ho_element)
                logger.info(f"호수 {ho} 클릭 완료 (JS)")
            
            time.sleep(2)
            
        except Exception as e:
            logger.warning(f"호수 {ho}를 찾을 수 없습니다: {e}")
            return None, None
        
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

def convert_m2_to_pyung(m2_str):
    """제곱미터를 평수로 변환"""
    try:
        # "60㎡" → 60.0 추출
        match = re.search(r'([\d.]+)', m2_str)
        if match:
            m2 = float(match.group(1))
            pyung = m2 / 3.3058
            return round(pyung, 2)
        return None
    except Exception as e:
        return None

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
        return False

def close_popup(driver, logger):
    """팝업 광고 닫기 또는 오늘 하루 보지 않기"""
    try:
        # 먼저 "오늘 하루 보지 않기" 버튼 찾기
        today_hide = driver.find_element(By.XPATH, "//a[@class='adPop__utilArea__todayHide']")
        today_hide.click()
        logger.info("오늘 하루 보지 않기 클릭 완료")
        time.sleep(1)  # 팝업이 닫힐 때까지 대기
        return True
    except Exception as e:
        logger.info(f"오늘 하루 보지 않기 버튼이 없음: {e}")
        
        # "오늘 하루 보지 않기"가 없으면 일반 닫기 버튼 시도
        try:
            popup_close = driver.find_element(By.XPATH, "//a[@class='adPop__utilArea__popClose ui_pop_close']")
            popup_close.click()
            logger.info("팝업 광고 닫기 완료")
            time.sleep(1)  # 팝업이 닫힐 때까지 대기
            return True
        except Exception as e2:
            logger.info(f"팝업 광고가 없거나 이미 닫혀있음: {e2}")
            return False

def click_area_dropdown(driver, logger):
    """전용평수 드롭다운 클릭"""
    try:
        # 전용평수 선택 박스 찾기 및 클릭
        dropdown = driver.find_element(By.XPATH, "//div[@class='this']//div[@data-dan-toggle-con='rpTopSelect']")
        dropdown.click()
        logger.info("전용평수 드롭다운 클릭 완료")
        time.sleep(2)  # 드롭다운 열릴 때까지 대기
        return True
    except Exception as e:
        logger.warning(f"전용평수 드롭다운 클릭 실패: {e}")
        return False

def find_and_click_similar_area(driver, logger, target_pyung):
    """유사 평수 찾기 및 클릭"""
    try:
        # 모든 평수 옵션 찾기
        area_elements = driver.find_elements(By.XPATH, "//a[contains(@class, 'tac-box')][@data-area]")
        
        if not area_elements:
            logger.warning("평수 옵션을 찾을 수 없습니다")
            return False
        
        closest_element = None
        min_diff = float('inf')
        
        for i, element in enumerate(area_elements):
            try:
                area_m2 = float(element.get_attribute('data-area'))
                area_pyung = area_m2 / 3.3058
                diff = abs(area_pyung - target_pyung)
                
                if diff < min_diff:
                    min_diff = diff
                    closest_element = element
            except Exception as e:
                logger.warning(f"평수 옵션 {i+1} 처리 오류: {e}")
                continue
        
        if closest_element:
            closest_element.click()
            logger.info(f"유사 평수 클릭 완료: {closest_element.text}")
            time.sleep(3)  # 페이지 로딩 대기
            return True
        else:
            logger.warning("클릭할 평수 옵션을 찾을 수 없습니다")
            return False
            
    except Exception as e:
        logger.error(f"유사 평수 찾기 및 클릭 오류: {e}")
        return False

def scrape_bdsplanet_page(driver, logger, tid, building_area, bdsplanet_link, address, is_logged_in=False):
    """부동산플래닛 페이지 스크래핑"""
    try:
        logger.info(f"부동산플래닛 페이지 스크래핑 시작 - tid: {tid}")
        logger.info(f"건물면적: {building_area}")
        logger.info(f"접속 URL: {bdsplanet_link}")
        
        # 부동산플래닛 페이지로 이동
        driver.get(bdsplanet_link)
        time.sleep(5)  # 페이지 로딩 대기
        
        # 페이지 제목
        page_title = driver.title
        logger.info(f"페이지 제목: {page_title}")
        
        # 현재 URL
        current_url = driver.current_url
        logger.info(f"현재 URL: {current_url}")
        
        # 팝업 광고 닫기
        close_popup(driver, logger)
        
        # 건물면적을 평수로 변환
        target_pyung = convert_m2_to_pyung(building_area)
        if target_pyung:
            logger.info(f"타겟 평수: {target_pyung}평")
            
            # 전용평수 드롭다운 클릭
            if click_area_dropdown(driver, logger):
                # 유사 평수 찾아서 클릭
                if find_and_click_similar_area(driver, logger, target_pyung):
                    logger.info(f"평수 선택 완료: {target_pyung}평")
                else:
                    logger.warning("평수 선택 실패")
            else:
                logger.warning("전용평수 드롭다운 클릭 실패")
        else:
            logger.warning(f"건물면적 변환 실패: {building_area}")
        
        # 실거래 정보표 로딩 완료 대기
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_all_elements_located((By.XPATH, "//tbody//tr[@class='tr-click-ef']")))
            time.sleep(3)  # 모든 행이 완전히 로드될 때까지 추가 대기
            logger.info("실거래 테이블 로딩 완료")
        except Exception as e:
            logger.warning(f"실거래 정보표 로딩 대기 중 오류: {e}")
        
        # 실거래 정보표에서 최근 1년간 데이터 분석
        try:
            
            # 실거래 정보표 찾기
            transaction_rows = driver.find_elements(By.XPATH, "//tbody//tr[@class='tr-click-ef']")
            
            if transaction_rows:
                from datetime import datetime, timedelta
                
                # 최근 1년 날짜 계산
                one_year_ago = datetime.now() - timedelta(days=365)
                recent_transactions = []
                
                for row_idx, row in enumerate(transaction_rows):
                    try:
                        # 날짜 추출 (td01)
                        date_cell = row.find_element(By.XPATH, ".//td[contains(@class, 'td01')]")
                        date_text = date_cell.text.strip()
                        
                        # 가격 추출 (여러 전략 시도)
                        price_text = None
                        try:
                            # 전략 1: td03의 paybold
                            price_cell = row.find_element(By.XPATH, ".//td[contains(@class, 'td03')]//span[@class='paybold']")
                            price_text = price_cell.text.strip()
                        except:
                            try:
                                # 전략 2: td03 전체 텍스트에서 추출
                                price_cell = row.find_element(By.XPATH, ".//td[contains(@class, 'td03')]")
                                price_text = price_cell.text.strip()
                            except Exception as e:
                                logger.warning(f"행 {row_idx+1} 가격 추출 실패: {e}")
                                continue  # 가격 정보가 없는 행은 건너뛰고 다음 행으로
                        
                        # 층수 추출 (td04)
                        floor_cell = row.find_element(By.XPATH, ".//td[contains(@class, 'td04')]")
                        floor_text = floor_cell.text.strip()
                        
                        # 날짜 파싱 (25.08.29 형식)
                        if '.' in date_text:
                            year_month_day = date_text.split('.')
                            if len(year_month_day) == 3:
                                year = 2000 + int(year_month_day[0])
                                month = int(year_month_day[1])
                                day = int(year_month_day[2])
                                transaction_date = datetime(year, month, day)
                                
                                # 1년 이내 거래인지 확인
                                if transaction_date >= one_year_ago:
                                    # 가격에서 숫자만 추출
                                    price_match = re.search(r'([\d,]+)', price_text)
                                    if price_match:
                                        price = int(price_match.group(1).replace(',', ''))
                                        recent_transactions.append({
                                            'date': date_text,
                                            'price': price,
                                            'floor': floor_text,
                                            'datetime': transaction_date
                                        })
                            
                    except Exception as e:
                        logger.warning(f"행 {row_idx+1} 처리 오류: {e}")
                        continue
                
                # 최근 1년간 거래 분석
                transaction_data = None
                if recent_transactions:
                    # 가격 정렬
                    prices = [t['price'] for t in recent_transactions]
                    prices.sort()
                    
                    min_price = prices[0]
                    max_price = prices[-1]
                    avg_price = sum(prices) / len(prices)
                    
                    # 최저가와 최고가의 층수 찾기
                    min_transaction = next(t for t in recent_transactions if t['price'] == min_price)
                    max_transaction = next(t for t in recent_transactions if t['price'] == max_price)
                    
                    logger.info("최근 1년간 실거래 분석 결과:")
                    logger.info(f"  최저금액: {min_price:,}만원 - {min_transaction['floor']} ({min_transaction['date']})")
                    logger.info(f"  최고금액: {max_price:,}만원 - {max_transaction['floor']} ({max_transaction['date']})")
                    logger.info(f"  평균가격: {avg_price:,.0f}만원")
                    logger.info(f"  거래건수: {len(recent_transactions)}건")
                    
                    # 실거래 데이터 저장
                    transaction_data = {
                        'min_transaction': min_transaction,
                        'max_transaction': max_transaction,
                        'avg_price': int(avg_price),
                        'transaction_count': len(recent_transactions),
                        'recent_transactions': recent_transactions
                    }
                else:
                    logger.warning("최근 1년간 실거래 데이터가 없습니다.")
                
        except Exception as e:
            logger.warning(f"실거래 정보 분석 오류: {e}")
        
        # 호별 가격 추출 (로그인된 상태에서만)
        if is_logged_in and address:
            logger.info(f"호별 가격 추출 시작 - tid: {tid}")
            dong, ho = parse_address_unit(address, logger)
            
            if ho:
                ai_price, public_price = extract_unit_price(driver, logger, dong, ho)
                
                # DB 업데이트
                if ai_price or public_price:
                    conn = sqlite3.connect('tankauction.db')
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE valid_data 
                        SET unit_ai_price = ?, unit_public_price = ? 
                        WHERE tid = ?
                    ''', (ai_price, public_price, tid))
                    conn.commit()
                    conn.close()
                    logger.info(f"호별 가격 저장 완료 - tid: {tid}, AI가: {ai_price}만, 공시가: {public_price}만")
                else:
                    logger.warning(f"호별 가격 추출 실패 - tid: {tid}")
            else:
                logger.warning(f"호수 정보 없음 - tid: {tid}, 주소: {address}")
        
        logger.info(f"부동산플래닛 페이지 스크래핑 완료 - tid: {tid}")
        return transaction_data
        
    except Exception as e:
        logger.error(f"부동산플래닛 페이지 스크래핑 오류 - tid: {tid}, 오류: {e}")
        return False

def scrape_bdsplanet_details(driver, logger):
    """부동산플래닛 상세 정보 스크래핑 (실거래 + AI 추정가)"""
    logger.info("부동산플래닛 상세 스크래핑 시작")
    
    # 데이터베이스에서 부동산플래닛 링크 가져오기
    links = get_bdsplanet_links_from_db(logger)
    
    if not links:
        logger.info("테스트할 부동산플래닛 링크가 없습니다.")
        return False
    
    logger.info(f"총 {len(links)}개의 부동산플래닛 링크를 테스트합니다.")
    
    success_count = 0
    fail_count = 0
    login_success = False
    
    for i, (tid, building_area, bdsplanet_link, address) in enumerate(links):
        try:
            print(f"\n[{i+1}/{len(links)}] 부동산플래닛 테스트: tid={tid}")
            print(f"건물면적: {building_area}")
            print(f"주소: {address}")
            print(f"링크: {bdsplanet_link}")
            
            # 건물면적을 평수로 변환
            target_pyung = convert_m2_to_pyung(building_area)
            
            # 부동산플래닛 페이지 스크래핑 (주소 정보 전달)
            transaction_data = scrape_bdsplanet_page(driver, logger, tid, building_area, bdsplanet_link, address, login_success)
            
            if transaction_data:
                success_count += 1
                print(f"✅ 성공: tid={tid}")
                
                # 실거래 데이터를 valid_data에 저장
                update_valid_data_with_transaction_info(logger, tid, transaction_data, target_pyung)
                
                # 첫 번째 레코드 처리 완료 후 로그인 시도
                if i == 0 and not login_success:
                    logger.info("첫 번째 레코드 처리 완료, 로그인을 시도합니다.")
                    login_success = login_bdsplanet(driver, logger)
                    if login_success:
                        logger.info("로그인 성공, 첫 번째 레코드에서 호별 가격을 추출합니다.")
                        
                        # 첫 번째 레코드에서 호별 가격 추출
                        logger.info(f"첫 번째 레코드 호별 가격 추출 시작 - tid: {tid}")
                        dong, ho = parse_address_unit(address, logger)
                        
                        if ho:
                            ai_price, public_price = extract_unit_price(driver, logger, dong, ho)
                            
                            # DB 업데이트
                            if ai_price or public_price:
                                conn = sqlite3.connect('tankauction.db')
                                cursor = conn.cursor()
                                cursor.execute('''
                                    UPDATE valid_data 
                                    SET unit_ai_price = ?, unit_public_price = ? 
                                    WHERE tid = ?
                                ''', (ai_price, public_price, tid))
                                conn.commit()
                                conn.close()
                                logger.info(f"첫 번째 레코드 호별 가격 저장 완료 - tid: {tid}, AI가: {ai_price}만, 공시가: {public_price}만")
                            else:
                                logger.warning(f"첫 번째 레코드 호별 가격 추출 실패 - tid: {tid}")
                        else:
                            logger.warning(f"첫 번째 레코드 호수 정보 없음 - tid: {tid}, 주소: {address}")
                    else:
                        logger.warning("로그인 실패, AI 가격 추출을 건너뜁니다.")
            else:
                fail_count += 1
                print(f"❌ 실패: tid={tid}")
            
            # 다음 테스트를 위해 잠시 대기
            time.sleep(2)
            
        except Exception as e:
            fail_count += 1
            logger.error(f"테스트 오류 (tid={tid}): {e}")
            print(f"❌ 오류 발생 (tid={tid}): {e}")
            continue
    
    logger.info(f"부동산플래닛 테스트 완료 - 성공: {success_count}개, 실패: {fail_count}개")
    print(f"\n부동산플래닛 테스트 완료 - 성공: {success_count}개, 실패: {fail_count}개")
    
    return login_success

def main():
    """메인 함수"""
    # 로깅 설정
    logger = setup_logging()
    
    print("부동산플래닛 스크래퍼를 시작합니다.")
    print("주의: Chrome 브라우저가 자동으로 열립니다.")
    
    # Chrome 드라이버 설정
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # 부동산플래닛 상세 스크래핑
        scrape_bdsplanet_details(driver, logger)
        
        print("\n스크래핑 완료. 브라우저를 수동으로 닫아주세요.")
        
    finally:
        # driver.quit() 제거 - 브라우저를 열어둠
        pass

if __name__ == "__main__":
    main()
