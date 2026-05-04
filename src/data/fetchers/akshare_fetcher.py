"""
akshare 数据采集器
"""
import akshare as ak, pandas as pd, datetime, traceback
from typing import Optional


def fetch_index_quotes() -> dict:
    """4大指数 OHLCV"""
    try:
        df = ak.stock_zh_index_spot_em()
        rows = {}
        for _, row in df.iterrows():
            code = str(row.get("代码", ""))
            name = str(row.get("名称", ""))
            if code in ("000001", "399001", "399006", "000688"):
                code_full = f"{code}.{'SH' if code.startswith('0') or code == '000688' else 'SZ'}"
                rows[code_full] = {
                    "index_code": code_full,
                    "index_name": name,
                    "open": _float(row.get("今开", row.get("开盘", None))),
                    "high": _float(row.get("最高", None)),
                    "low": _float(row.get("最低", None)),
                    "close": _float(row.get("收盘", row.get("最新价", None))),
                    "volume": _int(row.get("成交量", None)),
                    "amount": _float(row.get("成交额", None)),
                    "change_pct": _float(row.get("涨跌幅", None)),
                    "source": "akshare:stock_zh_index_spot_em",
                }
        return {"indices": rows, "status": "success", "fetched_at": str(datetime.datetime.now())}
    except Exception as e:
        return {"status": "failed", "error": str(e), "trace": traceback.format_exc()}


def fetch_limit_up_count() -> dict:
    """涨停家数"""
    try:
        df = ak.stock_zt_pool_strong_em(date=datetime.date.today().strftime("%Y%m%d"))
        return {
            "limit_up_count": len(df),
            "source": "akshare:stock_zt_pool_strong_em",
            "status": "success",
            "fetched_at": str(datetime.datetime.now()),
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def fetch_limit_down_count() -> dict:
    """跌停家数"""
    try:
        df = ak.stock_zt_pool_dtgc_em(date=datetime.date.today().strftime("%Y%m%d"))
        return {
            "limit_down_count": len(df),
            "source": "akshare:stock_zt_pool_dtgc_em",
            "status": "success",
            "fetched_at": str(datetime.datetime.now()),
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def fetch_north_flow_summary() -> dict:
    """北向资金流向概况（今日，akshare 实时）"""
    try:
        df = ak.stock_hsgt_fund_flow_summary_em()
        result = {"status": "success", "source": "akshare:stock_hsgt_fund_flow_summary_em", "rows": {}}
        for _, row in df.iterrows():
            typ = str(row.get("类型", ""))
            net = _float(row.get("成交净买额", None))
            fund_inflow = _float(row.get("资金净流入", None))
            direction = str(row.get("资金方向", ""))
            result["rows"][typ] = {
                "type": typ,
                "direction": direction,
                "net_deal_amt": net,
                "fund_inflow": fund_inflow,
            }
        return result
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def fetch_north_hist() -> dict:
    """北向历史（akshare，注意：2024-08-19起净买额全NaN）"""
    try:
        df = ak.stock_hsgt_hist_em(symbol="北向资金")
        df["日期"] = pd.to_datetime(df["日期"], errors="coerce").dt.date
        valid = df[df["当日成交净买额"].notna()]
        nan = df[df["当日成交净买额"].isna()]
        return {
            "total": len(df),
            "valid_count": len(valid),
            "na_count": len(nan),
            "last_valid_date": str(valid.iloc[-1]["日期"]) if len(valid) else None,
            "first_na_date": str(nan.iloc[0]["日期"]) if len(nan) else None,
            "latest_5": valid.tail(5)[["日期", "当日成交净买额", "当日资金流入"]].to_dict("records") if len(valid) else [],
            "source": "akshare:stock_hsgt_hist_em",
            "status": "success" if len(valid) > 0 else "partial",
            "note": "2024-08-19起全NaN，建议CDP补历史",
        }
    except Exception as e:
        return {"status": "failed", "error": str(e)}


def _float(v) -> Optional[float]:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _int(v) -> Optional[int]:
    try:
        return int(v)
    except (TypeError, ValueError):
        return None
