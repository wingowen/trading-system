"""
akshare 数据采集器
"""
import akshare as ak, pandas as pd, datetime, traceback, logging
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
                # 尝试多个可能的中文列名（akshare 可能变更）
                c_open   = _df_col(df, "今开", "开盘")
                c_high   = _df_col(df, "最高")
                c_low    = _df_col(df, "最低")
                c_close  = _df_col(df, "收盘", "最新价")
                c_vol    = _df_col(df, "成交量")
                c_amount = _df_col(df, "成交额")
                c_chg    = _df_col(df, "涨跌幅")
                rows[code_full] = {
                    "index_code": code_full,
                    "index_name": name,
                    "open": _float(row.get(c_open)),
                    "high": _float(row.get(c_high)),
                    "low": _float(row.get(c_low)),
                    "close": _float(row.get(c_close)),
                    "volume": _int(row.get(c_vol)),
                    "amount": _float(row.get(c_amount)),
                    "change_pct": _float(row.get(c_chg)),
                    "source": "akshare:stock_zh_index_spot_em",
                }
        logger.info(f"获取指数行情，共 {len(rows)} 个指数")
        return {"indices": rows, "status": "success", "fetched_at": str(datetime.datetime.now())}
    except Exception as e:
        logger.error(f"获取指数行情失败: {e}")
        return {"status": "failed", "error": str(e), "trace": traceback.format_exc()}


def fetch_limit_up_count() -> dict:
    """涨停家数"""
    try:
        df = ak.stock_zt_pool_strong_em(date=datetime.date.today().strftime("%Y%m%d"))
        logger.info(f"涨停家数: {len(df)}")
        return {
            "limit_up_count": len(df),
            "source": "akshare:stock_zt_pool_strong_em",
            "status": "success",
            "fetched_at": str(datetime.datetime.now()),
        }
    except Exception as e:
        logger.error(f"获取涨停家数失败: {e}")
        return {"status": "failed", "error": str(e)}


def fetch_limit_down_count() -> dict:
    """跌停家数"""
    try:
        df = ak.stock_zt_pool_dtgc_em(date=datetime.date.today().strftime("%Y%m%d"))
        logger.info(f"跌停家数: {len(df)}")
        return {
            "limit_down_count": len(df),
            "source": "akshare:stock_zt_pool_dtgc_em",
            "status": "success",
            "fetched_at": str(datetime.datetime.now()),
        }
    except Exception as e:
        logger.error(f"获取跌停家数失败: {e}")
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
        logger.info(f"获取北向资金概况，共 {len(result['rows'])} 条")
        return result
    except Exception as e:
        logger.error(f"获取北向资金概况失败: {e}")
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
        logger.error(f"获取北向历史失败: {e}")
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


def _df_col(df: pd.DataFrame, *names) -> str:
    """返回 df 中实际存在的列名（尝试多个备选名）。"""
    for name in names:
        if name in df.columns:
            return name
    return df.columns[0] if len(df.columns) > 0 else ""


# ─── 精准数据采集：板块 → 个股 ────────────────────────────────────────────────

def fetch_strong_sectors(date: str = None, top_n: int = 5) -> dict:
    """
    获取强势板块（近5日累计涨幅 Top N）。
    链路: stock_board_industry_name_em() → stock_board_industry_hist_em() 查近5日涨幅 → TopN
    """
    try:
        # 计算日期范围，只获取最近 30 天数据以避免获取太多
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(days=60)).strftime("%Y%m%d") if not date else date
        board_df = ak.stock_board_industry_name_em()
        sectors = []
        for _, row in board_df.iterrows():
            name = str(row.get("板块名称", ""))
            if not name:
                continue
            try:
                hist = ak.stock_board_industry_hist_em(
                    symbol=name, period="日", start_date=start_date, 
                    end_date=date or today.strftime("%Y%m%d"), adjust="qfq"
                )
                if hist is not None and len(hist) >= 2:
                    # 取近5日（去掉今日最新）累计涨幅
                    recent = hist.tail(6)  # 含今日共6条，取前5日
                    chgs = recent["涨跌幅"].tolist() if "涨跌幅" in recent.columns else []
                    chg_5d = round(sum(chgs), 2) if chgs else 0.0
                    close = float(recent.iloc[-1]["收盘"]) if "收盘" in recent.columns else 0
                    sectors.append({"name": name, "chg_5d": chg_5d, "close": close})
            except Exception:
                continue

        # 按5日涨幅降序
        sectors.sort(key=lambda x: x["chg_5d"], reverse=True)
        top = sectors[:top_n]
        logger.info(f"获取强势板块，共 {len(sectors)} 个板块，Top {top_n}")
        return {"status": "success", "strong_sectors": top, "all_count": len(sectors)}
    except Exception as e:
        logger.error(f"获取强势板块失败: {e}")
        return {"status": "failed", "error": str(e)}


