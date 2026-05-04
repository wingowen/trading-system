"""
交易日志记录器
根据 spec 04-layer4-evolution.md：
- 记录入场/出场信息
- 存储到 SQLite（复用 stockexpert.db）
"""
import sqlite3
from typing import Any, Dict, Optional
from datetime import datetime

DB_PATH = "/mnt/c/Users/WINGO/Documents/WorkSpace/trading-system/data/stockexpert.db"


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


class TradeJournal:
    """交易日志记录器 — 写入 SQLite"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self._ensure_schema()

    def _ensure_schema(self):
        """建 trade_journal 表"""
        conn = _conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trade_journal (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                trade_id        TEXT NOT NULL,
                action          TEXT NOT NULL,  -- 'entry' | 'exit'
                code            TEXT,
                name            TEXT,
                price           REAL DEFAULT 0,
                date            TEXT,
                pattern         TEXT,
                sector          TEXT,
                market_env_score REAL DEFAULT 0,
                sector_score    REAL DEFAULT 0,
                stop_loss       REAL DEFAULT 0,
                take_profit     REAL DEFAULT 0,
                position_size   REAL DEFAULT 0,
                reason          TEXT,
                pnl_percent     REAL DEFAULT 0,
                holding_days    INTEGER DEFAULT 0,
                created_at      TEXT DEFAULT (datetime('now', 'localtime')),
                updated_at      TEXT DEFAULT (datetime('now', 'localtime')),
                UNIQUE(trade_id, action)
            )
        """)
        conn.commit()
        # 确保 status 字段存在（ALTER TABLE for existing dbs）
        try:
            conn.execute("ALTER TABLE trade_journal ADD COLUMN status TEXT DEFAULT 'holding'")
            conn.commit()
        except Exception:
            pass  # 字段已存在
        conn.close()

    def record_entry(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """记录入场"""
        try:
            trade_id = trade_data.get("trade_id", "")
            if not trade_id:
                return {"status": "error", "message": "trade_id is required"}

            conn = _conn()
            conn.execute("""
                INSERT OR REPLACE INTO trade_journal
                    (trade_id, action, code, name, price, date,
                     pattern, sector, market_env_score, sector_score,
                     stop_loss, take_profit, position_size, created_at, updated_at)
                VALUES (?, 'entry', ?, ?, ?, ?,
                        ?, ?, ?, ?,
                        ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))
            """, (
                trade_id,
                trade_data.get("code", ""),
                trade_data.get("name", ""),
                trade_data.get("buy_price", 0),
                trade_data.get("buy_date", ""),
                trade_data.get("pattern", ""),
                trade_data.get("sector", ""),
                trade_data.get("market_env_score", 0),
                trade_data.get("sector_score", 0),
                trade_data.get("stop_loss", 0),
                trade_data.get("take_profit", 0),
                trade_data.get("position_size", 0),
            ))
            conn.commit()
            conn.close()
            return {"status": "success", "trade_id": trade_id}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def record_exit(self, trade_data: Dict[str, Any]) -> Dict[str, Any]:
        """记录出场"""
        try:
            trade_id = trade_data.get("trade_id", "")
            if not trade_id:
                return {"status": "error", "message": "trade_id is required"}

            conn = _conn()
            conn.execute("""
                INSERT OR REPLACE INTO trade_journal
                    (trade_id, action, code, name, price, date,
                     reason, pnl_percent, holding_days, updated_at)
                VALUES (?, 'exit', ?, ?, ?, ?,
                        ?, ?, ?, datetime('now', 'localtime'))
            """, (
                trade_id,
                trade_data.get("code", ""),
                trade_data.get("name", ""),
                trade_data.get("sell_price", 0),
                trade_data.get("sell_date", ""),
                trade_data.get("reason", ""),
                trade_data.get("pnl_percent", 0),
                trade_data.get("holding_days", 0),
            ))
            conn.commit()
            conn.close()
            return {"status": "success", "trade_id": trade_id}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_trade(self, trade_id: str) -> Dict[str, Any]:
        """获取某笔交易的入场和出场记录"""
        conn = _conn()
        rows = conn.execute(
            "SELECT * FROM trade_journal WHERE trade_id=? ORDER BY action",
            (trade_id,)
        ).fetchall()
        conn.close()
        if not rows:
            return {"status": "error", "message": "trade not found"}
        records = [dict(r) for r in rows]
        return {"status": "success", "trade_id": trade_id, "records": records}

    def get_all_trades(self) -> Dict[str, Any]:
        """获取所有交易记录"""
        conn = _conn()
        rows = conn.execute(
            "SELECT * FROM trade_journal ORDER BY created_at DESC"
        ).fetchall()
        conn.close()
        return {"status": "success", "trades": [dict(r) for r in rows]}
