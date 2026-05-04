"""
编排器 API
路由: GET /api/orchestrator/run — 运行编排器（精准采集）
      GET /api/orchestrator/sectors — 采集强势板块
      GET /api/orchestrator/sector-stocks — 采集板块成分股
"""
import os, traceback
from flask import Blueprint, request, jsonify
from functools import wraps
from src.data.fetchers.akshare_fetcher import (
    fetch_strong_sectors,
    fetch_sector_stocks,
    enrich_stock_metrics,
)
from src.data.analyzers import StockRightPatternScreener

_api_key = os.environ.get("FLASK_API_KEY", "")


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if _api_key:
            if request.headers.get("X-API-Key", "") != _api_key:
                return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


orchestrator_bp = Blueprint("orchestrator", __name__)


@orchestrator_bp.route("/api/orchestrator/sectors", methods=["GET"])
@require_api_key
def api_sectors():
    """采集强势板块（近5日累计涨幅 Top5）"""
    top_n = int(request.args.get("top_n", 5))
    result = fetch_strong_sectors(top_n=top_n)
    return jsonify(result)


@orchestrator_bp.route("/api/orchestrator/sector-stocks", methods=["GET"])
@require_api_key
def api_sector_stocks():
    """采集某板块成分股 Top10（按涨幅排序）"""
    sector = request.args.get("sector", "")
    top_n = int(request.args.get("top_n", 10))
    if not sector:
        return jsonify({"error": "sector parameter required"}), 400
    result = fetch_sector_stocks(sector, top_n=top_n)
    return jsonify(result)


@orchestrator_bp.route("/api/orchestrator/run", methods=["GET"])
@require_api_key
def api_run():
    """
    运行完整编排链路（精准采集）：
    1. fetch_strong_sectors() → Top5 强势板块
    2. fetch_sector_stocks() → 每板块 Top10 成分股
    3. enrich_stock_metrics() → 单股补充 MA/量比
    4. StockRightPatternScreener → 形态筛选
    """
    try:
        # Step 1: 强势板块
        sectors_result = fetch_strong_sectors(top_n=5)
        if sectors_result.get("status") != "success":
            return jsonify({"status": "failed", "step": "sectors", "error": sectors_result.get("error")}), 500

        strong_sectors = sectors_result.get("strong_sectors", [])
        if not strong_sectors:
            return jsonify({"status": "success", "candidates": [], "message": "no strong sectors found"})

        candidates = []
        screener = StockRightPatternScreener()

        # Step 2+3+4: 每板块采集成分股并补充指标
        for sector_info in strong_sectors:
            sector_name = sector_info["name"]
            stocks_result = fetch_sector_stocks(sector_name, top_n=10)
            if stocks_result.get("status") != "success":
                continue

            stocks = stocks_result.get("stocks", [])
            enriched_stocks = []

            for stock in stocks:
                code = stock.get("code", "")
                metrics = enrich_stock_metrics(code)
                stock.update(metrics)
                enriched_stocks.append(stock)

            # Step 4: 形态筛选
            screen_result = screener.analyze({
                "sector": sector_name,
                "stocks": enriched_stocks,
            })
            screen_candidates = screen_result.get("candidates", [])

            for c in screen_candidates:
                c["sector"] = sector_name
                candidates.append(c)

        return jsonify({
            "status": "success",
            "strong_sectors": strong_sectors,
            "candidates": candidates,
            "total_candidates": len(candidates),
        })
    except Exception as e:
        return jsonify({"status": "failed", "error": str(e), "trace": traceback.format_exc()}), 500
