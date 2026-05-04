"""
StockExpert 数据库读取层 — 溯源 Dashboard 查询
"""
import sqlite3, json
from datetime import date

DB_PATH = "/mnt/c/Users/WINGO/Documents/WorkSpace/trading-system/data/stockexpert.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_fetch_status(trade_date: str, stage: str = None) -> list:
    """今日各字段采集状态（核心溯源查询）"""
    conn = get_conn()
    query = """
        SELECT
            field_group,
            field_name,
            source,
            source_detail,
            status,
            CASE status
                WHEN 'success' THEN '✅'
                WHEN 'failed'  THEN '🔴'
                WHEN 'partial' THEN '⚠️'
                ELSE '❓'
            END AS icon,
            value,
            error_message,
            fetched_at
        FROM field_fetch_log
        WHERE trade_date = ?
    """
    params = [trade_date]
    if stage:
        query += " AND stage = ?"
        params.append(stage)
    query += " ORDER BY field_group, field_name"

    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_coverage(trade_date: str = None) -> list:
    """字段覆盖率视图"""
    conn = get_conn()
    query = "SELECT * FROM v_field_coverage"
    if trade_date:
        query += " WHERE trade_date = ?"
        rows = conn.execute(query, [trade_date]).fetchall()
    else:
        rows = conn.execute(query).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_index_quotes(trade_date: str) -> list:
    """指数行情"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM index_quotes WHERE trade_date = ? ORDER BY index_code",
        [trade_date]
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_market_sentiment(trade_date: str) -> dict:
    """市场情绪"""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM market_sentiment WHERE trade_date = ?", [trade_date]
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_board_metrics(trade_date: str) -> dict:
    """连板炸板"""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM board_metrics WHERE trade_date = ?", [trade_date]
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_north_flow(trade_date: str) -> dict:
    """北向资金"""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM north_flow WHERE trade_date = ?", [trade_date]
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_field_history(field_name: str, limit: int = 30) -> list:
    """某字段历史采集记录"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT trade_date, stage, value, status, source, error_message
        FROM field_fetch_log
        WHERE field_name = ?
        ORDER BY trade_date DESC, fetched_at DESC
        LIMIT ?
    """, [field_name, limit]).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_sources() -> list:
    """所有数据源统计"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT field_name, source, source_detail,
               COUNT(*) AS total,
               SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) AS ok,
               ROUND(1.0*SUM(CASE WHEN status='success' THEN 1 ELSE 0 END)/COUNT(*)*100,1) AS rate
        FROM field_fetch_log
        GROUP BY field_name, source, source_detail
        ORDER BY field_name
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def print_dashboard(trade_date: str = None):
    """打印完整溯源看板"""
    if trade_date is None:
        trade_date = date.today().isoformat()

    print(f"\n{'='*60}")
    print(f"📊 StockExpert 溯源看板 — {trade_date}")
    print(f"{'='*60}")

    # 覆盖率
    cov = get_coverage(trade_date)
    if cov:
        for c in cov:
            icon = "✅" if c["coverage_pct"] == 100 else ("⚠️" if float(c["coverage_pct"] or 0) > 50 else "🔴")
            print(f"\n{icon} {c['stage']} 覆盖率: {c['coverage_pct']}% ({c['success_cnt']}/{c['total_fields']})")
            if c["failed_fields"]:
                print(f"   失败字段: {c['failed_fields']}")
    else:
        print("\n⚠️ 今日无采集记录")

    # 各表数据
    print("\n--- 指数行情 ---")
    for idx in get_index_quotes(trade_date):
        chg = f"{idx['change_pct']:+.2f}%" if idx['change_pct'] else "N/A"
        print(f"  {idx['index_name']}({idx['index_code']}) "
              f"收{idx['close']} {chg} | {idx['source']}")

    ms = get_market_sentiment(trade_date)
    if ms:
        print(f"\n--- 市场情绪 ---")
        print(f"  涨 {ms['up_count']} / 平 {ms['flat_count']} / 跌 {ms['down_count']} "
              f"(涨停{ms['limit_up_count']} 跌停{ms['limit_down_count']}) | {ms['source_detail']}")

    bm = get_board_metrics(trade_date)
    if bm:
        print(f"\n--- 连板炸板 ---")
        print(f"  最高{bm['highest_board']}连板({bm['highest_board_stock']}) "
              f"今炸板率{bm['break_board_rate']}% | {bm['source']}")

    nf = get_north_flow(trade_date)
    if nf:
        print(f"\n--- 北向资金 ---")
        print(f"  主力{nf['main_net_inflow']}亿 "
              f"超大单{nf['super_large_net']}亿 | {nf['source_detail']}")

    # 字段状态详情
    print(f"\n{'='*60}")
    print("📋 字段采集状态")
    print(f"{'='*60}")
    statuses = get_fetch_status(trade_date)
    if not statuses:
        print("  (无记录)")
    else:
        current_group = None
        for s in statuses:
            if s["field_group"] != current_group:
                print(f"\n  [{s['field_group']}]")
                current_group = s["field_group"]
            err = f" | 🔴{s['error_message']}" if s["status"] == "failed" else ""
            val = f" = {s['value']}" if s["value"] and len(str(s["value"])) < 30 else ""
            print(f"    {s['icon']} {s['field_name']}{val} ({s['source']}:{s['source_detail']}){err}")

    # 数据源统计
    print(f"\n{'='*60}")
    print("📡 数据源成功率")
    print(f"{'='*60}")
    for src in get_all_sources():
        print(f"  {src['field_name']:25s} {src['source']:15s} {src['source_detail']:40s} {src['ok']:3d}/{src['total']:3d} ({src['rate']}%)")
