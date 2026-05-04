"""
StockExpert 数据库写入层
将各采集器数据写入 SQLite，并记录溯源日志
"""
import sqlite3, json, datetime
from typing import Optional, Any

DB_PATH = "/mnt/c/Users/WINGO/Documents/WorkSpace/trading-system/data/stockexpert.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


class DatabaseWriter:
    last_record_id: Optional[int] = None

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.conn = get_conn()
        self._ensure_schema()
        self.last_record_id = None

    def _ensure_schema(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS trading_days (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_date  TEXT NOT NULL UNIQUE,
            weekday     INTEGER,
            created_at  TEXT DEFAULT (datetime('now'))
        )""")
        self.conn.execute("""
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
        )""")
        self.conn.execute("""
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
        )""")
        self.conn.commit()

    def write_field(self, trade_date: str, session: str,
                    field: str, value: Any, source: str,
                    status: str = "success", error: str = None):
        """写入单个字段记录"""
        if isinstance(value, (dict, list)):
            raw = json.dumps(value, ensure_ascii=False, default=str)
        else:
            raw = None

        self.conn.execute("""
            INSERT OR REPLACE INTO data_records
                (trade_date, session, field_name, field_value, raw_value,
                 source, fetch_time, status, error_message)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'), ?, ?)""",
            (trade_date, session, field, value, raw,
             source, status, error))
        self.conn.commit()

    def write_all(self, trade_date: str, session: str,
                  akshare_data: dict, zt_data: dict, cdp_data: dict):
        """
        批量写入全量采集数据。
        返回 (success: bool, message: str)。
        """
        ok_count, fail_count = 0, 0

        # akshare fields
        AX = akshare_data

        # 1. index quotes — indices dict key 格式: "000001.SH" / "399001.SZ"
        iq = AX.get("index_quotes", {})
        self._log("akshare", trade_date, session, "fetch_index_quotes",
                  iq.get("status"), records_count=len(iq.get("indices", {})))
        idx_map = {
            "000001.SH": ("sh000001", "上证指数"),
            "399001.SZ": ("sz399001", "深证成指"),
            "399006.SZ": ("sz399006", "创业板指"),
            "000688.SH": ("sh000688", "科创50"),
        }
        for key, (code, name) in idx_map.items():
            row = iq.get("indices", {}).get(key)
            if row and row.get("change_pct") is not None:
                self.write_field(trade_date, session, f"index_chg_{code}", row["change_pct"],
                                 "akshare:stock_zh_index_spot_em")
                ok_count += 1
            else:
                fail_count += 1

        # 2. limit up/down pools
        lu = AX.get("limit_up", {})
        self._log("akshare", trade_date, session, "fetch_limit_up_pool",
                  lu.get("status"), records_count=lu.get("zt_count"))
        if lu.get("zt_count") is not None:
            self.write_field(trade_date, session, "zt_pool_count", lu["zt_count"],
                             lu.get("source", "akshare:stock_zt_pool_strong_em"))
            ok_count += 1
        else:
            fail_count += 1

        ld = AX.get("limit_down", {})
        self._log("akshare", trade_date, session, "fetch_limit_down_pool",
                  ld.get("status"), records_count=ld.get("dt_count"))
        if ld.get("dt_count") is not None:
            self.write_field(trade_date, session, "dt_pool_count", ld["dt_count"],
                             ld.get("source", "akshare:stock_zt_pool_dtgc_em"))
            ok_count += 1
        else:
            fail_count += 1

        # 3. north history — latest_5[-1] 是最近一条有效记录
        nh = AX.get("north_hist", {})
        self._log("akshare", trade_date, session, "fetch_north_hist",
                  nh.get("status"), records_count=nh.get("valid_count", 0))
        latest_5 = nh.get("latest_5", [])
        if latest_5:
            last = latest_5[-1]
            v = last.get("当日成交净买额") if isinstance(last, dict) else None
            self.write_field(trade_date, session, "north_net_inflow_latest",
                             v,
                             "akshare:stock_hsgt_hist_em",
                             status=nh.get("status", "success"))
            if v is not None:
                ok_count += 1
            else:
                fail_count += 1
        else:
            self.write_field(trade_date, session, "north_net_inflow_latest",
                             None, "akshare:stock_hsgt_hist_em",
                             status=nh.get("status", "partial"),
                             error=f"valid_count={nh.get('valid_count',0)}, "
                                   f"last_valid_date={nh.get('last_valid_date')}")
            fail_count += 1

        # 4. north summary — rows dict key: "沪港通" / "深港通"
        ns = AX.get("north_summary", {})
        self._log("akshare", trade_date, session, "fetch_north_flow_summary",
                  ns.get("status"), records_count=len(ns.get("rows", {})))
        hgt = ns.get("rows", {}).get("沪港通", {})
        sgt = ns.get("rows", {}).get("深港通", {})
        # hgt_net_inflow: 沪股通净流入
        v = hgt.get("net_deal_amt") if isinstance(hgt, dict) else None
        if v is not None:
            self.write_field(trade_date, session, "hgt_net_inflow", v,
                             ns.get("source", "akshare:stock_hsgt_fund_flow_summary_em"))
            ok_count += 1
        else:
            fail_count += 1
        v = sgt.get("net_deal_amt") if isinstance(sgt, dict) else None
        if v is not None:
            self.write_field(trade_date, session, "sgt_net_inflow", v,
                             ns.get("source", "akshare:stock_hsgt_fund_flow_summary_em"))
            ok_count += 1
        else:
            fail_count += 1

        # 5. north board (akshare 无此接口，跳过)
        # 6. concept board (akshare 无此接口，跳过)

        # zhangtingke fields
        ZT = zt_data.get("today", {})
        if ZT.get("highest_board") is not None:
            self.write_field(trade_date, session, "highest_board", ZT["highest_board"],
                             ZT.get("source", "zhangtingke.com:zt_lbgd_line"))
            ok_count += 1
        if ZT.get("break_board_rate") is not None:
            self.write_field(trade_date, session, "break_board_rate", ZT["break_board_rate"],
                             ZT.get("source", "zhangtingke.com:vip_today_lbtd"))
            ok_count += 1
        if ZT.get("limit_up_total") is not None:
            self.write_field(trade_date, session, "continue_board_count",
                             ZT["limit_up_total"],
                             ZT.get("source", "zhangtingke.com:vip_today_lbtd"))
            ok_count += 1
        if ZT.get("break_board_count") is not None:
            self.write_field(trade_date, session, "touched_not_sealed",
                             ZT["break_board_count"],
                             ZT.get("source", "zhangtingke.com:vip_today_lbtd"))
            ok_count += 1
        # 晋级率
        for lv in ["1_to_2", "2_to_3", "3_to_4", "4_to_5"]:
            key = f"level_{lv}"
            if ZT.get(key) is not None:
                self.write_field(trade_date, session, key, ZT[key],
                                 ZT.get("source", "zhangtingke.com:lbtd_yesterday_jinji"))
                ok_count += 1

        # CDP fields
        NF = cdp_data.get("north_flow", {})
        self._log("cdp", trade_date, session, "fetch_north_flow_cdp",
                  NF.get("status"))
        for f in ["main_net_inflow", "super_large_net", "large_net",
                  "medium_net", "small_net"]:
            v = NF.get(f)
            if v is not None:
                self.write_field(trade_date, session, f, v,
                                 NF.get("source", "CDP:dpzjlx.html"))
                ok_count += 1
            else:
                fail_count += 1

        # save record_id
        cur = self.conn.execute(
            "SELECT id FROM data_records WHERE trade_date=? AND session=? LIMIT 1",
            (trade_date, session))
        row = cur.fetchone()
        self.last_record_id = row["id"] if row else None

        msg = f"写入 {ok_count} 字段, {fail_count} 失败"
        return ok_count > 0, msg

    def _log(self, fetcher: str, trade_date: str, session: str,
             endpoint: str, status: str = "unknown", records_count: int = 0,
             error_message: str = None):
        self.conn.execute("""
            INSERT INTO fetch_logs
                (trade_date, session, fetcher, status, records_count, error_message)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (trade_date, session, f"{fetcher}:{endpoint}", status,
             records_count, error_message))
        self.conn.commit()

    def close(self):
        self.conn.close()
