"""
交易日志 API
路由: GET/POST /api/trades, GET/PUT /api/trades/<trade_id>, GET /api/trades/summary
"""
import os
from flask import Blueprint, request, jsonify
from functools import wraps
from .evolution.trade_journal import TradeJournal

_api_key = os.environ.get("FLASK_API_KEY", "")


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if _api_key:
            if request.headers.get("X-API-Key", "") != _api_key:
                return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


trades_bp = Blueprint("trades", __name__)
_journal = TradeJournal()


@trades_bp.route("/api/trades", methods=["GET"])
@require_api_key
def api_list():
    """查询交易记录列表（分页/过滤）"""
    status = request.args.get("status", "all")
    if status == "all":
        status = None
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    sector = request.args.get("sector")
    pattern = request.args.get("pattern")
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
    except ValueError:
        return jsonify({"error": "invalid page/page_size"}), 400

    result = _journal.query_trades(
        status=status,
        start_date=start_date,
        end_date=end_date,
        sector=sector,
        pattern=pattern,
        page=page,
        page_size=page_size,
    )
    summary = _journal.get_summary()
    result["summary"] = summary
    return jsonify(result)


@trades_bp.route("/api/trades", methods=["POST"])
@require_api_key
def api_entry():
    """录入入场记录"""
    data = request.get_json(silent=True) or {}
    required = ["trade_id", "code", "buy_price", "buy_date"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"missing field: {field}"}), 400

    # 自动填入当日市场评分（从 db_reader 读取）
    buy_date = data.get("buy_date", "")
    if buy_date and not data.get("market_env_score"):
        try:
            from db_reader import get_field
            idx_chg = get_field(buy_date, "index_chg_sh000001", "morning")
            if idx_chg is not None:
                data["market_env_score"] = round(float(idx_chg) * 10 + 50, 1)
        except Exception:
            pass  # 无法获取则留空

    result = _journal.record_entry(data)
    status_code = 200 if result["status"] == "success" else 400
    return jsonify(result), status_code


@trades_bp.route("/api/trades/<trade_id>", methods=["GET"])
@require_api_key
def api_get(trade_id):
    """获取单笔交易详情"""
    result = _journal.get_trade(trade_id)
    status_code = 200 if result["status"] == "success" else 404
    return jsonify(result), status_code


@trades_bp.route("/api/trades/<trade_id>", methods=["PUT"])
@require_api_key
def api_exit(trade_id):
    """更新出场记录（平仓）"""
    data = request.get_json(silent=True) or {}

    # 获取入场记录
    trade = _journal.get_trade(trade_id)
    if trade["status"] != "success" or not trade["records"]:
        return jsonify({"error": "trade not found"}), 404

    entry_record = next((r for r in trade["records"] if r["action"] == "entry"), None)
    if not entry_record:
        return jsonify({"error": "entry record not found"}), 404

    # 计算持仓天数
    if not data.get("holding_days"):
        try:
            from datetime import date as date_cls
            buy_d = date_cls.fromisoformat(entry_record["date"])
            sell_d = date_cls.fromisoformat(data.get("sell_date", ""))
            data["holding_days"] = (sell_d - buy_d).days
        except Exception:
            data["holding_days"] = 0

    # 计算盈亏百分比
    if not data.get("pnl_percent") and entry_record.get("price"):
        try:
            buy_p = float(entry_record["price"])
            sell_p = float(data.get("sell_price", 0))
            data["pnl_percent"] = round((sell_p - buy_p) / buy_p * 100, 2)
        except Exception:
            pass

    result = _journal.record_exit({"trade_id": trade_id, **data})
    status_code = 200 if result["status"] == "success" else 400
    return jsonify(result), status_code


@trades_bp.route("/api/trades/summary", methods=["GET"])
@require_api_key
def api_summary():
    """交易汇总统计"""
    return jsonify(_journal.get_summary())
