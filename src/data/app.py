"""
StockExpert 数据 API + 前端页面
Flask 服务，端口 5789

路由:
  GET /                     — 前端看板页面
  GET /api/records           — 所有字段记录 ?date=YYYY-MM-DD&session=morning
  GET /api/fetch-log         — 采集日志   ?date=YYYY-MM-DD&session=morning
  GET /api/dates             — 有数据的日期列表
  GET /api/collect           — 触发全量采集（同步，约30秒）
  GET /api/field-list        — 字段定义列表（溯源用）
"""
import sys, os, sqlite3, json, datetime
from functools import wraps
from flask import Flask, render_template_string, request, jsonify

BASE = os.path.dirname(os.path.abspath(__file__))
# 统一DB路径：与db_writer.py保持一致
DB_PATH = "/mnt/c/Users/WINGO/Documents/WorkSpace/trading-system/data/stockexpert.db"

# 确保 src 路径在 sys.path（这样直接 python app.py 也能用 src.data.xxx 导入）
if BASE not in sys.path:
    sys.path.insert(0, BASE)

app = Flask(__name__,
            template_folder=os.path.join(BASE, "templates"),
            static_folder=None)
app.config["JSON_AS_ASCII"] = False
app.config["API_KEY"] = os.environ.get("FLASK_API_KEY", "")  # 空 = 不启用鉴权


def require_api_key(f):
    """API Key 鉴权装饰器。启用条件：FLASK_API_KEY 环境变量已设置。"""
    @wraps(f)
    def decorated(*args, **kwargs):
        expected = app.config.get("API_KEY", "")
        if expected:  # 只有设置了 key 才校验
            provided = request.headers.get("X-API-Key", "")
            if provided != expected:
                return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


# ─── Field definitions (溯源元数据) ───────────────────────────────────────────
FIELD_META = {
    # Index
    "index_chg_sh000001":  {"label": "上证指数涨跌幅",  "unit": "%",   "category": "指数", "source_pattern": "akshare"},
    "index_chg_sz399001":  {"label": "深证成指涨跌幅",  "unit": "%",   "category": "指数", "source_pattern": "akshare"},
    "index_chg_sz399006":  {"label": "创业板指涨跌幅",  "unit": "%",   "category": "指数", "source_pattern": "akshare"},
    "index_chg_sh000688":  {"label": "科创50涨跌幅",    "unit": "%",   "category": "指数", "source_pattern": "akshare"},
    # Pool
    "zt_pool_count":       {"label": "涨停家数",        "unit": "只",   "category": "涨停池", "source_pattern": "akshare"},
    "dt_pool_count":       {"label": "跌停家数",        "unit": "只",   "category": "跌停池", "source_pattern": "akshare"},
    # Zhangtingke
    "highest_board":       {"label": "最高连板",        "unit": "连板", "category": "连板", "source_pattern": "zhangtingke"},
    "break_board_rate":    {"label": "今炸板率",        "unit": "%",    "category": "炸板", "source_pattern": "zhangtingke"},
    "continue_board_count":{"label": "今连板数",        "unit": "只",   "category": "连板", "source_pattern": "zhangtingke"},
    "touched_not_sealed":  {"label": "触板未封",        "unit": "只",   "category": "炸板", "source_pattern": "zhangtingke"},
    "level_1_to_2":        {"label": "1进2晋级率",      "unit": "%",   "category": "晋级率", "source_pattern": "zhangtingke"},
    "level_2_to_3":        {"label": "2进3晋级率",      "unit": "%",   "category": "晋级率", "source_pattern": "zhangtingke"},
    "level_3_to_4":        {"label": "3进4晋级率",      "unit": "%",   "category": "晋级率", "source_pattern": "zhangtingke"},
    "level_4_to_5":        {"label": "4进5晋级率",      "unit": "%",   "category": "晋级率", "source_pattern": "zhangtingke"},
    # North flow CDP
    "main_net_inflow":     {"label": "主力净流入",       "unit": "亿元", "category": "资金流", "source_pattern": "CDP"},
    "super_large_net":     {"label": "超大单净流入",     "unit": "亿元", "category": "资金流", "source_pattern": "CDP"},
    "large_net":           {"label": "大单净流入",       "unit": "亿元", "category": "资金流", "source_pattern": "CDP"},
    "medium_net":          {"label": "中单净流入",       "unit": "亿元", "category": "资金流", "source_pattern": "CDP"},
    "small_net":           {"label": "小单净流入",       "unit": "亿元", "category": "资金流", "source_pattern": "CDP"},
    # North summary
    "hgt_net_inflow":      {"label": "沪股通净流入",    "unit": "亿元", "category": "北向", "source_pattern": "akshare"},
    "sgt_net_inflow":      {"label": "深股通净流入",    "unit": "亿元", "category": "北向", "source_pattern": "akshare"},
    # North history
    "north_net_inflow_latest": {"label": "北向历史最新", "unit": "亿元", "category": "北向历史", "source_pattern": "akshare"},
}


