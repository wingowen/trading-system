"""
StockExpert SQLite 数据库 Schema
建表脚本 — 只需执行一次

注意：此文件定义的 Schema 与 db_writer.py 中 _ensure_schema() 保持一致
实际生产使用中，db_writer.py 会自动初始化表结构
"""
import sqlite3, pathlib, os, logging
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

DB_PATH = pathlib.Path(__file__).parent.parent.parent / "data" / "stockexpert.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SCHEMA = """
-- 交易日主表
CREATE TABLE IF NOT EXISTS trading_days (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date  TEXT NOT NULL UNIQUE,
    weekday     INTEGER,
    created_at  TEXT DEFAULT (datetime('now'))
);

-- 数据记录主表（核心 KV 存储）
CREATE TABLE IF NOT EXISTS data_records (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date      TEXT NOT NULL,
    session         TEXT NOT NULL,
    field_name      TEXT NOT NULL,
    field_value     REAL,
    raw_value       TEXT,
    source          TEXT NOT NULL,
    fetch_time      TEXT,
    status          TEXT DEFAULT 'success',
    error_message   TEXT,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(trade_date, session, field_name)
);

-- 采集器执行日志
CREATE TABLE IF NOT EXISTS fetch_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date      TEXT NOT NULL,
    session         TEXT NOT NULL,
    fetcher         TEXT NOT NULL,
    status          TEXT NOT NULL,
    duration_ms     INTEGER,
    records_count   INTEGER,
    error_message   TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- 策略参数调整日志
CREATE TABLE IF NOT EXISTS strategy_tuning_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    field_name   TEXT NOT NULL,
    old_value    TEXT,
    new_value    TEXT,
    reason       TEXT,
    confidence   REAL,
    trade_date   TEXT,
    created_at   TEXT DEFAULT (datetime('now', 'localtime'))
);
"""


def init_db(db_path: str = None) -> str:
    """
    初始化数据库 Schema
    
    Args:
        db_path: 数据库文件路径，默认使用项目默认路径
    
    Returns:
        初始化后的数据库文件路径
    """
    path = db_path or str(DB_PATH)
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()
    logger.info(f"数据库初始化完成: {path}")
    return path


if __name__ == "__main__":
    p = init_db()
    logger.info(f"✅ 数据库初始化完成: {p}")