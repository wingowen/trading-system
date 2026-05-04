"""
个股右侧形态筛选器
根据 spec 02-layer2-analyzers.md 的规则：
- 垃圾过滤：ST股市值<30亿、次新股<6月
- 突破右侧：放量突破20日线、均线多头排列、量比≥1.2
- 回踩右侧：回踩5/10日线企稳、回踩缩量、未破20日线
"""

from datetime import datetime
from typing import Any, Dict


class StockRightPatternScreener:
    """筛选右侧形态个股"""

    MIN_FLOAT_MV = 30000000000  # 30亿
    MIN_VOLUME_RATIO = 1.2
    NEW_STOCK_MONTHS = 6

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """筛选个股

        Args:
            data: 包含 sector, stocks 列表

        Returns:
            dict: {
                "candidates": [...]
            }
        """
        try:
            sector = data.get("sector", "")
            stocks = data.get("stocks", [])
            candidates = []

            for stock in stocks:
                if not self._pass_filters(stock):
                    continue

                pattern = self._detect_pattern(stock)
                if pattern:
                    candidates.append(self._build_candidate(stock, pattern))

            return {"candidates": candidates}
        except Exception as e:
            return {"candidates": [], "error": str(e)}

    def _pass_filters(self, stock: Dict[str, Any]) -> bool:
        """垃圾过滤"""
        if stock.get("is_st", False):
            return False
        if stock.get("float_mv", 0) < self.MIN_FLOAT_MV:
            return False
        if self._is_new_stock(stock):
            return False
        return True

    def _is_new_stock(self, stock: Dict[str, Any]) -> bool:
        """是否次新股（上市<6月）"""
        list_date = stock.get("list_date")
        if not list_date:
            return False
        try:
            listed = datetime.strptime(list_date, "%Y-%m-%d").date()
            months = (datetime.now().date() - listed).days / 30
            return months < self.NEW_STOCK_MONTHS
        except:
            return False

    def _detect_pattern(self, stock: Dict[str, Any]) -> str:
        """检测右侧形态"""
        if self._is_breakout(stock):
            return "突破右侧"
        if self._is_pullback(stock):
            return "回踩右侧"
        return ""

    def _is_breakout(self, stock: Dict[str, Any]) -> bool:
        """放量突破右侧"""
        close = stock.get("close", 0)
        ma20 = stock.get("ma20", 0)
        ma5 = stock.get("ma5", 0)
        ma10 = stock.get("ma10", 0)

        if close <= ma20:
            return False
        if not (ma5 > ma10 > ma20):
            return False
        if stock.get("volume_ratio", 0) < self.MIN_VOLUME_RATIO:
            return False
        return True

    def _is_pullback(self, stock: Dict[str, Any]) -> bool:
        """回踩右侧"""
        close = stock.get("close", 0)
        ma5 = stock.get("ma5", 0)
        ma10 = stock.get("ma10", 0)
        ma20 = stock.get("ma20", 0)
        volume_ratio = stock.get("volume_ratio", 0)

        if close < ma10:
            return False
        if volume_ratio >= 1.0:
            return False
        if close < ma20:
            return False
        return True

    def _build_candidate(self, stock: Dict[str, Any], pattern: str) -> Dict[str, Any]:
        """构建候选标的"""
        close = stock.get("close", 0)
        stop_loss = close * 0.95
        take_profit = close * 1.10

        return {
            "code": stock.get("code", ""),
            "name": stock.get("name", ""),
            "pattern": pattern,
            "score": 85,
            "current_price": close,
            "suggested_entry": close,
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "position_size": 0.2,
        }
