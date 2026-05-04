"""
持仓跟踪器测试
"""

import pytest
from src.data.analyzers.position_tracker import PositionTracker


class TestPositionTracker:
    """持仓跟踪测试"""

    def test_hold_when_no_trigger(self):
        """无触发条件时继续持有"""
        tracker = PositionTracker()
        input_data = {
            "positions": [
                {
                    "code": "688981",
                    "name": "中芯国际",
                    "sector": "半导体",
                    "buy_price": 45.20,
                    "buy_date": "2026-05-03",
                    "position_size": 0.2,
                    "stop_loss": 42.94,
                    "take_profit": 48.82,
                }
            ],
            "current_prices": {"688981": 46.50},
            "sector_status": {"半导体": {"daily_gain": 1.2, "limit_up_count": 2}},
            "market_env": {"tradable": True, "score": 80},
        }
        result = tracker.track(input_data)
        assert result["positions_status"][0]["action"] == "hold"

    def test_stop_loss_triggered(self):
        """触发止损"""
        tracker = PositionTracker()
        input_data = {
            "positions": [
                {
                    "code": "688981",
                    "name": "中芯国际",
                    "sector": "半导体",
                    "buy_price": 45.20,
                    "buy_date": "2026-05-03",
                    "position_size": 0.2,
                    "stop_loss": 42.94,
                    "take_profit": 48.82,
                }
            ],
            "current_prices": {"688981": 42.00},
            "sector_status": {"半导体": {"daily_gain": 1.2, "limit_up_count": 2}},
            "market_env": {"tradable": True, "score": 80},
        }
        result = tracker.track(input_data)
        assert result["positions_status"][0]["action"] == "sell"
