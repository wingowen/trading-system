"""
交易编排器 - 串联整个交易流程
"""

from typing import Any, Dict, List


class TradingOrchestrator:
    """交易编排器"""

    MAX_CANDIDATES = 5

    def __init__(self):
        from src.data.analyzers import (
            MarketEnvironmentAnalyzer,
            SectorResonanceAnalyzer,
            StockRightPatternScreener,
            PositionTracker,
        )

        self.market_analyzer = MarketEnvironmentAnalyzer()
        self.sector_analyzer = SectorResonanceAnalyzer()
        self.stock_screener = StockRightPatternScreener()
        self.position_tracker = PositionTracker()

    def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行完整交易流程"""
        mode = input_data.get("mode", "daily_scan")
        target_sector = input_data.get("target_sector")

        result = {
            "mode": mode,
            "market_env": {"tradable": False, "score": 0, "reasons": []},
            "strong_sectors": [],
            "candidates": [],
            "positions_status": [],
            "alerts": [],
        }

        # Step 1: 大盘环境
        market_data = {}
        market_result = self.market_analyzer.analyze(market_data)
        result["market_env"] = {
            "tradable": market_result.get("tradable", False),
            "score": market_result.get("score", 0),
            "reasons": self._extract_reasons(market_result),
        }

        if not market_result.get("tradable", False):
            return result

        # Step 2: 板块共振
        sector_data = {"sectors": []}
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
            stock_data = {"sector": sector["name"], "stocks": []}
            stock_result = self.stock_screener.analyze(stock_data)
            candidates = stock_result.get("candidates", [])
            for c in candidates[: self.MAX_CANDIDATES]:
                c["sector"] = sector["name"]
                result["candidates"].append(c)

        # Step 4: 持仓跟踪
        position_data = {
            "positions": [],
            "current_prices": {},
            "sector_status": {},
            "market_env": {},
        }
        position_result = self.position_tracker.track(position_data)
        result["positions_status"] = position_result.get("positions_status", [])
        result["alerts"] = position_result.get("alerts", [])

        return result

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