# ─── DB helpers ───────────────────────────────────────────────────────────────
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_to_dict(row):
    return dict(row)


# ─── API Routes ───────────────────────────────────────────────────────────────
@app.route("/api/field-list")
@require_api_key
def api_field_list():
    """返回所有字段的元数据"""
    return jsonify({"fields": FIELD_META})


@app.route("/api/dates")
@require_api_key
def api_dates():
    """返回有数据的日期列表"""
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT trade_date FROM data_records ORDER BY trade_date DESC"
    ).fetchall()
    conn.close()
    dates = [r["trade_date"] for r in rows]
    return jsonify({"dates": dates})


@app.route("/api/records")
@require_api_key
def api_records():
    """返回指定日期/时段的字段记录"""
    date = request.args.get("date", datetime.date.today().isoformat())
    session = request.args.get("session", "morning")

    conn = get_conn()
    rows = conn.execute("""
        SELECT field_name, field_value, source, fetch_time, status, error_message
        FROM data_records
        WHERE trade_date=? AND session=?
        ORDER BY field_name
    """, (date, session)).fetchall()
    conn.close()

    records = []
    for r in rows:
        d = row_to_dict(r)
        meta = FIELD_META.get(d["field_name"], {})
        d["label"] = meta.get("label", d["field_name"])
        d["unit"] = meta.get("unit", "")
        d["category"] = meta.get("category", "其他")
        d["source_pattern"] = meta.get("source_pattern", "")
        records.append(d)

    # 分类汇总
    categories = {}
    for rec in records:
        cat = rec.pop("category")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(rec)

    return jsonify({
        "date": date,
        "session": session,
        "records": records,
        "categories": categories,
        "total": len(records),
        "success_count": sum(1 for r in records if r["status"] == "success"),
        "failed_count": sum(1 for r in records if r["status"] != "success"),
    })


@app.route("/api/fetch-log")
@require_api_key
def api_fetch_log():
    """返回采集日志"""
    date = request.args.get("date", datetime.date.today().isoformat())
    session = request.args.get("session", "morning")

    conn = get_conn()
    rows = conn.execute("""
        SELECT fetcher, status, duration_ms, records_count, error_message, created_at
        FROM fetch_logs
        WHERE trade_date=? AND session=?
        ORDER BY created_at
    """, (date, session)).fetchall()
    conn.close()

    return jsonify({"logs": [row_to_dict(r) for r in rows]})


@app.route("/api/fetcher-logs")
@require_api_key
def api_fetcher_logs():
    """
    按 fetcher 名分组的日志，用于弹窗展示。
    同 fetcher 的所有记录（不同时间戳的多次采集）放在同一组。
    """
    date = request.args.get("date", datetime.date.today().isoformat())
    session = request.args.get("session", "morning")

    # CDP 来源映射：source → (中文名, 网址)
    CDP_SOURCES = {
        "CDP:dpzjlx.html": ("东方财富-个股资金流向", "https://data.eastmoney.com/zjlx/dpzjlx.html"),
    }

    conn = get_conn()
    rows = conn.execute("""
        SELECT fetcher, status, duration_ms, records_count, error_message, created_at
        FROM fetch_logs
        WHERE trade_date=? AND session=?
        ORDER BY fetcher, created_at
    """, (date, session)).fetchall()
    conn.close()

    # 按 fetcher 分组
    groups = {}
    for r in rows:
        fetcher = r["fetcher"]
        d = row_to_dict(r)
        # 解析 source_display
        if fetcher.startswith("cdp:"):
            cdp_key = fetcher  # e.g. "cdp:fetch_north_flow_cdp"
            # 从 error_message 里找 CDP: 前缀作为 source
            src = None
            em = d.get("error_message") or ""
            for k in CDP_SOURCES:
                if k in em or k in fetcher:
                    src = k
                    break
            if not src:
                src = "CDP:dpzjlx.html"
            info = CDP_SOURCES.get(src, ("CDP", ""))
            d["source_display"] = info[0]
            d["source_url"] = info[1]
            d["is_cdp"] = True
        elif fetcher.startswith("akshare:"):
            d["source_display"] = "akshare 金融数据库"
            d["source_url"] = "https://akshare.akfamily.xyz/"
            d["is_cdp"] = False
        elif fetcher.startswith("zhangtingke:"):
            d["source_display"] = "涨停狙击台"
            d["source_url"] = "https://www.zhangtingke.com"
            d["is_cdp"] = False
        else:
            d["source_display"] = fetcher.split(":")[0]
            d["source_url"] = ""
            d["is_cdp"] = False

        if fetcher not in groups:
            groups[fetcher] = {"fetcher": fetcher, "logs": []}
        groups[fetcher]["logs"].append(d)

    return jsonify({"groups": list(groups.values())})


