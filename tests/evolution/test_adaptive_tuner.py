"""
自适应调整测试
"""

import pytest
from src.data.evolution.adaptive_tuner import AdaptiveStrategyTuner


class TestAdaptiveStrategyTuner:
    """自适应调整测试"""

    def test_tune_with_suggestions(self):
        """生成调整建议"""
        tuner = AdaptiveStrategyTuner()
        review = {
            "summary": {"total_trades": 25, "win_rate": 0.72},
            "pattern_analysis": {
                "突破右侧": {"win_rate": 0.75, "trades": 15},
                "回踩右侧": {"win_rate": 0.35, "trades": 10},
            },
            "sector_analysis": {
                "半导体": {"win_rate": 0.80, "trades": 8},
                "新能源": {"win_rate": 0.30, "trades": 5},
            },
        }

        result = tuner.tune(review)

        assert "suggested_params" in result
        assert "changes" in result
        assert len(result["changes"]) >= 2

    def test_confidence_calculation(self):
        """置信度计算"""
        tuner = AdaptiveStrategyTuner()
        review = {
            "summary": {"total_trades": 30, "win_rate": 0.75},
            "pattern_analysis": {},
            "sector_analysis": {},
        }

        result = tuner.tune(review)

        assert result["confidence"] >= 0.7
        assert result["auto_apply"] is True
