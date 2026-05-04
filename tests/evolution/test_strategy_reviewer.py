"""
策略评估测试
"""

import pytest
from src.data.evolution.strategy_reviewer import StrategyReviewer


class TestStrategyReviewer:
    """策略评估测试"""

    def test_analyze_with_trades(self):
        """分析交易记录"""
        reviewer = StrategyReviewer()
        trades = [
            {
                "pattern": "突破右侧",
                "sector": "半导体",
                "outcome": "win",
                "pnl_percent": 8.5,
                "market_env_score": 85,
            },
            {
                "pattern": "突破右侧",
                "sector": "半导体",
                "outcome": "win",
                "pnl_percent": 5.2,
                "market_env_score": 85,
            },
            {
                "pattern": "回踩右侧",
                "sector": "新能源",
                "outcome": "loss",
                "pnl_percent": -3.1,
                "market_env_score": 55,
            },
        ]

        result = reviewer.analyze(trades)

        assert result["summary"]["total_trades"] == 3
        assert result["summary"]["win_rate"] == pytest.approx(0.67, rel=0.01)
        assert "pattern_analysis" in result
        assert "sector_analysis" in result

    def test_analyze_empty(self):
        """空交易列表"""
        reviewer = StrategyReviewer()
        result = reviewer.analyze([])

        assert result["summary"]["total_trades"] == 0
        assert result["conclusion"] == "无交易数据"
