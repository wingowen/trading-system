"""
大盘环境分析器测试
"""

import pytest
from src.data.analyzers.market_environment import MarketEnvironmentAnalyzer


class TestMarketEnvironmentAnalyzer:
    """大盘环境判断测试"""

    def test_above_ma5_positive(self):
        """上证站上5日线 - 通过"""
        analyzer = MarketEnvironmentAnalyzer()
        input_data = {
            "index_data": {"shanghai": {"close": 3250.50, "ma5": 3230.20}},
            "market_sentiment": {
                "limit_up_count": 28,
                "limit_down_count": 3,
            },
            "volume_5d_avg": 82000000000,
            "total_volume": 85000000000,
        }
        result = analyzer.analyze(input_data)
        assert result["tradable"] is True
        assert result["checks"]["above_ma5"] is True

    def test_above_ma5_negative(self):
        """上证未站上5日线 - 失败"""
        analyzer = MarketEnvironmentAnalyzer()
        input_data = {
            "index_data": {"shanghai": {"close": 3250.50, "ma5": 3260.00}},
            "market_sentiment": {
                "limit_up_count": 28,
                "limit_down_count": 3,
            },
            "volume_5d_avg": 82000000000,
            "total_volume": 85000000000,
        }
        result = analyzer.analyze(input_data)
        assert result["tradable"] is False
        assert result["checks"]["above_ma5"] is False

    def test_limit_down_exceeds_threshold(self):
        """跌停家数超过5家 - 失败"""
        analyzer = MarketEnvironmentAnalyzer()
        input_data = {
            "index_data": {"shanghai": {"close": 3250.50, "ma5": 3230.20}},
            "market_sentiment": {
                "limit_up_count": 28,
                "limit_down_count": 10,
            },
            "volume_5d_avg": 82000000000,
            "total_volume": 85000000000,
        }
        result = analyzer.analyze(input_data)
        assert result["tradable"] is False
        assert result["checks"]["limit_down_ok"] is False

    def test_volume_insufficient(self):
        """成交额不足5日均量80% - 失败"""
        analyzer = MarketEnvironmentAnalyzer()
        input_data = {
            "index_data": {"shanghai": {"close": 3250.50, "ma5": 3230.20}},
            "market_sentiment": {
                "limit_up_count": 28,
                "limit_down_count": 3,
            },
            "volume_5d_avg": 100000000000,
            "total_volume": 70000000000,
        }
        result = analyzer.analyze(input_data)
        assert result["tradable"] is False
        assert result["checks"]["volume_ok"] is False

    def test_limit_up_insufficient(self):
        """涨停家数不足12家 - 失败"""
        analyzer = MarketEnvironmentAnalyzer()
        input_data = {
            "index_data": {"shanghai": {"close": 3250.50, "ma5": 3230.20}},
            "market_sentiment": {
                "limit_up_count": 8,
                "limit_down_count": 3,
            },
            "volume_5d_avg": 82000000000,
            "total_volume": 85000000000,
        }
        result = analyzer.analyze(input_data)
        assert result["tradable"] is False
        assert result["checks"]["limit_up_ok"] is False

    def test_all_checks_pass(self):
        """全部检查通过"""
        analyzer = MarketEnvironmentAnalyzer()
        input_data = {
            "index_data": {"shanghai": {"close": 3250.50, "ma5": 3230.20}},
            "market_sentiment": {
                "limit_up_count": 28,
                "limit_down_count": 3,
            },
            "volume_5d_avg": 82000000000,
            "total_volume": 85000000000,
        }
        result = analyzer.analyze(input_data)
        assert result["tradable"] is True
        assert all(result["checks"].values())
        assert result["score"] == 100

    def test_missing_data(self):
        """数据缺失时返回 tradable=False"""
        analyzer = MarketEnvironmentAnalyzer()
        input_data = {}  # 缺少必要数据
        result = analyzer.analyze(input_data)
        assert result["tradable"] is False
