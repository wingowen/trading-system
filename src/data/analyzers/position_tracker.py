"""
持仓跟踪器
根据 spec 02-layer2-analyzers.md 的规则：
- 止损：跌破止损价、回撤5%
- 止盈：盈利8%/12%/15%分批止盈
- 板块止损：板块转弱
- 大盘止损：大盘环境恶化
"""

from typing import Any, Dict


class PositionTracker:
    """持仓跟踪与止损止盈"""

    STOP_LOSS_PCT = 0.05  # 5%止损

    def track(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """跟踪持仓

        Args:
            data: 包含 positions, current_prices, sector_status, market_env

        Returns:
            dict: {
                "positions_status": [...],
                "alerts": [...]
            }
        """
        try:
            positions = data.get("positions", [])
            current_prices = data.get("current_prices", {})
            sector_status = data.get("sector_status", {})
            market_env = data.get("market_env", {})

            statuses = []
            alerts = []

            for pos in positions:
                code = pos.get("code")
                current_price = current_prices.get(code, pos.get("buy_price"))
                buy_price = pos.get("buy_price", 1)
                pnl_pct = (current_price - buy_price) / buy_price

                action, reason = self._check_action(
                    pos,
                    current_price,
                    pnl_pct,
                    sector_status.get(pos.get("sector", "")),
                    market_env,
                )

                statuses.append(
                    {
                        "code": code,
                        "name": pos.get("name", ""),
                        "current_price": current_price,
                        "pnl_percent": round(pnl_pct * 100, 2),
                        "action": action,
                        "reason": reason,
                    }
                )

                if action != "hold":
                    alerts.append(
                        {
                            "code": code,
                            "action": action,
                            "reason": reason,
                        }
                    )

            return {"positions_status": statuses, "alerts": alerts}
        except Exception as e:
            return {"positions_status": [], "alerts": [], "error": str(e)}

    def _check_action(
        self,
        pos: Dict[str, Any],
        current_price: float,
        pnl_pct: float,
        sector: Dict,
        market_env: Dict,
    ) -> tuple:
        """检查触发条件"""
        buy_price = pos.get("buy_price", 0)
        stop_loss = pos.get("stop_loss", buy_price * (1 - self.STOP_LOSS_PCT))
        take_profit = pos.get("take_profit", buy_price * 1.10)

        # 止损
        if current_price <= stop_loss:
            return "sell", "触发止损"

        # 止盈
        if current_price >= take_profit:
            return "sell", "触发止盈"

        # 板块转弱（简化：涨停<1家）
        if sector and sector.get("limit_up_count", 999) < 1:
            return "sell", "板块转弱"

        # 大盘恶化
        if market_env and not market_env.get("tradable", True):
            return "sell", "大盘环境恶化"

        return "hold", "继续持有"
