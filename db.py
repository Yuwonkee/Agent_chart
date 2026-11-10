"""MariaDB 저장/조회 (조회날짜 key)."""
import os

import pymysql


def _conn():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"), port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"), password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "stock_agent"), charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor, autocommit=True,
    )


def save(dt, code, name, chart, news, analysis):
    """종목 1건의 차트/이슈/분석을 저장 (같은 날짜 재조회 시 덮어씀)."""
    with _conn() as c, c.cursor() as cur:
        cur.execute(
            """INSERT INTO stock_chart (dt, code, name, base_price, open_price, low_price,
                   high_price, close_price, change_rate, volume)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON DUPLICATE KEY UPDATE name=VALUES(name), base_price=VALUES(base_price),
                   open_price=VALUES(open_price), low_price=VALUES(low_price),
                   high_price=VALUES(high_price), close_price=VALUES(close_price),
                   change_rate=VALUES(change_rate), volume=VALUES(volume)""",
            (dt, code, name, chart["base_price"], chart["open_price"], chart["low_price"],
             chart["high_price"], chart["close_price"], chart["change_rate"], chart["volume"]))
        cur.execute("DELETE FROM stock_issue WHERE dt=%s AND code=%s", (dt, code))
        cur.executemany(
            "INSERT INTO stock_issue (dt, code, link, content) VALUES (%s,%s,%s,%s)",
            [(dt, code, n["link"], n["content"]) for n in news])
        cur.execute(
            """INSERT INTO stock_analysis (dt, code, content) VALUES (%s,%s,%s)
               ON DUPLICATE KEY UPDATE content=VALUES(content)""", (dt, code, analysis))


def load(dt):
    """날짜 기준 저장 내용 조회 → [{chart..., issues:[...], analysis}]"""
    with _conn() as c, c.cursor() as cur:
        cur.execute("SELECT * FROM stock_chart WHERE dt=%s ORDER BY change_rate DESC", (dt,))
        charts = cur.fetchall()
        cur.execute("SELECT code, link, content FROM stock_issue WHERE dt=%s ORDER BY id", (dt,))
        issues = cur.fetchall()
        cur.execute("SELECT code, content FROM stock_analysis WHERE dt=%s", (dt,))
        analysis = {r["code"]: r["content"] for r in cur.fetchall()}
    for ch in charts:
        ch["issues"] = [i for i in issues if i["code"] == ch["code"]][:5]
        ch["analysis"] = analysis.get(ch["code"], "")
    return charts
