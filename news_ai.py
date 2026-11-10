"""네이버 뉴스 검색(최대 5건) + Claude 동향/전망 분석."""
import html
import os
import re

import anthropic
import requests


def _clean(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def get_news(name, n=5):
    """종목명으로 최신 뉴스 검색 → [{link, content}]"""
    r = requests.get("https://openapi.naver.com/v1/search/news.json", headers={
        "X-Naver-Client-Id": os.environ["NAVER_CLIENT_ID"],
        "X-Naver-Client-Secret": os.environ["NAVER_CLIENT_SECRET"],
    }, params={"query": f"{name} 주가", "display": n, "sort": "date"}, timeout=10)
    r.raise_for_status()
    return [{
        "link": it.get("originallink") or it["link"],
        "content": f"{_clean(it['title'])} - {_clean(it['description'])}",
    } for it in r.json().get("items", [])[:n]]


def analyze(name, chart, news):
    """차트정보 + 뉴스로 최근 동향 요약과 향후 전망을 짧게 작성."""
    news_txt = "\n".join(f"- {x['content']}" for x in news) or "- 뉴스 없음"
    prompt = (
        f"종목: {name}\n"
        f"차트: 기준가 {chart['base_price']:,.0f}, 시가 {chart['open_price']:,.0f}, "
        f"고가 {chart['high_price']:,.0f}, 저가 {chart['low_price']:,.0f}, "
        f"종가 {chart['close_price']:,.0f}, 등락률 {chart['change_rate']}%, 거래량 {chart['volume']:,}\n"
        f"최근 뉴스:\n{news_txt}\n\n"
        "위 정보만으로 한국어로 간결하게 작성하라. 형식:\n"
        "[최근 동향] 2~3줄\n[향후 전망] 2~3줄 (긍정/부정 요인 포함)\n"
        "투자 권유가 아닌 참고용 분석임을 전제로 한다."
    )
    client = anthropic.Anthropic()
    resp = client.beta.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-opus-5-5"),
        max_tokens=2000,
        output_config={"effort": "low"},  # 짧은 요약 작업 → 토큰 최소화
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",  # 안전 필터 거절 시 서버가 다른 모델로 재시도
        messages=[{"role": "user", "content": prompt}],
    )
    if resp.stop_reason == "refusal":
        return "분석 불가 (모델 응답 거절)"
    return "".join(b.text for b in resp.content if b.type == "text").strip()
