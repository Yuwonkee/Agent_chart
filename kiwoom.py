"""키움 REST API: 토큰 발급, 조건검색(WebSocket), 일봉차트(ka10081)."""
import json
import os

import requests
from websockets.sync.client import connect


def _hosts():
    if os.getenv("KIWOOM_MOCK", "0") == "1":
        return "https://mockapi.kiwoom.com", "wss://mockapi.kiwoom.com:10000"
    return "https://api.kiwoom.com", "wss://api.kiwoom.com:10000"


def get_token():
    rest, _ = _hosts()
    r = requests.post(f"{rest}/oauth2/token", json={
        "grant_type": "client_credentials",
        "appkey": os.environ["KIWOOM_APPKEY"],
        "secretkey": os.environ["KIWOOM_SECRETKEY"],
    }, timeout=10)
    r.raise_for_status()
    body = r.json()
    if not body.get("token"):
        raise RuntimeError(f"토큰 발급 실패: {body.get('return_msg')}")
    return body["token"]


def _recv(ws, trnm):
    """원하는 trnm 응답이 올 때까지 수신 (PING은 그대로 돌려줌)."""
    while True:
        msg = json.loads(ws.recv(timeout=15))
        if msg.get("trnm") == "PING":
            ws.send(json.dumps(msg))
            continue
        if msg.get("trnm") == trnm:
            if str(msg.get("return_code", "0")) != "0":
                raise RuntimeError(f"{trnm} 실패: {msg.get('return_msg')}")
            return msg


def search_condition(token, cond_name):
    """사용자 조건식(이름)으로 종목 조회 → [(종목코드, 종목명)]"""
    _, ws_host = _hosts()
    with connect(f"{ws_host}/api/dostk/websocket") as ws:
        ws.send(json.dumps({"trnm": "LOGIN", "token": token}))
        _recv(ws, "LOGIN")

        ws.send(json.dumps({"trnm": "CNSRLST"}))  # ka10171 조건식 목록
        conds = _recv(ws, "CNSRLST").get("data") or []
        seq = next((c[0] for c in conds if c[1] == cond_name), None)
        if seq is None:
            raise RuntimeError(f"조건식 '{cond_name}' 없음. 목록: {[c[1] for c in conds]}")

        ws.send(json.dumps({  # ka10172 조건검색 일반조회
            "trnm": "CNSRREQ", "seq": seq, "search_type": "0",
            "stex_tp": "K", "cont_yn": "N", "next_key": "",
        }))
        rows = _recv(ws, "CNSRREQ").get("data") or []
    return [(r["9001"].lstrip("A"), r["302"]) for r in rows]


def _num(v):
    return abs(float(str(v).replace(",", "") or 0))


def get_daily(token, code, base_dt):
    """일봉차트 조회 (base_dt: YYYYMMDD). 최신순 [{dt, open, high, low, close, volume}]"""
    rest, _ = _hosts()
    r = requests.post(f"{rest}/api/dostk/chart", headers={
        "api-id": "ka10081",
        "authorization": f"Bearer {token}",
        "Content-Type": "application/json;charset=UTF-8",
    }, json={"stk_cd": code, "base_dt": base_dt, "upd_stkpc_tp": "1"}, timeout=10)
    r.raise_for_status()
    rows = r.json().get("stk_dt_pole_chart_qry") or []
    return [{
        "dt": x["dt"], "open": _num(x["open_pric"]), "high": _num(x["high_pric"]),
        "low": _num(x["low_pric"]), "close": _num(x["cur_prc"]), "volume": int(_num(x["trde_qty"])),
    } for x in rows]


def chart_row(daily):
    """선택일(최신) 행 → DB 저장용 차트정보. 기준가=전일종가."""
    today, prev = daily[0], daily[1] if len(daily) > 1 else daily[0]
    base = prev["close"]
    rate = round((today["close"] - base) / base * 100, 2) if base else 0
    return {
        "base_price": base, "open_price": today["open"], "low_price": today["low"],
        "high_price": today["high"], "close_price": today["close"],
        "change_rate": rate, "volume": today["volume"],
    }
