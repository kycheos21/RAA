# Persona01.md
## 페르소나1: 안전소액경매 스크래핑 방법

### 페르소나1 : 안전소액경매
1. 경매검색 메뉴 선택
2. 물건종류 > 아파트 선택
3. 유찰 > 2 - 2 선택 (2회 유찰)
4. 최저가격 > 4천만원 이하
5. 특수조건 > 위험조건 모두 제외

### 스크래핑, 매물 선별, 엑셀 전송 방법
#### 1.탱크옥션
1. 경매검색 > 즐겨쓰는 검색열기 > 안전소액경매
2. 목록수 > 100
3. 리스트 스크래핑
4. 행클릭
5. 주요정보 스크래핑 
   - 사건번호 : //div[@class="fleft f28 bold_900"]//span[@class="bold" and contains(text(), "경매")]/following-sibling::text()[1]
   - 주소 : //div[contains(@style, "padding:5px 0 10px")]//span[@class="bold"]
   - 대지권, 건물면적, 감정가, 최저가 : 
     * 대지권: //table[@class="Btbl_list"]//th[contains(text(), "대지권")]/following-sibling::td[1]
     * 건물면적: //table[@class="Btbl_list"]//th[contains(text(), "건물면적")]/following-sibling::td[1]
     * 감정가: //table[@class="Btbl_list"]//th[contains(text(), "감정가")]/following-sibling::td//span[@class="selectedNumType"]
     * 최저가: //table[@class="Btbl_list"]//th[contains(text(), "최저가")]/following-sibling::td//span[@class="selectedNumType"]
   - 유찰횟수 : //table[@class="tbl_list"]//tr[contains(@class, "hist_tr")]//td[contains(text(), "유찰")]의 개수 
4. 새창의 국토부 실거래가 테이블 스크래핑
   - 테이블 ID: qtLst
   - 매매 테이블 선택: //table[@id="qtLst"]//div[contains(text(), "매매(만원)")]/following-sibling::table
   - 스크래핑 데이터: 년월, 최저가, 평균가, 최고가, 건수
6. 현재를 기준으로 1년간 매매건수가 0건 이면 아래 프로세스 중지.
8. valid_data table에 추가 : tid, 사건번호, 주소, 대지권, 건물면적, 감정가, 최저가, 유찰횟수, 1년간 거래 건수 

7. 네이버부동산 클릭

#### 2.네이버부동산
1. 네이버부동산에서 해당물건 클릭
2. 전체면적 > 해당면적 클릭 (분양평수 계산 필요)
3. 전체거래방식 > 매매
4. 리스트 스크래핑핑
5. 매물 개수, 매물최저가, 매물 최저가의 층수

#### 3.탱크옥션
1. 부동산플래닛 클릭


<!-- 
#### 4.부동산플래닛 
1. 팝업끄기
2. 전용평수 > 해당전용평수 클릭
3. 실거래가 더보기 클릭 > 1년치 실거래가 스크래핑
    - 실거래 개수, 실거래 최저가, 실거래 최저가 층수, 실거래 평균가
4. 거래지수 (실거래 개수 / 매물 개수) > 0.7 이상인 경우만 후속 조치
5. 최저매각가격 < 실거래 평균가 인 경우만 후속 조치
6. 간편로그인 클릭 > 이메일 : 부동산플래닛 이메일 > 비밀번호 : 부동산플래닛 비밀번호 > 로그인
7. 동 클릭 > 더보기 클릭 > 해당 호수 클릭 > AI 추정가
-->


#### 5.탱크옥션
1. 관심 > 분류 > 안전소액경매 > 실거래 개수, 실거래 수, 매물 수, 매물 최저가, 실거래 최저가, AI 추정가 > 저장하기
2. 엑셀 생성 > 엑셀에 각셀에 스크래핑 정보 입력 > 엑셀 저장
3. 엑셀 첨부하여 카톡에 전송

---

*페르소나별 스크래핑 방법을 기록할 예정*

