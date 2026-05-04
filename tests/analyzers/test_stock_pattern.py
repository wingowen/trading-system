"""
个股右侧形态筛选器测试
"""

import pytest
from src.data.analyzers.stock_pattern import StockRightPatternScreener


class TestStockRightPatternScreener:
    """个股筛选测试"""

    def test突破右侧形态通过(self):
        """突破右侧形态通过筛选"""
        screener = StockRightPatternScreener()
        input_data = {
            "sector": "半导体",
            "stocks": [
                {
                    "code": "688981",
                    "name": "中芯国际",
                    "close": 45.20,
                    "ma5": 44.80,
                    "ma10": 44.20,
                    "ma20": 43.50,
                    "volume_ratio": 1.5,
                    "float_mv": 180000000000,
                    "is_st": False,
                    "is_new": False,
                    "list_date": "2020-07-16",
                }
            ],
        }
        result = screener.analyze(input_data)
        assert len(result["candidates"]) == 1
        assert result["candidates"][0]["pattern"] == "突破右侧"

    def test_stocks被过滤(self):
        """ST股被过滤"""
        screener = StockRightPatternScreener()
        input_data = {
            "sector": "半导体",
            "stocks": [
                {
                    "code": "688981",
                    "name": "中芯国际",
                    "close": 45.20,
                    "ma5": 44.80,
                    "ma10": 44.20,
                    "ma20": 43.50,
                    "volume_ratio": 1.5,
                    "float_mv": 180000000000,
                    "is_st": True,
                    "is_new": False,
                    "list_date": "2020-07-16",
                }
            ],
        }
        result = screener.analyze(input_data)
        assert len(result["candidates"]) == 0
