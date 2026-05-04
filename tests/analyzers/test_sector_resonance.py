"""
板块共振分析器测试
"""

import pytest
from src.data.analyzers.sector_resonance import SectorResonanceAnalyzer


class TestSectorResonanceAnalyzer:
    """板块共振分析测试"""

    def test_strong_sector_passes_all_checks(self):
        """强势板块通过全部检查"""
        analyzer = SectorResonanceAnalyzer()
        input_data = {
            "sectors": [
                {
                    "name": "半导体",
                    "daily_gain": 2.5,
                    "gain_5d": 6.8,
                    "up_ratio": 0.78,
                    "limit_up_count": 3,
                    "highest_board": 4,
                    "volume_market_ratio": 0.08,
                    "volume_top20_rank": 5,
                }
            ]
        }
        result = analyzer.analyze(input_data)
        assert len(result["strong_sectors"]) == 1
        assert result["strong_sectors"][0]["checks"]["daily_gain_ok"] is True

    def test_weak_sector_filtered_out(self):
        """弱势板块被过滤"""
        analyzer = SectorResonanceAnalyzer()
        input_data = {
            "sectors": [
                {
                    "name": "银行",
                    "daily_gain": 0.5,
                    "gain_5d": 2.0,
                    "up_ratio": 0.40,
                    "limit_up_count": 0,
                    "highest_board": 0,
                    "volume_market_ratio": 0.15,
                    "volume_top20_rank": 1,
                }
            ]
        }
        result = analyzer.analyze(input_data)
        assert len(result["strong_sectors"]) == 0