def fetch_sector_stocks(sector_name: str, top_n: int = 10) -> dict:
    """
    获取板块成分股，按涨幅降序取 TopN。
    链路: stock_board_industry_cons_em() → 日线涨幅排序 → TopN
    """
    try:
        # 计算日期范围，只获取最近 30 天数据
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(days=30)).strftime("%Y%m%d")
        
        cons_df = ak.stock_board_industry_cons_em(symbol=sector_name)
        if cons_df is None or cons_df.empty:
            return {"status": "success", "sector": sector_name, "stocks": []}

        # 取成分股代码
        codes = []
        code_col = None
        for col in ["代码", "代码   ", "股票代码"]:
            if col in cons_df.columns:
                code_col = col
                break
        if code_col:
            codes = cons_df[code_col].dropna().astype(str).str.strip().tolist()[:30]  # 最多30只

        stocks = []
        for code in codes[:15]:  # 最多查15只
            code_clean = code.replace(".SH", "").replace(".SZ", "").strip()
            try:
                hist = ak.stock_zh_a_hist(
                    symbol=code_clean, period="日", start_date=start_date, 
                    end_date=today.strftime("%Y%m%d"), adjust="qfq"
                )
                if hist is not None and len(hist) >= 2:
                    recent = hist.tail(2)
                    chg = float(recent.iloc[-1]["涨跌幅"]) if "涨跌幅" in recent.columns else 0
                    close = float(recent.iloc[-1]["收盘"]) if "收盘" in recent.columns else 0
                    name = str(recent.iloc[-1].get("股票名称", code_clean))
                    stocks.append({"code": code_clean, "name": name, "chg_1d": chg, "close": close})
            except Exception:
                continue

        stocks.sort(key=lambda x: x["chg_1d"], reverse=True)
        logger.info(f"获取板块 {sector_name} 成分股，共 {len(stocks)} 只，Top {top_n}")
        return {"status": "success", "sector": sector_name, "stocks": stocks[:top_n]}
    except Exception as e:
        logger.error(f"获取板块 {sector_name} 成分股失败: {e}")
        return {"status": "failed", "error": str(e)}


def enrich_stock_metrics(code: str) -> dict:
    """
    单股日线补充 MA5/MA10/MA20/量比。
    链路: stock_zh_a_hist() → 计算 MA 和量比
    """
    try:
        today = datetime.date.today()
        start_date = (today - datetime.timedelta(days=60)).strftime("%Y%m%d")
        hist = ak.stock_zh_a_hist(
            symbol=code, period="日", start_date=start_date, 
            end_date=today.strftime("%Y%m%d"), adjust="qfq"
        )
        if hist is None or len(hist) < 20:
            logger.warning(f"股票 {code} 历史数据不足 20 天")
            return {"status": "partial", "code": code}

        df = hist.tail(30).copy()
        df["MA5"] = df["收盘"].rolling(5).mean()
        df["MA10"] = df["收盘"].rolling(10).mean()
        df["MA20"] = df["收盘"].rolling(20).mean()
        vol = df["成交量"].values
        vol_avg5 = df["成交量"].rolling(5).mean().iloc[-1]
        vol_ratio = round(float(vol[-1] / vol_avg5), 2) if vol_avg5 and vol_avg5 > 0 else 0

        latest = df.iloc[-1]
        logger.info(f"计算股票 {code} 技术指标成功")
        return {
            "status": "success",
            "code": code,
            "close": float(latest["收盘"]),
            "ma5": round(float(latest["MA5"]), 2),
            "ma10": round(float(latest["MA10"]), 2),
            "ma20": round(float(latest["MA20"]), 2),
            "vol_ratio": vol_ratio,
        }
    except Exception as e:
        logger.error(f"计算股票 {code} 技术指标失败: {e}")
        return {"status": "failed", "error": str(e)}
