"""
StockExpert 数据库读取层 — 统一 kv 结构
所有数据存储在 data_records (kv) 和 fetch_logs两张表。
"""
import sqlite3
import os
from pathlib import Path
from datetime import date, datetime
from typing import Optional, List, Dict, Any
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 数据库路径配置
DB_PATH = os.environ.get(
    "STOCKEXPERT_DB",
    str(Path(__file__).parent.parent.parent / "data" / "stockexpert.db")
)


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─── data_records kv 查询 ───────────────────────────────────────────────────

def get_records(
    trade_date: str,
    session: str = None,
    field_name: str = None,
    category: str = None,
) -> List[Dict[str, Any]]:
    """
    查询 data_records。

    Args:
        trade_date: 格式 YYYY-MM-DD
        session: 可选 "morning" / "noon" / "close"
        field_name: 可选，精确匹配
        category: 可选，从 FIELD_META 映射的 category 过滤
    """
    conn = get_conn()
    query = "SELECT * FROM data_records WHERE trade_date = ?"
    params: list = [trade_date]

    if session:
        query += " AND session = ?"
        params.append(session)
    if field_name:
        query += " AND field_name = ?"
        params.append(field_name)

    rows = conn.execute(query, params).fetchall()
    conn.close()

    records = [dict(r) for r in rows]

    # category 过滤：需要 FIELD_META 映射
    if category:
        META_CAT = {
            "index_chg_sh000001": "指数", "index_chg_sz399001": "指数",
            "index_chg_sz399006": "指数", "index_chg_sh000688": "指数",
            "zt_pool_count": "涨停池", "dt_pool_count": "跌停池",
            "highest_board": "连板", "break_board_rate": "炸板",
            "continue_board_count": "连板", "touched_not_sealed": "炸板",
            "level_1_to_2": "晋级率", "level_2_to_3": "晋级率",
            "level_3_to_4": "晋级率", "level_4_to_5": "晋级率",
            "main_net_inflow": "资金流", "super_large_net": "资金流",
            "large_net": "资金流", "medium_net": "资金流", "small_net": "资金流",
            "hgt_net_inflow": "北向", "sgt_net_inflow": "北向",
            "north_net_inflow_latest": "北向历史",
        }
        records = [r for r in records if META_CAT.get(r["field_name"]) == category]

    return records


def get_field(trade_date: str, field_name: str, session: str = "morning") -> Optional[Any]:
    """查询单个字段最新值。"""
    conn = get_conn()
    row = conn.execute(
        "SELECT field_value FROM data_records "
        "WHERE trade_date=? AND session=? AND field_name=?",
        (trade_date, session, field_name),
    ).fetchone()
    conn.close()
    return row["field_value"] if row else None


def get_latest_field(field_name: str, limit: int = 5) -> List[Dict[str, Any]]:
    """查询某字段历史最近 N 条。"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT trade_date, session, field_value, status "
        "FROM data_records WHERE field_name=? "
        "ORDER BY trade_date DESC, session DESC LIMIT ?",
        (field_name, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── fetch_logs 查询 ────────────────────────────────────────────────────────

def get_fetch_logs(trade_date: str, session: str = None) -> List[Dict[str, Any]]:
    """采集日志。"""
    conn = get_conn()
    if session:
        rows = conn.execute(
            "SELECT * FROM fetch_logs WHERE trade_date=? AND session=? ORDER BY created_at",
            (trade_date, session),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM fetch_logs WHERE trade_date=? ORDER BY created_at",
            (trade_date,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_fetcher_groups(trade_date: str, session: str = "morning") -> List[Dict[str, Any]]:
    """按 fetcher 分组的日志（最新一次的状态）。"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT fetcher, status, duration_ms, records_count, error_message, created_at "
        "FROM fetch_logs WHERE trade_date=? AND session=? "
        "ORDER BY fetcher, created_at",
        (trade_date, session),
    ).fetchall()
    conn.close()

    groups: Dict[str, Dict] = {}
    for r in rows:
        d = dict(r)
        fetcher = d["fetcher"]
        if fetcher not in groups:
            groups[fetcher] = {"fetcher": fetcher, "logs": []}
        groups[fetcher]["logs"].append(d)

    return list(groups.values())


# ─── 覆盖率 ─────────────────────────────────────────────────────────────────

