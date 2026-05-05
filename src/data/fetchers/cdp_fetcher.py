"""
Chrome DevTools Protocol 数据采集器

关键发现 (2026-05-03):
  - Page.navigate 在已有 tab 上会阻塞后续命令直到页面 load 完成
  - 正确做法: 用 Target.createTarget 新开 tab，读完后关闭
  - 东财 dpzjlx.html 渲染后:
    - selector "table" → 主力/超大单/大单/中单/小单净流入
    - selector "[class*=marketData]" → 上证/深证 涨跌平
"""
import re
import logging
from typing import Dict, Optional

from .cdp_screenshot import (
    get_tab_ws,
    new_page,
    read_on_tab
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ─── 数据解析 ─────────────────────────────────────────────────────────────────

def _parse_money_flow(text: str) -> dict:
    patterns = [
        ("main_net_inflow",   r"今日主力净流入[：:\s]*([-]?\d+\.?\d*)\s*亿"),
        ("super_large_net",   r"今日超大单净流入[：:\s]*([-]?\d+\.?\d*)\s*亿"),
        ("large_net",         r"今日大单净流入[：:\s]*([-]?\d+\.?\d*)\s*亿"),
        ("medium_net",        r"今日中单净流入[：:\s]*([-]?\d+\.?\d*)\s*亿"),
        ("small_net",         r"今日小单净流入[：:\s]*([-]?\d+\.?\d*)\s*亿"),
    ]
    result = {}
    for field, pat in patterns:
        m = re.search(pat, text)
        result[field] = float(m.group(1)) if m else None
    return result


def _parse_market_data(text: str) -> dict:
    result = {"up_count": None, "down_count": None, "flat_count": None}
    m_up = re.search(r"涨[\\s:–-=]*(\d+)", text)
    m_flat = re.search(r"平[\\s:–-=]*(\d+)", text)
    m_down = re.search(r"跌[\\s:–-=]*(\d+)", text)
    if m_up:   result["up_count"]   = int(m_up.group(1))
    if m_flat: result["flat_count"] = int(m_flat.group(1))
    if m_down: result["down_count"] = int(m_down.group(1))
    return result


# ─── 主采集函数 ───────────────────────────────────────────────────────────────

def fetch_north_flow_cdp() -> dict:
    """
    CDP 读东财北向资金 dpzjlx.html
    数据: 主力/超大单/大单/中单/小单净流入 + 涨跌平
    """
    result = {
        "status": "failed",
        "source": "CDP:dpzjlx.html",
        "main_net_inflow": None, "super_large_net": None,
        "large_net": None, "medium_net": None, "small_net": None,
        "up_count": None, "down_count": None, "flat_count": None,
        "error": None,
    }

    # 找已有东财 tab
    ws_url = get_tab_ws(["data.eastmoney.com", "zjlx"])
    if not ws_url:
        logger.warning("未找到 Eastmoney tab")
        return {**result, "error": "无东财dpzjlx tab，请先在 Chrome 打开 https://data.eastmoney.com/zjlx/dpzjlx.html"}

    logger.info(f"找到 Eastmoney tab: {ws_url}")
    
    # 直接读已有 tab
    table_text = read_on_tab(ws_url, "table")
    market_text = read_on_tab(ws_url, "[class*=marketData]")

    # 如果 NOT_FOUND，开新 tab
    if not table_text or table_text == "NOT_FOUND":
        logger.info("现有 tab 未找到数据，尝试创建新 tab")
        page_id = new_page("https://data.eastmoney.com/zjlx/dpzjlx.html", wait=5.0)
        if page_id:
            import time
            time.sleep(2)
            ws_url_new = f"ws://127.0.0.1:9222/devtools/page/{page_id}"
            table_text = read_on_tab(ws_url_new, "table")
            market_text = read_on_tab(ws_url_new, "[class*=marketData]")

    # Parse
    if table_text and table_text != "NOT_FOUND":
        result.update(_parse_money_flow(table_text))

    if market_text and market_text != "NOT_FOUND":
        result.update(_parse_market_data(market_text))

    if any(result[k] is not None for k in
           ["main_net_inflow", "super_large_net", "up_count"]):
        result["status"] = "success"
        logger.info("CDP 采集成功")
    else:
        result["error"] = f"table={str(table_text)[:80]}, market={str(market_text)[:80]}"
        logger.error(f"CDP 采集失败: {result['error']}")

    return result


def fetch_market_sentiment_cdp() -> dict:
    r = fetch_north_flow_cdp()
    return {
        "status": r.get("status"),
        "source": "CDP:dpzjlx.html",
        "up_count": r.get("up_count"),
        "down_count": r.get("down_count"),
        "flat_count": r.get("flat_count"),
        "error": r.get("error"),
    }


def fetch_all() -> dict:
    north = fetch_north_flow_cdp()
    sentiment = {
        "status": north.get("status"),
        "source": "CDP:dpzjlx.html",
        "up_count": north.get("up_count"),
        "down_count": north.get("down_count"),
        "flat_count": north.get("flat_count"),
    }
    return {"north_flow_cdp": north, "market_sentiment_cdp": sentiment}
