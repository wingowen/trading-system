"""
交易编排器 - 串联整个交易流程
"""
from datetime import date
from typing import Any, Dict, List, Optional

from src.data.analyzers import (
    MarketEnvironmentAnalyzer,
    SectorResonanceAnalyzer,
    StockRightPatternScreener,
    PositionTracker,
)
from src.data.db_reader import get_field, get_records


class TradingOrchestrator:
    """交易编排器"""

    MAX_CANDIDATES = 5

    def __init__(self):
        self.market_analyzer = MarketEnvironmentAnalyzer()
        self.sector_analyzer = SectorResonanceAnalyzer()
        self.stock_screener = StockRightPatternScreener()
        self.position_tracker = PositionTracker()

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行完整交易流程"""
        mode = input_data.get("mode", "daily_scan")
        target_date = input_data.get("date") or date.today().isoformat()
        session = input_data.get("session", "morning")

        result = {
            "mode": mode,
            "market_env": {"tradable": False, "score": 0, "reasons": []},
            "strong_sectors": [],
            "candidates": [],
            "positions_status": [],
            "alerts": [],
        }

        # Step 1: 大盘环境（从 db_reader 取今日数据）
        market_data = self._fetch_market_data(target_date, session)
        market_result = self.market_analyzer.analyze(market_data)
        result["market_env"] = {
            "tradable": market_result.get("tradable", False),
            "score": market_result.get("score", 0),
            "reasons": self._extract_reasons(market_result),
        }

        if not market_result.get("tradable", False):
            result["_debug"] = {"market_data": market_data}
            return result

        # Step 2: 板块共振（暂时还是 stub，直到有真实板块数据源）
        sector_data = {"sectors": input_data.get("sectors", [])}
        sector_result = self.sector_analyzer.analyze(sector_data)
        strong_sectors = sector_result.get("strong_sectors", [])
        result["strong_sectors"] = [
            {"name": s["name"], "score": s["score"], "metrics": s.get("metrics", {})}
            for s in strong_sectors
        ]

        if not strong_sectors:
            return result

        # Step 3: 个股筛选
        for sector in strong_sectors[:3]:
            stock_data = {
                "sector": sector["name"],
                "stocks": input_data.get("stocks", []),  # TODO: 需真实个股数据源
            }
            stock_result = self.stock_screener.analyze(stock_data)
            candidates = stock_result.get("candidates", [])
            for c in candidates[: self.MAX_CANDIDATES]:
                c["sector"] = sector["name"]
                result["candidates"].append(c)

        # Step 4: 持仓跟踪（从 input_data 注入持仓）
        position_data = input_data.get("position_data", {
            "positions": [],
            "current_prices": {},
            "sector_status": {},
            "market_env": market_result,
        })
        position_result = self.position_tracker.track(position_data)
        result["positions_status"] = position_result.get("positions_status", [])
        result["alerts"] = position_result.get("alerts", [])

        return result

    def _fetch_market_data(self, trade_date: str, session: str) -> Dict[str, Any]:
        """
        从 db_reader 读取今日字段，组装成 market_analyzer 需要的格式。
        如果字段不存在，返回空（analyzer 会走 defaults）。
        """
        index_data = {}
        # 上证数据
        sh_close = get_field(trade_date, "index_chg_sh000001", session)
        if sh_close is not None:
            index_data["shanghai"] = {
                "close": sh_close,  # 注意：db 里存的是涨跌幅，不是价格
                "ma5": sh_close,    # TODO: 需要真实 MA5，需历史数据
            }

        # 涨跌停家数
        limit_up = get_field(trade_date, "zt_pool_count", session)
        limit_down = get_field(trade_date, "dt_pool_count", session)

        # 成交额（db 里暂无此字段，用 0 填充）
        total_vol = 0

        return {
            "index_data": index_data,
            "market_sentiment": {
                "limit_up_count": limit_up if limit_up is not None else 0,
                "limit_down_count": limit_down if limit_down is not None else 0,
            },
            "total_volume": total_vol,
            "volume_5d_avg": total_vol,  # TODO: 需历史均量
        }

    def _extract_reasons(self, result: Dict) -> List[str]:
        """提取通过的原因"""
        reasons = []
        checks = result.get("checks", {})
        if checks.get("above_ma5"):
            reasons.append("上证站上5日线")
        if checks.get("limit_up_ok"):
            reasons.append("涨停家数≥12")
        if checks.get("volume_ok"):
            reasons.append("成交量正常")
        return reasons