def get_coverage(trade_date: str, session: str = None) -> Dict[str, Any]:
    """计算 data_records 字段采集覆盖率。"""
    conn = get_conn()
    query = (
        "SELECT status, COUNT(*) as cnt FROM data_records "
        "WHERE trade_date = ?"
    )
    params: list = [trade_date]
    if session:
        query += " AND session = ?"
        params.append(session)
    query += " GROUP BY status"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    total = sum(r["cnt"] for r in rows)
    success = next((r["cnt"] for r in rows if r["status"] == "success"), 0)
    return {
        "total": total,
        "success": success,
        "failed": total - success,
        "coverage_pct": round(success / total * 100, 1) if total else 0,
    }


# ─── 溯源看板打印 ────────────────────────────────────────────────────────────

FIELD_META = {
    "index_chg_sh000001":  {"label": "上证指数涨跌幅",  "unit": "%",   "category": "指数"},
    "index_chg_sz399001":  {"label": "深证成指涨跌幅",  "unit": "%",   "category": "指数"},
    "index_chg_sz399006":  {"label": "创业板指涨跌幅",  "unit": "%",   "category": "指数"},
    "index_chg_sh000688":  {"label": "科创50涨跌幅",    "unit": "%",   "category": "指数"},
    "zt_pool_count":       {"label": "涨停家数",        "unit": "只",   "category": "涨停池"},
    "dt_pool_count":       {"label": "跌停家数",        "unit": "只",   "category": "跌停池"},
    "highest_board":       {"label": "最高连板",        "unit": "连板", "category": "连板"},
    "break_board_rate":    {"label": "今炸板率",        "unit": "%",    "category": "炸板"},
    "continue_board_count":{"label": "今连板数",        "unit": "只",   "category": "连板"},
    "touched_not_sealed":  {"label": "触板未封",        "unit": "只",   "category": "炸板"},
    "level_1_to_2":        {"label": "1进2晋级率",      "unit": "%",   "category": "晋级率"},
    "level_2_to_3":        {"label": "2进3晋级率",      "unit": "%",   "category": "晋级率"},
    "level_3_to_4":        {"label": "3进4晋级率",      "unit": "%",   "category": "晋级率"},
    "level_4_to_5":        {"label": "4进5晋级率",      "unit": "%",   "category": "晋级率"},
    "main_net_inflow":     {"label": "主力净流入",       "unit": "亿元", "category": "资金流"},
    "super_large_net":     {"label": "超大单净流入",     "unit": "亿元", "category": "资金流"},
    "large_net":           {"label": "大单净流入",       "unit": "亿元", "category": "资金流"},
    "medium_net":          {"label": "中单净流入",       "unit": "亿元", "category": "资金流"},
    "small_net":           {"label": "小单净流入",       "unit": "亿元", "category": "资金流"},
    "hgt_net_inflow":      {"label": "沪股通净流入",    "unit": "亿元", "category": "北向"},
    "sgt_net_inflow":      {"label": "深股通净流入",    "unit": "亿元", "category": "北向"},
    "north_net_inflow_latest": {"label": "北向历史最新", "unit": "亿元", "category": "北向历史"},
}


def print_dashboard(trade_date: str = None, session: str = "morning"):
    """打印完整溯源看板。"""
    if trade_date is None:
        trade_date = date.today().isoformat()

    records = get_records(trade_date, session)
    cov = get_coverage(trade_date, session)

    logger.info(f"\n{'='*60}")
    logger.info(f"📊 StockExpert 溯源看板 — {trade_date}  {session}")
    logger.info(f"   覆盖率: {cov['coverage_pct']}% ({cov['success']}/{cov['total']})")
    logger.info(f"{'='*60}")

    # 按 category 分组展示
    by_cat: Dict[str, List] = {}
    for r in records:
        meta = FIELD_META.get(r["field_name"], {})
        cat = meta.get("category", "其他")
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append({**r, "meta": meta})

    for cat, items in by_cat.items():
        logger.info(f"\n  [{cat}]")
        for it in items:
            icon = "✅" if it["status"] == "success" else "⚠️" if it["status"] == "partial" else "🔴"
            val = it["field_value"]
            unit = it["meta"].get("unit", "")
            src = it.get("source", "")
            err = f" | 🔴{it.get('error_message', '')[:40]}" if it["status"] != "success" else ""
            logger.info(f"    {icon} {it['meta'].get('label', it['field_name'])}: {val}{unit}  [{src}]{err}")

    # 采集日志摘要
    logs = get_fetch_logs(trade_date, session)
    logger.info(f"\n  [采集日志] {len(logs)} 条")
    for lg in logs[-5:]:  # 只显示最近5条
        icon = "✅" if lg["status"] == "success" else "🔴"
        logger.info(f"    {icon} {lg['fetcher']} {lg.get('duration_ms', 0)}ms {lg.get('records_count', 0)}条")