def _cdp_screenshot_on_browser(url: str) -> bytes:
    """
    用 curl + Chrome DevTools HTTP API 创建 tab，然后 WebSocket 截屏。
    curl -X PUT http://127.0.0.1:9222/json/new?url=...  → 稳定创建新 tab
    """
    import sys as _sys, subprocess as _subprocess, time as _time
    _sys.path.insert(0, "/home/wingo/.hermes/hermes-agent/venv/lib/python3.11/site-packages")
    import websocket as _ws, json as _json, base64 as _b64

    try:
        # 1. 用 HTTP PUT 创建新 tab
        r = _subprocess.run(
            ["curl", "-s", "-X", "PUT",
             f"http://127.0.0.1:9222/json/new?url={url}"],
            capture_output=True, text=True, timeout=10
        )
        new_tab = _json.loads(r.stdout)
        ws_url = new_tab.get("webSocketDebuggerUrl")
        if not ws_url:
            return None

        # 等 SPA 加载
        _time.sleep(6)

        # 2. WebSocket 连接 tab 并截图
        tab_ws = _ws.create_connection(ws_url, timeout=10, suppress_origin=True)
        tab_ws.settimeout(15)
        tab_results = {}

        def _recv_tab():
            deadline = _time.time() + 20
            while _time.time() < deadline:
                try:
                    msg = tab_ws.recv()
                    if msg:
                        d = _json.loads(msg)
                        rid = d.get("id")
                        if rid is not None:
                            tab_results[rid] = d
                except Exception:
                    break

        import threading as _th
        t = _th.Thread(target=_recv_tab, daemon=True)
        t.start()

        tab_ws.send(_json.dumps({"id": 1, "method": "Runtime.enable"}))
        tab_ws.send(_json.dumps({"id": 2, "method": "Page.enable"}))
        _time.sleep(0.5)
        tab_ws.send(_json.dumps({
            "id": 10,
            "method": "Page.captureScreenshot",
            "params": {"format": "png", "quality": 80}
        }))

        deadline = _time.time() + 15
        while _time.time() < deadline:
            if 10 in tab_results:
                break
            _time.sleep(0.3)

        tab_ws.close()

        # Chrome CDP returns: {"id": 10, "result": {"data": "base64..."}}
        result = tab_results.get(10, {})
        data_str = result.get("result", {}).get("data")
        if data_str:
            return _b64.b64decode(data_str)
    except Exception:
        pass
    return None


@app.route("/api/cdp-screenshot")
@require_api_key
def api_cdp_screenshot():
    """
    对东财 dpzjlx.html tab 截屏并保存到 data/cdp_screenshots/。
    ?date=YYYY-MM-DD&session=morning
    """
    date = request.args.get("date", datetime.date.today().isoformat())
    session = request.args.get("session", "morning")

    screenshot_dir = os.path.join(BASE, "data", "cdp_screenshots")
    os.makedirs(screenshot_dir, exist_ok=True)

    filename = f"{date}_{session}.png"
    filepath = os.path.join(screenshot_dir, filename)

    # 如果已存在直接返回
    if os.path.exists(filepath):
        return jsonify({"ok": True, "path": filepath, "url": f"/cdp-screenshots/{filename}"})

    try:
        img_bytes = _cdp_screenshot_on_browser(
            "https://data.eastmoney.com/zjlx/dpzjlx.html"
        )
        if img_bytes:
            with open(filepath, "wb") as f:
                f.write(img_bytes)
            return jsonify({"ok": True, "path": filepath,
                           "url": f"/cdp-screenshots/{filename}"})
        return jsonify({"ok": False, "error": "截屏失败，tab可能未加载dpzjlx页面"})
    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()})


