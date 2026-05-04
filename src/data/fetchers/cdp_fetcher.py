"""
Chrome CDP 数据采集器

关键发现 (2026-05-03):
  - Page.navigate 在已有 tab 上会阻塞后续命令直到页面 load 完成
  - 正确做法: 用 Target.createTarget 新开 tab，读完后关闭
  - 东财 dpzjlx.html 渲染后:
    - selector "table" → 主力/超大单/大单/中单/小单净流入
    - selector "[class*=marketData]" → 上证/深证 涨跌平
"""
import re, time, json, subprocess
import websocket  # pip install websocket-client


# ─── Browser WS 动态发现 ──────────────────────────────────────────────────────

_BROWSER_WS: str = ""


def _get_browser_ws() -> str:
    """
    从 Chrome CDP HTTP 端点动态发现 browser WebSocket URL。
    每次调用都重新查询，避免硬编码 Browser Context ID。
    """
    global _BROWSER_WS
    if _BROWSER_WS:
        return _BROWSER_WS
    try:
        r = subprocess.run(
            ["curl", "-s", "http://127.0.0.1:9222/json/version"],
            capture_output=True, text=True, timeout=5
        )
        info = json.loads(r.stdout)
        ws_url = info.get("webSocketDebuggerUrl", "")
        if ws_url:
            _BROWSER_WS = ws_url
            return ws_url
    except Exception:
        pass
    return ""


# ─── Tab 发现 ────────────────────────────────────────────────────────────────

def _get_tab_ws(patterns=("eastmoney",)):
    """从 Chrome CDP 找指定 URL 的 tab WebSocket URL"""
    try:
        r = subprocess.run(
            ["curl", "-s", "http://127.0.0.1:9222/json"],
            capture_output=True, text=True, timeout=5
        )
        tabs = json.loads(r.stdout)
        for t in tabs:
            url = t.get("url", "")
            if any(p in url for p in patterns):
                return t.get("webSocketDebuggerUrl")
    except Exception:
        pass
    return None


# ─── 核心 CDP 操作 ───────────────────────────────────────────────────────────

def _new_page(url: str, wait: float = 5.0) -> str:
    """
    用 Target.createTarget 在 Browser WS 上新建 tab，返回 pageId。
    页面加载完后 tab 留在内存，可以复用。
    """
    browser_ws = _get_browser_ws()
    if not browser_ws:
        return ""
    try:
        ws = websocket.create_connection(browser_ws, timeout=10, suppress_origin=True)
        ws.settimeout(15)

        results = {}

        def recv():
            ws.settimeout(15)
            deadline = time.time() + 20
            while time.time() < deadline:
                try:
                    msg = ws.recv()
                    if msg:
                        d = json.loads(msg)
                        rid = d.get("id")
                        if rid is not None:
                            results[rid] = d
                        if d.get("method") == "Target.attachedToTarget":
                            results["_new_tab"] = d["params"]["targetInfo"]["targetId"]
                except Exception:
                    break

        import threading
        t = threading.Thread(target=recv, daemon=True)
        t.start()

        ws.send(json.dumps({
            "id": 1,
            "method": "Target.createTarget",
            "params": {"url": url, "browserContextId": None}
        }))

        deadline = time.time() + wait + 5
        while time.time() < deadline:
            if results.get("_new_tab"):
                break
            time.sleep(0.2)

        page_id = results.get("_new_tab")
        ws.close()
        time.sleep(wait)
        return page_id or ""
    except Exception:
        return ""


def _read_on_tab(ws_url: str, selector: str) -> str:
    """
    在已有 tab 上读 selector.innerText（tab 已加载完页面）。
    返回 innerText 或 None。
    """
    try:
        ws = websocket.create_connection(ws_url, timeout=8, suppress_origin=True)
        ws.settimeout(8)
        results = {}

        def recv():
            ws.settimeout(8)
            deadline = time.time() + 12
            while time.time() < deadline:
                try:
                    msg = ws.recv()
                    if msg:
                        d = json.loads(msg)
                        rid = d.get("id")
                        if rid is not None:
                            results[rid] = d
                except Exception:
                    break

        import threading
        t = threading.Thread(target=recv, daemon=True)
        t.start()

        ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        ws.send(json.dumps({"id": 2, "method": "Page.enable"}))
        time.sleep(0.3)

        expr = (
            f'document.querySelector("{selector}") '
            f'? document.querySelector("{selector}").innerText.slice(0,1000) '
            f': "NOT_FOUND"'
        )
        ws.send(json.dumps({
            "id": 10,
            "method": "Runtime.evaluate",
            "params": {"expression": expr, "returnByValue": True}
        }))

        deadline = time.time() + 12
        while time.time() < deadline:
            if 10 in results:
                break
            time.sleep(0.2)

        ws.close()
        r = results.get(10, {})
        val = r.get("result", {})
        if isinstance(val, dict):
            return val.get("result", {}).get("value")
        return None
    except Exception:
        return None


def _read_on_page(page_id: str, selector: str) -> str:
    """用 page_id 拼接 ws_url 并读取"""
    return _read_on_tab(f"ws://127.0.0.1:9222/devtools/page/{page_id}", selector)


# ─── 数据解析 ────────────────────────────────────────────────────────────────

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


# ─── 主采集函数 ──────────────────────────────────────────────────────────────

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
    ws_url = _get_tab_ws(["data.eastmoney.com", "zjlx"])
    if not ws_url:
        return {**result, "error": "无东财dpzjlx tab，请先在 Chrome 打开 https://data.eastmoney.com/zjlx/dpzjlx.html"}

    # 直接读已有 tab
    table_text = _read_on_tab(ws_url, "table")
    market_text = _read_on_tab(ws_url, "[class*=marketData]")

    # 如果 NOT_FOUND，开新 tab
    if not table_text or table_text == "NOT_FOUND":
        page_id = _new_page("https://data.eastmoney.com/zjlx/dpzjlx.html", wait=5.0)
        if page_id:
            time.sleep(2)
            ws_url_new = f"ws://127.0.0.1:9222/devtools/page/{page_id}"
            table_text = _read_on_tab(ws_url_new, "table")
            market_text = _read_on_tab(ws_url_new, "[class*=marketData]")

    # Parse
    if table_text and table_text != "NOT_FOUND":
        result.update(_parse_money_flow(table_text))

    if market_text and market_text != "NOT_FOUND":
        result.update(_parse_market_data(market_text))

    if any(result[k] is not None for k in
           ["main_net_inflow", "super_large_net", "up_count"]):
        result["status"] = "success"
    else:
        result["error"] = f"table={str(table_text)[:80]}, market={str(market_text)[:80]}"

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
