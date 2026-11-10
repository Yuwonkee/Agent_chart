"""조건검색 종목 분석 Agent (실행: streamlit run app.py)"""
import datetime as dt
import os

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

import db
import kiwoom
import news_ai

load_dotenv()
st.set_page_config(page_title="조건검색 종목 분석", layout="wide")
st.title("조건검색 종목 분석 Agent")

day = st.date_input("조회 날짜", dt.date.today(), max_value=dt.date.today())
cond = os.getenv("CONDITION_NAME", "")
st.caption(f"조건식: {cond or '(CONDITION_NAME 미설정)'} · 오늘=키움 실시간 조회 후 저장 / 과거=DB 조회")


def collect(day):
    """키움 조건검색 → 종목별 차트/뉴스/분석 → DB 저장. 캔들용 일봉 반환."""
    token = kiwoom.get_token()
    stocks = kiwoom.search_condition(token, cond)
    candles, bar = {}, st.progress(0.0, "종목 조회 중...")
    for i, (code, name) in enumerate(stocks, 1):
        bar.progress(i / len(stocks), f"{name} 분석 중 ({i}/{len(stocks)})")
        daily = kiwoom.get_daily(token, code, day.strftime("%Y%m%d"))
        if not daily:
            continue
        chart = kiwoom.chart_row(daily)
        news = news_ai.get_news(name)
        db.save(day, code, name, chart, news, news_ai.analyze(name, chart, news))
        candles[code] = daily[:60]
    bar.empty()
    return candles


def candle(daily):
    df = pd.DataFrame(daily[::-1])
    df["dt"] = pd.to_datetime(df["dt"])
    fig = go.Figure(go.Candlestick(x=df["dt"], open=df["open"], high=df["high"],
                                   low=df["low"], close=df["close"],
                                   increasing_line_color="red", decreasing_line_color="blue"))
    fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), xaxis_rangeslider_visible=False)
    return fig


if st.button("종목조회", type="primary"):
    try:
        candles = collect(day) if day == dt.date.today() else {}
        rows = db.load(day)
    except KeyError as e:
        st.error(f".env 설정 누락: {e}")
        st.stop()
    except Exception as e:  # DB 연결, 네트워크 오류 등
        st.error(f"오류: {e}")
        st.stop()

    if not rows:
        st.info("저장된 데이터 없음 (과거 날짜는 당일에 조회·저장된 데이터만 볼 수 있음)")
    st.subheader(f"{day} · {len(rows)}종목")

    for r in rows:
        with st.expander(f"{r['name']} ({r['code']})  {float(r['change_rate']):+.2f}%", expanded=True):
            # 1) 차트정보
            st.markdown("**① 차트정보**")
            st.dataframe(pd.DataFrame([{
                "날짜": str(r["dt"]), "종목번호": r["code"], "종목명": r["name"],
                "기준가": f"{r['base_price']:,.0f}", "시작가": f"{r['open_price']:,.0f}",
                "저가": f"{r['low_price']:,.0f}", "고가": f"{r['high_price']:,.0f}",
                "종가": f"{r['close_price']:,.0f}", "등락률(%)": float(r["change_rate"]),
                "거래량": f"{r['volume']:,}",
            }]), hide_index=True, use_container_width=True)
            if r["code"] in candles:
                st.plotly_chart(candle(candles[r["code"]]), use_container_width=True)
            # 2) 동향 및 이슈 (최대 5)
            st.markdown("**② 동향 및 이슈**")
            for i in r["issues"]:
                st.markdown(f"- [{i['content'][:80]}]({i['link']})")
            # 3) 향후 전망
            st.markdown("**③ 분석 / 향후 전망**")
            st.write(r["analysis"])
