"""
交易编排器测试
"""

import pytest
from src.data.orchestrator import TradingOrchestrator


class TestTradingOrchestrator:
    """交易编排测试"""

    def test_orchestrator_init(self):
        """编排器初始化"""
        orch = TradingOrchestrator()
        assert orch.market_analyzer is not None
        assert orch.sector_analyzer is not None
        assert orch.stock_screener is not None
        assert orch.position_tracker is not None

    def test_run_returns_dict(self):
        """run 返回结构"""
        orch = TradingOrchestrator()
        result = orch.run({"mode": "daily_scan"})

        assert "market_env" in result
        assert "strong_sectors" in result
        assert "candidates" in result
        assert "positions_status" in result
        assert "alerts" in result
