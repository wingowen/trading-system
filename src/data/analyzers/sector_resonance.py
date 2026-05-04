"""
板块共振分析器
根据 spec 02-layer2-analyzers.md 的规则：
- 当日涨幅 ≥ 1.5%
- 5日涨幅 ≥ 5%
- 上涨占比 ≥ 70%
- 成交额排名前20
- 连板龙头 ≥ 2板
"""

from typing import Any, Dict


class SectorResonanceAnalyzer:
    """分析板块共振强度，识别强势板块"""

    THRESHOLD_DAILY_GAIN = 1.5
    THRESHOLD_GAIN_5D = 5.0
    THRESHOLD_UP_RATIO = 0.70
    THRESHOLD_BOARD = 2

    def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """分析板块共振

        Args:
            data: 包含 sectors 列表

        Returns:
            dict: {
                "strong_sectors": [...]
            }
        """
        try:
            sectors = data.get("sectors", [])
            strong = []

            for sector in sectors:
                checks = self._run_checks(sector)
                if all(checks.values()):
                    strong.append(self._build_sector(sector, checks))

            return {"strong_sectors": strong}
        except Exception as e:
            return {"strong_sectors": [], "error": str(e)}

    def _run_checks(self, sector: Dict[str, Any]) -> Dict[str, bool]:
        """执行各项检查"""
        checks = {}

        checks["daily_gain_ok"] = (
            sector.get("daily_gain", 0) >= self.THRESHOLD_DAILY_GAIN
        )
        checks["gain_5d_ok"] = sector.get("gain_5d", 0) >= self.THRESHOLD_GAIN_5D
        checks["up_ratio_ok"] = sector.get("up_ratio", 0) >= self.THRESHOLD_UP_RATIO
        checks["volume_top20"] = sector.get("volume_top20_rank", 999) <= 20
        checks["has_leader"] = sector.get("highest_board", 0) >= self.THRESHOLD_BOARD

        return checks

    def _build_sector(
        self, sector: Dict[str, Any], checks: Dict[str, bool]
    ) -> Dict[str, Any]:
        """构建强势板块输出"""
        score = sum(20 for v in checks.values() if v)

        return {
            "name": sector.get("name", ""),
            "score": score,
            "checks": checks,
            "metrics": {
                "daily_gain": sector.get("daily_gain", 0),
                "gain_5d": sector.get("gain_5d", 0),
                "up_ratio": sector.get("up_ratio", 0),
                "limit_up_count": sector.get("limit_up_count", 0),
                "highest_board": sector.get("highest_board", 0),
            },
        }
