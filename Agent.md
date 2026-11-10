# 조건검색 종목 분석 Agent

## 업무
캘린더에서 날짜 선택 → **[종목조회]** → 키움 사용자 조건식으로 종목 조회 → 종목별 차트정보 / 동향·이슈 / 향후 전망을 보여준다.
결과는 조회날짜를 key로 MariaDB에 저장하고, 화면은 저장된 내용을 다시 조회해서 보여준다.

## 처리 흐름
| 단계 | 내용 | 파일 |
|---|---|---|
| 1 | 키움 토큰 발급 → 조건식 목록(ka10171) → 조건검색(ka10172) → 종목별 일봉(ka10081) | `kiwoom.py` |
| 2 | 종목명으로 네이버 뉴스 최신 5건 수집 → Claude 구독(`claude -p`)으로 최근 동향·향후 전망 분석 | `news_ai.py` |
| 3 | 차트/이슈/분석을 날짜 key로 저장 (같은 날짜 재조회 시 덮어씀) | `db.py` |
| 4 | DB에서 날짜로 조회 → 종목별 표시 | `app.py` |

- **오늘 날짜**: 1→2→3→4 실행 (키움 조건검색은 현재 시점만 지원)
- **과거 날짜**: 4만 실행 (DB에 저장된 데이터 조회)

## 화면 순서 (종목별)
1. 차트정보 표 (+ 오늘 조회 시 최근 60일 캔들)
2. 동향 및 이슈: 링크 포함 최대 5개
3. 분석 / 향후 전망

## 저장 테이블 (`schema.sql`)
| 테이블 | 컬럼 |
|---|---|
| `stock_chart` | 날짜, 종목번호, 종목명, 기준가(전일종가), 시작가, 저가, 고가, 종가, 전날대비등락률, 거래량 |
| `stock_issue` | 날짜, 종목번호, 링크주소, 내용 |
| `stock_analysis` | 날짜, 종목번호, 분석내용 |

## 실행 (Windows, 64비트 Python)
```powershell
# 최초 1회: Claude Code 설치 후 `claude` 실행 → 구독 계정 로그인
irm https://claude.ai/install.ps1 | iex

py -3 -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # 키움/네이버 키, 조건식 이름, DB 정보 입력
mysql -u root -p -e "source schema.sql"
streamlit run app.py
```

## 참고
- 조건식은 영웅문(HTS)에서 미리 저장하고, 그 이름을 `.env`의 `CONDITION_NAME`에 입력
- 분석은 Claude 구독 사용량에서 차감됨 (종목당 1회 호출)
- 분석은 참고용이며 투자 권유가 아님
