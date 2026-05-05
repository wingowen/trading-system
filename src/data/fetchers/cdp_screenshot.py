"""
Chrome DevTools Protocol 截图模块
独立封装，避免 app.py 内联代码过多
"""
import re
import time
import json
import subprocess
import websocket
import logging
from typing import Optional, Dict, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def get_browser_ws(force_refresh: bool = False) -> str:
    """
    从 Chrome CDP HTTP 端点动态发现 browser WebSocket URL

    Args:
        force_refresh: 是否强制刷新浏览器 WS 地址
    """
    # 避免全局缓存导致 stale 连接
    try:
        r = subprocess.run(
            ["curl", "-s", "http://127.0.0.1:9222/json/version"],
            capture_output=True, text=True, timeout=5
        )
        info = json.loads(r.stdout)
        ws_url = info.get("webSocketDebuggerUrl", "")
        if ws_url:
            logger.debug(f"发现浏览器 WebSocket 地址: {ws_url}")
            return ws_url
    except Exception as e:
        logger.warning(f"获取浏览器 WebSocket 地址失败: {str(e)}")
    return ""


def get_tab_ws(patterns: tuple = ("eastmoney",)) -> Optional[str]:
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
                logger.debug(f"找到匹配的 tab: {url}")
                return t.get("webSocketDebuggerUrl")
    except Exception as e:
        logger.warning(f"获取 tab WebSocket 地址失败: {str(e)}")
    return None


def read_on_tab(ws_url: str, selector: str) -> Optional[str]:
    """
    在已有 tab 上读 selector.innerText（tab 已加载完页面）
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
    except Exception as e:
        logger.error(f"读取 tab 内容失败: {str(e)}")
        return None


def new_page(url: str, wait: float = 5.0) -> Optional[str]:
    """
    用 Target.createTarget 在 Browser WS 上新建 tab，返回 pageId

    注意：pageId 可以用于构造 ws://127.0.0.1:9222/devtools/page/{pageId}
    """
    browser_ws = get_browser_ws()
    if not browser_ws:
        return None
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
        logger.debug(f"成功创建新页面: {page_id}")
        return page_id
    except Exception as e:
        logger.error(f"创建新页面失败: {str(e)}")
        return None


def take_screenshot(url: str = "https://data.eastmoney.com/zjlx/dpzjlx.html") -> Optional[bytes]:
    """
    对指定 URL 页面进行截图

    流程：
    1. 找已有 tab
    2. 如果没有，创建新 tab
    3. 截图返回 bytes
    """
    # 找已有东财 tab
    ws_url = get_tab_ws(["data.eastmoney.com", "zjlx"])
    if not ws_url:
        logger.info("未找到已有 Eastmoney tab，尝试创建新 tab")
        page_id = new_page(url, wait=6.0)
        if page_id:
            ws_url = f"ws://127.0.0.1:9222/devtools/page/{page_id}"

    if not ws_url:
        logger.error("无法获取有效的 tab WebSocket 地址")
        return None

    # 开始截图
    try:
        ws = websocket.create_connection(ws_url, timeout=10, suppress_origin=True)
        ws.settimeout(15)
        tab_results = {}

        def recv_tab():
            deadline = time.time() + 20
            while time.time() < deadline:
                try:
                    msg = ws.recv()
                    if msg:
                        d = json.loads(msg)
                        rid = d.get("id")
                        if rid is not None:
                            tab_results[rid] = d
                except Exception:
                    break

        import threading
        t = threading.Thread(target=recv_tab, daemon=True)
        t.start()

        ws.send(json.dumps({"id": 1, "method": "Runtime.enable"}))
        ws.send(json.dumps({"id": 2, "method": "Page.enable"}))
        time.sleep(0.5)
        ws.send(json.dumps({
            "id": 10,
            "method": "Page.captureScreenshot",
            "params": {"format": "png", "quality": 80}
        }))

        deadline = time.time() + 15
        while time.time() < deadline:
            if 10 in tab_results:
                break
            time.sleep(0.3)

        ws.close()

        # Chrome CDP returns: {"id": 10, "result": {"data": "base64..."}}
        result = tab_results.get(10, {})
        data_str = result.get("result", {}).get("data")
        if data_str:
            import base64
            return base64.b64decode(data_str)
    except Exception as e:
        logger.error(f"截图失败: {str(e)}")
    return None
