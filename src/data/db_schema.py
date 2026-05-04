"""
StockExpert SQLite 数据库 Schema
建表脚本 — 只需执行一次
"""
import sqlite3, pathlib, os

DB_PATH = pathlib.Path(__file__).parent.parent.parent / "data" / "stockexpert.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA = """
-- 交易日主表
CREATE TABLE IF NOT EXISTS trading_days (
    trade_date   TEXT PRIMARY KEY,
    weekday      INTEGER,
    is_trading   INTEGER DEFAULT 1,
    created_at   TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at   TEXT DEFAULT (datetime('now', 'localtime')),
    morning_done INTEGER DEFAULT 0,
    midday_done  INTEGER DEFAULT 0,
    close_done   INTEGER DEFAULT 0
);

-- 指数行情（上证/深证/创业板/科创50）
CREATE TABLE IF NOT EXISTS index_quotes (
    trade_date  TEXT,
    index_code  TEXT,
    index_name  TEXT,
    open        REAL,
    high        REAL,
    low         REAL,
    close       REAL,
    volume      INTEGER,
    amount      REAL,
    change_pct  REAL,
    source      TEXT,
    fetched_at  TEXT DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (trade_date, index_code)
);

-- 全市场情绪（涨跌平 + 涨跌停）
CREATE TABLE IF NOT EXISTS market_sentiment (
    trade_date      TEXT PRIMARY KEY,
    up_count        INTEGER,
    down_count      INTEGER,
    flat_count      INTEGER,
    limit_up_count  INTEGER,
    limit_down_count INTEGER,
    total_stocks    INTEGER,
    up_ratio        REAL,
    source          TEXT,
    source_detail   TEXT,
    fetched_at      TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 连板炸板核心指标
CREATE TABLE IF NOT EXISTS board_metrics (
    trade_date           TEXT PRIMARY KEY,
    highest_board        INTEGER,
    highest_board_stock  TEXT,
    break_board_rate     REAL,
    break_board_count    INTEGER,
    limit_up_count       INTEGER,
    source               TEXT,
    fetched_at           TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 连板晋级率
CREATE TABLE IF NOT EXISTS board_promotion (
    trade_date     TEXT PRIMARY KEY,
    level_1_to_2   REAL,
    level_2_to_3   REAL,
    level_3_to_4   REAL,
    level_1_to_2_cnt INTEGER,
    level_2_to_3_cnt INTEGER,
    level_3_to_4_cnt INTEGER,
    source         TEXT,
    fetched_at     TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 北向资金
CREATE TABLE IF NOT EXISTS north_flow (
    trade_date      TEXT PRIMARY KEY,
    north_net_inflow REAL,
    hgt_net_inflow  REAL,
    sgt_net_inflow  REAL,
    main_net_inflow REAL,
    super_large_net REAL,
    large_net       REAL,
    medium_net      REAL,
    small_net       REAL,
    source          TEXT,
    source_detail   TEXT,
    fetched_at      TEXT DEFAULT (datetime('now', 'localtime'))
);

-- 字段采集溯源日志（核心可观测表）
CREATE TABLE IF NOT EXISTS field_fetch_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date   TEXT,
    stage        TEXT,
    field_group  TEXT,
    field_name   TEXT,
    source       TEXT,
    source_detail TEXT,
    status       TEXT,
    value        TEXT,
    error_message TEXT,
    fetched_at   TEXT DEFAULT (datetime('now', 'localtime')),
    UNIQUE(trade_date, stage, field_group, field_name)
);

-- 溯源覆盖率视图
CREATE VIEW IF NOT EXISTS v_field_coverage AS
SELECT
    trade_date,
    stage,
    COUNT(*) AS total_fields,
    SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) AS success_cnt,
    ROUND(1.0*SUM(CASE WHEN status='success' THEN 1 ELSE 0 END)/COUNT(*)*100, 1) AS coverage_pct,
    GROUP_CONCAT(CASE WHEN status != 'success' THEN field_name||':'||status ELSE NULL END) AS failed_fields
FROM field_fetch_log
WHERE trade_date IS NOT NULL
GROUP BY trade_date, stage
ORDER BY trade_date DESC, stage;
"""


def init_db(db_path: str = None) -> str:
    path = db_path or str(DB_PATH)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    return path


if __name__ == "__main__":
    p = init_db()
    print(f"✅ 数据库初始化完成: {p}")
