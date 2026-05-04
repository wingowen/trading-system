#!/usr/bin/env python3
"""
数据库迁移脚本
用于添加 status 字段到 trade_journal 表

用法:
    python migrations/001_add_status_to_trade_journal.py
"""

import sqlite3
import os
import sys


def get_db_path():
    if os.name == "nt":
        return (
            "/mnt/c/Users/WINGO/Documents/WorkSpace/trading-system/data/stockexpert.db"
        )
    db_path = os.environ.get("TRADING_DB_PATH")
    if db_path:
        return db_path
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", "stockexpert.db")


def migrate():
    db_path = get_db_path()
    print(f"数据库路径: {db_path}")

    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(trade_journal)")
    columns = {row["name"] for row in cursor.fetchall()}

    if "status" not in columns:
        print("添加 status 字段到 trade_journal 表...")
        cursor.execute(
            "ALTER TABLE trade_journal ADD COLUMN status TEXT DEFAULT 'holding'"
        )
        conn.commit()
        print("迁移完成: 已添加 status 字段")
    else:
        print("status 字段已存在，跳过迁移")

    cursor.execute("PRAGMA table_info(trade_journal)")
    print("\n当前表结构:")
    for row in cursor.fetchall():
        print(f"  - {row['name']}: {row['type']}")

    conn.close()
    print("\n迁移脚本执行成功!")


if __name__ == "__main__":
    migrate()