@app.route("/api/collect", methods=["GET"])
@require_api_key
def api_collect():
    """触发全量采集（约30秒）"""
    date = request.args.get("date", datetime.date.today().isoformat())
    session = request.args.get("session", "morning")

    try:
        from db_writer import DatabaseWriter
        from fetchers.akshare_fetcher import (
            fetch_index_quotes, fetch_limit_up_count, fetch_limit_down_count,
            fetch_north_flow_summary, fetch_north_hist,
        )
        from fetchers.zhangtingke_fetcher import fetch_all as fetch_zhangtingke
        from fetchers.cdp_fetcher import fetch_north_flow_cdp

        # 采集
        ax = {}
        ax["index_quotes"] = fetch_index_quotes()
        ax["limit_up"] = fetch_limit_up_count()
        ax["limit_down"] = fetch_limit_down_count()
        ax["north_summary"] = fetch_north_flow_summary()
        ax["north_hist"] = fetch_north_hist()

        zt = {"today": fetch_zhangtingke()}
        cdp_r = {"north_flow": fetch_north_flow_cdp()}

        # 写入
        db = DatabaseWriter()
        ok, msg = db.write_all(date, session, ax, zt, cdp_r)
        db.close()

        return jsonify({"ok": ok, "message": msg})
    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e), "trace": traceback.format_exc()})


