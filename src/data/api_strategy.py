"""
策略评估 API
路由: GET /api/strategy/review
"""
import os
from flask import Blueprint, request, jsonify
from functools import wraps
from evolution.strategy_reviewer import StrategyReviewer
from evolution.trade_journal import TradeJournal

_api_key = os.environ.get("FLASK_API_KEY", "")


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if _api_key:
            if request.headers.get("X-API-Key", "") != _api_key:
                return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


strategy_bp = Blueprint("strategy", __name__)
_journal = TradeJournal()
_reviewer = StrategyReviewer()


@strategy_bp.route("/api/strategy/review", methods=["GET"])
@require_api_key
def api_review():
    """策略评估"""
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    pattern = request.args.get("pattern")
    sector = request.args.get("sector")

    # 从 trade_journal 查已平仓记录（exited）
    result = _journal.query_trades(
        status="exited",
        start_date=start_date,
        end_date=end_date,
        sector=sector,
        pattern=pattern,
        page=1,
        page_size=1000,  # 评估时取全部
    )

    # 适配 StrategyReviewer 需要的字段
    trades = result.get("trades", [])
    for t in trades:
        t["outcome"] = "win" if t.get("pnl_percent", 0) > 0 else "loss"

    review = _reviewer.analyze(trades, start_date, end_date)
    return jsonify(review)


@strategy_bp.route("/api/strategy/summary", methods=["GET"])
@require_api_key
def api_summary():
    """策略汇总（与 /api/trades/summary 相同数据源）"""
    return jsonify(_journal.get_summary())


@strategy_bp.route("/api/strategy/patterns", methods=["GET"])
@require_api_key
def api_patterns():
    """各形态统计"""
    result = _journal.query_trades(status="exited", page=1, page_size=1000)
    trades = result.get("trades", [])
    from collections import defaultdict
    groups = defaultdict(list)
    for t in trades:
        groups[t.get("pattern", "unknown")].append(t)

    patterns = {}
    for p, group in groups.items():
        total = len(group)
        wins = sum(1 for t in group if t.get("pnl_percent", 0) > 0)
        pnls = [t.get("pnl_percent", 0) for t in group]
        patterns[p] = {
            "total": total,
            "wins": wins,
            "losses": total - wins,
            "win_rate": round(wins / total, 2) if total > 0 else 0,
            "avg_pnl": round(sum(pnls) / total, 2) if total > 0 else 0,
        }
    return jsonify({"patterns": patterns})


@strategy_bp.route("/api/strategy/sectors", methods=["GET"])
@require_api_key
def api_sectors():
    """各板块统计"""
    result = _journal.query_trades(status=None, page=1, page_size=1000)
    trades = result.get("trades", [])
    from collections import defaultdict
    groups = defaultdict(list)
    for t in trades:
        groups[t.get("sector", "unknown")].append(t)

    sectors = {}
    for s, group in groups.items():
        total = len(group)
        wins = sum(1 for t in group if t.get("pnl_percent", 0) > 0)
        pnls = [t.get("pnl_percent", 0) for t in group]
        sectors[s] = {
            "total": total,
            "wins": wins,
            "losses": total - wins,
            "win_rate": round(wins / total, 2) if total > 0 else 0,
            "avg_pnl": round(sum(pnls) / total, 2) if total > 0 else 0,
        }
    return jsonify({"sectors": sectors})
