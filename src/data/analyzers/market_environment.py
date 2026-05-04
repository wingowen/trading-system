"""
大盘环境分析器 - 市场可行性判断
根据 spec 02-layer2-analyzers.md 的规则：
- 上证站上5日线 (close > ma5)
- 跌停家数 ≤ 5
- 成交额 ≥ 5日均量 80%
- 涨停家数 ≥ 12
"""

from typing import Any, Dict


class MarketEnvironmentAnalyzer:
    """判断大盘环境是否适合交易"""

    # 阈值配置
    THRESHOLD_LIMIT_DOWN = 5
    THRESHOLD_LIMIT_UP = 12
    THRESHOLD_VOLUME_RATIO = 0.8  # 5日均量的80%

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析大盘环境

        Args:
            data: 包含 index_data, market_sentiment, volume_5d_avg, total_volume

        Returns:
            dict: {
                "tradable": bool,
                "score": int (0-100),
                "checks": dict,
                "details": dict
            }
        """
        try:
            checks = self._run_checks(data)
            tradable = all(checks.values())
            score = self._calculate_score(checks)

            return {
                "tradable": tradable,
                "score": score,
                "checks": checks,
                "details": self._extract_details(data),
            }
        except Exception as e:
            return {
                "tradable": False,
                "score": 0,
                "checks": {},
                "details": {},
                "error": str(e),
            }

    def _run_checks(self, data: Dict[str, Any]) -> Dict[str, bool]:
        """执行各项检查"""
        checks = {}

        # 1. 上证站上5日线
        index_data = data.get("index_data", {})
        shanghai = index_data.get("shanghai", {})
        close = shanghai.get("close", 0)
        ma5 = shanghai.get("ma5", 0)
        checks["above_ma5"] = close > ma5 if close and ma5 else False

        # 2. 跌停家数 ≤ 5
        market_sentiment = data.get("market_sentiment", {})
        limit_down = market_sentiment.get("limit_down_count", 999)
        checks["limit_down_ok"] = limit_down <= self.THRESHOLD_LIMIT_DOWN

        # 3. 成交额 ≥ 5日均量80%
        volume_5d = data.get("volume_5d_avg", 0)
        total_vol = data.get("total_volume", 0)
        if volume_5d and total_vol:
            volume_ratio = total_vol / volume_5d
        else:
            volume_ratio = 0
        checks["volume_ok"] = volume_ratio >= self.THRESHOLD_VOLUME_RATIO

        # 4. 涨停家数 ≥ 12
        limit_up = market_sentiment.get("limit_up_count", 0)
        checks["limit_up_ok"] = limit_up >= self.THRESHOLD_LIMIT_UP

        return checks

    def _calculate_score(self, checks: Dict[str, bool]) -> int:
        """计算大盘环境评分 (0-100)"""
        if not any(checks.values()):
            return 0

        # 每项通过得25分，满分100
        score = sum(25 for v in checks.values() if v)

        # 全部通过时额外加分到85-100范围
        if all(checks.values()):
            score = min(100, score + 15)

        return score

    def _extract_details(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取详细信息"""
        market_sentiment = data.get("market_sentiment", {})

        volume_5d = data.get("volume_5d_avg", 0) or 1
        total_vol = data.get("total_volume", 0) or 0

        return {
            "limit_up_count": market_sentiment.get("limit_up_count", 0),
            "limit_down_count": market_sentiment.get("limit_down_count", 0),
            "volume_ratio": round(total_vol / volume_5d, 2) if volume_5d else 0,
        }