# ─── Frontend ─────────────────────────────────────────────────────────────────
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>StockExpert 数据看板</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, 'PingFang SC', 'Microsoft YaHei', sans-serif;
         background: #0d1117; color: #e6edf3; font-size: 14px; }

  header { background: #161b22; border-bottom: 1px solid #30363d; padding: 14px 24px;
           display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
  h1 { font-size: 18px; font-weight: 600; color: #58a6ff; }
  .tab-nav { display: flex; gap: 4px; margin-left: 24px; }
  .tab-link { background: #21262d; color: #8b949e; border: 1px solid #30363d;
              border-radius: 6px; padding: 5px 14px; font-size: 13px;
              text-decoration: none; }
  .tab-link:hover { color: #e6edf3; }
  .tab-link.active { background: #1f6feb; border-color: #1f6feb; color: #fff; }
  .header-controls { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
  select, button { background: #21262d; color: #e6edf3; border: 1px solid #30363d;
                    border-radius: 6px; padding: 5px 12px; font-size: 13px; cursor: pointer; }
  button { background: #238636; border-color: #238636; }
  button:hover { background: #2ea043; }
  button.collect { background: #1f6feb; border-color: #1f6feb; }
  button.collect:hover { background: #388bfd; }
  button.collect:disabled { background: #484f58; border-color: #484f58; cursor: not-allowed; }
  .status-bar { font-size: 12px; color: #8b949e; margin-left: auto; }

  .summary-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
                   gap: 12px; padding: 16px 24px; }
  .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px;
          padding: 14px 16px; }
  .card-label { font-size: 12px; color: #8b949e; margin-bottom: 6px; }
  .card-value { font-size: 22px; font-weight: 700;
                color: #79c0ff; font-variant-numeric: tabular-nums; }
  .card-value.up { color: #f85149; }
  .card-value.down { color: #3fb950; }
  .card-value.warn { color: #d29922; }
  .card-source { font-size: 10px; color: #484f58; margin-top: 4px; }

  .main { display: grid; grid-template-columns: 1fr 320px; gap: 16px; padding: 0 24px 24px; }
  .section { background: #161b22; border: 1px solid #30363d; border-radius: 8px;
             overflow: hidden; }
  .section-header { background: #21262d; padding: 10px 16px; font-size: 13px;
                     font-weight: 600; border-bottom: 1px solid #30363d;
                     display: flex; align-items: center; gap: 8px; }
  .badge { background: #238636; color: #fff; border-radius: 10px; padding: 1px 7px;
           font-size: 11px; font-weight: 400; }
  .badge.warn { background: #d29922; }
  .badge.fail { background: #f85149; }

  table { width: 100%; border-collapse: collapse; }
  th { background: #21262d; color: #8b949e; font-size: 11px; text-align: left;
       padding: 8px 12px; border-bottom: 1px solid #30363d; font-weight: 400; }
  td { padding: 9px 12px; border-bottom: 1px solid #21262d; font-size: 13px; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #1c2128; }
  .field-name { color: #e6edf3; }
  .field-value { color: #79c0ff; font-variant-numeric: tabular-nums; font-weight: 600; }
  .source-tag { font-size: 10px; color: #484f58; font-family: monospace; }
  .status-dot { display: inline-block; width: 6px; height: 6px; border-radius: 50%;
                 margin-right: 5px; }
  .status-dot.ok { background: #3fb950; }
  .status-dot.fail { background: #f85149; }

  .log-list { padding: 8px 0; }
  .log-item { display: flex; align-items: center; gap: 8px; padding: 7px 16px;
              font-size: 12px; border-bottom: 1px solid #21262d; }
  .log-item:last-child { border-bottom: none; }
  .log-fetcher { color: #e6edf3; flex: 1; }
  .log-status { font-size: 11px; }

  .tabs { display: flex; border-bottom: 1px solid #30363d; }
  .tab { padding: 8px 16px; font-size: 13px; cursor: pointer; color: #8b949e;
         border-bottom: 2px solid transparent; margin-bottom: -1px; }
  .tab.active { color: #e6edf3; border-bottom-color: #58a6ff; }

  .empty { text-align: center; color: #484f58; padding: 40px; font-size: 13px; }
  .loading { text-align: center; color: #484f58; padding: 20px; }

  .toast { position: fixed; bottom: 20px; right: 20px; background: #21262d;
           border: 1px solid #30363d; border-radius: 8px; padding: 10px 16px;
           font-size: 13px; z-index: 999; display: none; }
  .toast.ok { border-color: #3fb950; color: #3fb950; }
  .toast.fail { border-color: #f85149; color: #f85149; }

  /* 弹窗 */
  .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7);
                   z-index: 1000; display: none; align-items: center;
                   justify-content: center; }
  .modal-overlay.show { display: flex; }
  .modal { background: #161b22; border: 1px solid #30363d; border-radius: 12px;
           width: 680px; max-width: 95vw; max-height: 80vh; display: flex;
           flex-direction: column; }
  .modal-header { padding: 14px 20px; border-bottom: 1px solid #30363d;
                  display: flex; align-items: center; justify-content: space-between; }
  .modal-title { font-size: 15px; font-weight: 600; color: #e6edf3; }
  .modal-close { background: none; border: none; color: #8b949e; font-size: 20px;
                 cursor: pointer; padding: 0 4px; }
  .modal-close:hover { color: #e6edf3; }
  .modal-body { padding: 16px 20px; overflow-y: auto; flex: 1; }
  .modal-note { font-size: 12px; color: #8b949e; margin-bottom: 12px; }
  .modal-table { width: 100%; border-collapse: collapse; }
  .modal-table th { background: #21262d; color: #8b949e; font-size: 11px;
                    text-align: left; padding: 7px 10px; font-weight: 400;
                    border-bottom: 1px solid #30363d; }
  .modal-table td { padding: 8px 10px; border-bottom: 1px solid #21262d;
                    font-size: 12px; color: #c9d1d9; }
  .modal-table tr:last-child td { border-bottom: none; }
  .modal-table .mono { font-family: monospace; color: #79c0ff; }
  .modal-table .err { color: #f85149; font-size: 11px; }
  .modal-empty { text-align: center; color: #484f58; padding: 30px; }
</style>
</head>
<body>

<header>
  <h1>📊 StockExpert</h1>
  <nav class="tab-nav">
    <a class="tab-link active" href="/">数据看板</a>
    <a class="tab-link" href="/trade-log">交易日志</a>
    <a class="tab-link" href="/strategy-review">策略评估</a>
    <a class="tab-link" href="/orchestrator">编排器</a>
  </nav>
  <div class="header-controls">
    <select id="dateSelect"></select>
    <select id="sessionSelect">
      <option value="morning">晨报</option>
      <option value="noon">午盘</option>
      <option value="close">收评</option>
    </select>
    <button class="collect" id="collectBtn" onclick="triggerCollect()">🔄 采集数据</button>
    <button onclick="loadData()">↻ 刷新</button>
    <span class="status-bar" id="statusBar">—</span>
  </div>
</header>

<!-- KPI 卡片 -->
<div class="summary-cards" id="summaryCards">
  <div class="loading">加载中…</div>
</div>

<div class="main">
  <!-- 左：字段详情表 -->
  <div class="section">
    <div class="tabs">
      <div class="tab active" data-cat="all" onclick="switchTab(this)">全部</div>
      <div class="tab" data-cat="指数" onclick="switchTab(this)">指数</div>
      <div class="tab" data-cat="涨停池" onclick="switchTab(this)">涨停池</div>
      <div class="tab" data-cat="连板" onclick="switchTab(this)">连板</div>
      <div class="tab" data-cat="炸板" onclick="switchTab(this)">炸板</div>
      <div class="tab" data-cat="晋级率" onclick="switchTab(this)">晋级率</div>
      <div class="tab" data-cat="资金流" onclick="switchTab(this)">资金流</div>
      <div class="tab" data-cat="北向" onclick="switchTab(this)">北向</div>
    </div>
    <div id="recordsTable">
      <div class="empty">选择日期后点击「刷新」</div>
    </div>
  </div>

  <!-- 右：采集日志 -->
  <div class="section">
    <div class="section-header">📋 采集日志</div>
    <div class="log-list" id="logList">
      <div class="empty">—</div>
    </div>
  </div>
</div>

<div class="toast" id="toast"></div>

<!-- 采集日志详情弹窗 -->
<div class="modal-overlay" id="modalOverlay" onclick="closeModal(event)">
  <div class="modal" onclick="event.stopPropagation()">
    <div class="modal-header">
      <span class="modal-title" id="modalTitle">采集日志详情</span>
      <button class="modal-close" onclick="closeModal()">×</button>
    </div>
    <div class="modal-body" id="modalBody"></div>
  </div>
</div>

<script>
const API = '';
let currentData = null;
let currentCat = 'all';
let fetcherGroups = [];

async function api(url) {
  const r = await fetch(API + url);
  return r.json();
}

async function loadDates() {
  const { dates } = await api('/api/dates');
  const sel = document.getElementById('dateSelect');
  sel.innerHTML = '';
  dates.forEach(d => {
    const opt = document.createElement('option');
    opt.value = d;
    opt.textContent = d;
    sel.appendChild(opt);
  });
  if (dates.length > 0) loadData();
}

async function loadData() {
  const date = document.getElementById('dateSelect').value;
  const session = document.getElementById('sessionSelect').value;
  document.getElementById('statusBar').textContent = '加载中…';
  try {
    const [recData, logData] = await Promise.all([
      api(`/api/records?date=${date}&session=${session}`),
      api(`/api/fetch-log?date=${date}&session=${session}`),
    ]);
    // 同时加载分组日志（用于弹窗）
    const groupedData = await api(`/api/fetcher-logs?date=${date}&session=${session}`);
    fetcherGroups = groupedData.groups || [];

    currentData = recData;
    renderCards(recData);
    renderTable(recData.records, currentCat);
    renderLog(logData.logs);
    document.getElementById('statusBar').textContent =
      `${date} ${session} | ${recData.success_count}/${recData.total} 字段成功 | ${logData.logs.length} 条采集日志`;
  } catch(e) {
    showToast('加载失败: ' + e.message, 'fail');
  }
}

function renderCards(data) {
  const el = document.getElementById('summaryCards');
  const kv = {
    '上证指数': findVal(data, 'index_chg_sh000001'),
    '深证成指': findVal(data, 'index_chg_sz399001'),
    '创业板指': findVal(data, 'index_chg_sz399006'),
    '科创50':   findVal(data, 'index_chg_sh000688'),
    '涨停家数': findVal(data, 'zt_pool_count'),
    '跌停家数': findVal(data, 'dt_pool_count'),
    '最高连板': findVal(data, 'highest_board'),
    '今炸板率': findVal(data, 'break_board_rate'),
    '主力净流入': findVal(data, 'main_net_inflow'),
  };
  let html = '';
  for (const [label, item] of Object.entries(kv)) {
    if (!item) continue;
    let cls = 'card-value';
    if (item.value !== null && !isNaN(item.value)) {
      const v = parseFloat(item.value);
      if (label.includes('指数') || label.includes('炸板')) cls += v > 0 ? ' up' : v < 0 ? ' down' : '';
      else if (label.includes('主力')) cls += v > 0 ? ' down' : v < 0 ? ' up' : ' warn';
    }
    const src = item.source || '';
    html += `<div class="card">
      <div class="card-label">${label}</div>
      <div class="${cls}">${item.value !== null ? item.value : '—'}${item.unit || ''}</div>
      <div class="card-source">${src}</div>
    </div>`;
  }
  el.innerHTML = html || '<div class="empty">暂无数据</div>';
}

function findVal(data, field) {
  const rec = (data.records || []).find(r => r.field_name === field);
  if (!rec) return null;
  return { value: rec.field_value, unit: rec.unit || '', source: rec.source || '' };
}

function renderTable(records, cat) {
  const el = document.getElementById('recordsTable');
  const filtered = cat === 'all' ? records : records.filter(r => r.category === cat);
  if (!filtered.length) {
    el.innerHTML = `<div class="empty">该分类暂无数据</div>`;
    return;
  }
  let html = `<table>
    <thead><tr>
      <th>字段</th><th>数值</th><th>来源</th><th>状态</th>
    </tr></thead><tbody>`;
  for (const r of filtered) {
    const dot = r.status === 'success'
      ? '<span class="status-dot ok"></span>'
      : '<span class="status-dot fail"></span>';
    const val = r.field_value !== null ? r.field_value : '—';
    const src = r.source || '';
    html += `<tr>
      <td class="field-name">${dot}${r.label}</td>
      <td class="field-value">${val}${r.unit || ''}</td>
      <td class="source-tag">${src}</td>
      <td><span class="badge ${r.status === 'success' ? '' : r.status === 'partial' ? 'warn' : 'fail'}">${r.status}</span></td>
    </tr>`;
  }
  html += '</tbody></table>';
  el.innerHTML = html;
}

function renderLog(logs) {
  const el = document.getElementById('logList');
  if (!logs.length) { el.innerHTML = '<div class="empty">暂无日志</div>'; return; }

  // 按 fetcher 分组展示（仅显示最后一次的状态，行可点击）
  // 从 fetcherGroups 取数据，fetcherGroups 在 loadData 时已加载
  if (fetcherGroups.length === 0) {
    // fallback：兜底显示
    let html = '';
    for (const l of logs) {
      const dot = l.status === 'success'
        ? '<span class="status-dot ok"></span>'
        : '<span class="status-dot fail"></span>';
      const badge = l.status === 'success' ? '' : l.status === 'partial' ? 'warn' : 'fail';
      html += `<div class="log-item">
        ${dot}<span class="log-fetcher">${l.fetcher}</span>
        <span class="log-status"><span class="badge ${badge}">${l.status}</span></span>
      </div>`;
    }
    el.innerHTML = html;
    return;
  }

  let html = '';
  for (const group of fetcherGroups) {
    const lastLog = group.logs[group.logs.length - 1];
    const dot = lastLog.status === 'success'
      ? '<span class="status-dot ok"></span>'
      : '<span class="status-dot fail"></span>';
    const badge = lastLog.status === 'success' ? '' : lastLog.status === 'partial' ? 'warn' : 'fail';
    const count = group.logs.length;
    const cursor = count > 1
      ? `<span style="color:#58a6ff;font-size:10px;margin-left:4px;cursor:pointer;text-decoration:underline" onclick="openFetcherModal('${group.fetcher}')">${count}次</span>`
      : '';
    html += `<div class="log-item" style="cursor:pointer" onclick="openFetcherModal('${group.fetcher}')">
      ${dot}<span class="log-fetcher">${group.fetcher}${cursor}</span>
      <span class="log-status"><span class="badge ${badge}">${lastLog.status}</span></span>
    </div>`;
  }
  el.innerHTML = html;
}

function switchTab(tab) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  tab.classList.add('active');
  currentCat = tab.dataset.cat;
  if (currentData) renderTable(currentData.records, currentCat);
}

async function triggerCollect() {
  const date = document.getElementById('dateSelect').value;
  const session = document.getElementById('sessionSelect').value;
  const btn = document.getElementById('collectBtn');
  btn.disabled = true;
  btn.textContent = '采集中…';
  showToast('开始采集，约30秒…', 'ok');
  try {
    const result = await api(`/api/collect?date=${date}&session=${session}`);
    if (result.ok) {
      showToast('采集成功！', 'ok');
      loadData();
    } else {
      showToast('采集失败: ' + (result.error || result.message), 'fail');
    }
  } catch(e) {
    showToast('采集请求失败: ' + e.message, 'fail');
  } finally {
    btn.disabled = false;
    btn.textContent = '🔄 采集数据';
  }
}

function showToast(msg, type) {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = 'toast ' + type;
  el.style.display = 'block';
  setTimeout(() => el.style.display = 'none', 3500);
}

function openFetcherModal(fetcher) {
  const group = fetcherGroups.find(g => g.fetcher === fetcher);
  if (!group) return;

  const firstLog = group.logs[group.logs.length - 1]; // 最后一次（最新的）
  const isCdp = firstLog.is_cdp || false;
  const srcDisplay = firstLog.source_display || '';
  const srcUrl = firstLog.source_url || '';

  document.getElementById('modalTitle').textContent = '📋 ' + fetcher;
  const body = document.getElementById('modalBody');

  // 来源信息区块
  let srcHtml = `<div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;padding:8px 12px;background:#21262d;border-radius:6px;font-size:12px;">
    <span style="color:#8b949e">数据来源:</span>
    <span style="color:#e6edf3;font-weight:600">${srcDisplay}</span>
    ${srcUrl ? `<a href="${srcUrl}" target="_blank" style="color:#58a6ff;font-size:11px;text-decoration:none">🔗 查看官网 →</a>` : ''}
    <span style="margin-left:auto;font-size:10px;color:#484f58">${isCdp ? '🖥️ CDP动态渲染' : '📡 API直连'}</span>
  </div>`;

  // CDP 截图（异步加载）
  let screenshotHtml = `<div id="screenshotArea" style="margin-bottom:14px;display:none">
    <div style="font-size:11px;color:#8b949e;margin-bottom:6px">🖥️ 数据来源截图</div>
    <img id="cdpScreenshot" style="max-width:100%;border-radius:6px;border:1px solid #30363d;display:none">
    <div id="screenshotLoading" style="color:#484f58;font-size:12px;padding:10px 0">正在截取来源页面…</div>
    <div id="screenshotError" style="color:#f85149;font-size:12px;padding:10px 0;display:none"></div>
  </div>`;

  let tableHtml = `<table class="modal-table">
    <thead><tr>
      <th>#</th><th>状态</th><th>耗时</th><th>记录数</th><th>错误信息</th><th>采集时间</th>
    </tr></thead><tbody>`;

  [...group.logs].reverse().forEach((log, i) => {
    const badge = log.status === 'success' ? 'badge' : log.status === 'partial' ? 'badge warn' : 'badge fail';
    const err = log.error_message
      ? `<span class="err" title="${escHtml(log.error_message)}">${escHtml(log.error_message.slice(0,40))}${log.error_message.length > 40 ? '…' : ''}</span>`
      : '—';
    const duration = log.duration_ms != null ? log.duration_ms + 'ms' : '—';
    tableHtml += `<tr>
      <td class="mono">${i + 1}</td>
      <td><span class="${badge}">${log.status}</span></td>
      <td class="mono">${duration}</td>
      <td class="mono">${log.records_count ?? '—'}</td>
      <td>${err}</td>
      <td class="mono" style="font-size:11px;color:#8b949e">${log.created_at || '—'}</td>
    </tr>`;
  });
  tableHtml += '</tbody></table>';

  body.innerHTML = srcHtml + screenshotHtml + tableHtml;
  document.getElementById('modalOverlay').classList.add('show');

  // CDP 类型：异步加载截图
  if (isCdp) {
    const date = document.getElementById('dateSelect').value;
    const session = document.getElementById('sessionSelect').value;
    const area = document.getElementById('screenshotArea');
    area.style.display = 'block';
    fetch(`/api/cdp-screenshot?date=${date}&session=${session}`)
      .then(r => r.json())
      .then(data => {
        if (data.ok) {
          const img = document.getElementById('cdpScreenshot');
          img.src = data.url + '?t=' + Date.now(); // 防止缓存
          img.style.display = 'block';
          document.getElementById('screenshotLoading').style.display = 'none';
        } else {
          document.getElementById('screenshotLoading').style.display = 'none';
          const err = document.getElementById('screenshotError');
          err.textContent = '截图失败: ' + (data.error || '未知错误');
          err.style.display = 'block';
        }
      })
      .catch(e => {
        document.getElementById('screenshotLoading').style.display = 'none';
        const err = document.getElementById('screenshotError');
        err.textContent = '截图请求失败: ' + e.message;
        err.style.display = 'block';
      });
  }
}

function closeModal(e) {
  if (e && e.target !== document.getElementById('modalOverlay')) return;
  document.getElementById('modalOverlay').classList.remove('show');
}

function escHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// Init
document.getElementById('sessionSelect').addEventListener('change', loadData);
document.getElementById('dateSelect').addEventListener('change', loadData);
loadDates();
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


app.route("/cdp-screenshots/<path:filename>")
def cdp_screenshot_file(filename):
    """提供截图静态文件"""
    from flask import send_from_directory
    return send_from_directory(os.path.join(BASE, "data", "cdp_screenshots"), filename)


# 注册 API 蓝图
import sys, os as _os
_data_dir = _os.path.dirname(_os.path.abspath(__file__))
if _data_dir not in sys.path:
    sys.path.insert(0, _data_dir)

from api_trades import trades_bp
from api_strategy import strategy_bp
from api_orchestrator import orchestrator_bp
app.register_blueprint(trades_bp)
app.register_blueprint(strategy_bp)
app.register_blueprint(orchestrator_bp)


# ─── 新增页面路由 ─────────────────────────────────────────────────────────────
@app.route("/trade-log")
def trade_log_page():
    from flask import render_template
    return render_template("trade_log.html")


@app.route("/strategy-review")
def strategy_review_page():
    from flask import render_template
    return render_template("strategy_review.html")


@app.route("/orchestrator")
def orchestrator_page():
    from flask import render_template
    return render_template("orchestrator.html")


if __name__ == "__main__":
    # 确保 data 目录存在
    os.makedirs(os.path.join(BASE, "data"), exist_ok=True)
    # 截图目录也要创建
    os.makedirs(os.path.join(BASE, "data", "cdp_screenshots"), exist_ok=True)
    app.run(host="0.0.0.0", port=5789, debug=False)
