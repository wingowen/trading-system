"""
交易日志测试
"""

import pytest
from src.data.evolution.trade_journal import TradeJournal


class TestTradeJournal:
    """交易日志测试"""

    def test_record_entry(self):
        """记录入场"""
        journal = TradeJournal()
        data = {
            "trade_id": "T20260503-001",
            "code": "688981",
            "name": "中芯国际",
            "buy_price": 45.20,
            "buy_date": "2026-05-03",
            "pattern": "突破右侧",
            "sector": "半导体",
            "market_env_score": 85,
            "sector_score": 92,
            "stop_loss": 42.94,
            "take_profit": 48.82,
            "position_size": 0.2,
        }
        result = journal.record_entry(data)

        assert result["status"] == "success"
        assert result["trade_id"] == "T20260503-001"

    def test_record_exit(self):
        """记录出场"""
        journal = TradeJournal()
        data = {
            "trade_id": "T20260503-001",
            "sell_price": 48.50,
            "sell_date": "2026-05-08",
            "reason": "止盈",
            "pnl_percent": 7.30,
            "holding_days": 5,
        }
        result = journal.record_exit(data)

        assert result["status"] == "success"

    def test_get_trade(self):
        """获取交易记录"""
        journal = TradeJournal()
        result = journal.get_trade("T20260503-001")

        assert result["status"] == "success"
