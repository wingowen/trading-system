"""
策略参数自适应调整器
根据 spec 04-layer4-evolution.md：
- 根据评估结果生成参数调整建议
- 计算置信度
- 需用户审核或自动应用
"""

from typing import Any, Dict, List


class AdaptiveStrategyTuner:
    """策略参数自适应调整器"""

    # 默认阈值
    DEFAULT_PARAMS = {
        "sector": {
            "min_daily_gain": 1.5,
            "min_5d_gain": 5.0,
            "min_up_ratio": 0.70,
        },
        "stock": {
            "min_volume_ratio": 1.2,
            "min_float_mv": 30000000000,
        },
        "position": {
            "stop_loss_percent": 5.0,
            "take_profit_percent": 10.0,
        },
    }

    def tune(
        self, review_result: Dict[str, Any], current_params: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """根据评估结果调整参数

        Args:
            review_result: strategy-reviewer 的分析结果
            current_params: 当前参数配置

        Returns:
            dict: {
                "suggested_params": {...},
                "changes": [...],
                "confidence": 0.0-1.0,
                "auto_apply": bool
            }
        """
        if current_params is None:
            current_params = self.DEFAULT_PARAMS.copy()

        changes = []
        suggested = dict(current_params)

        # 分析形态胜率
        pattern_analysis = review_result.get("pattern_analysis", {})
        for pattern, data in pattern_analysis.items():
            win_rate = data.get("win_rate", 0.5)
            trades = data.get("trades", 0)

            if win_rate < 0.4 and trades >= 5:
                # 降低该形态阈值需要更严格的筛选，但这里简化处理
                changes.append(
                    {
                        "param": f"pattern_{pattern}_threshold",
                        "old_value": "current",
                        "new_value": "stricter",
                        "reason": f"胜率 {win_rate * 100:.0f}% 低于40%，需改进",
                    }
                )

            elif win_rate > 0.7 and trades >= 5:
                changes.append(
                    {
                        "param": f"pattern_{pattern}_threshold",
                        "old_value": "current",
                        "new_value": "looser",
                        "reason": f"胜率 {win_rate * 100:.0f}% 表现优异，可降低阈值提高覆盖率",
                    }
                )

        # 分析板块胜率
        sector_analysis = review_result.get("sector_analysis", {})
        for sector, data in sector_analysis.items():
            win_rate = data.get("win_rate", 0.5)

            if win_rate < 0.35:
                changes.append(
                    {
                        "param": f"sector_{sector}_threshold",
                        "old_value": "current",
                        "new_value": "suspended",
                        "reason": f"板块 '{sector}' 胜率 {win_rate * 100:.0f}% 低于35%，建议暂停",
                    }
                )

        # 计算置信度
        confidence = self._calculate_confidence(review_result)

        # 置信度≥0.7时自动应用
        auto_apply = confidence >= 0.7

        return {
            "suggested_params": suggested,
            "changes": changes,
            "confidence": round(confidence, 2),
            "auto_apply": auto_apply,
        }

    def persist(self, tune_result: dict, trade_date: str = None) -> dict:
        """
        将调参结果写入 SQLite。
        表: strategy_tuning_log (field_name, old_value, new_value, reason, confidence, trade_date, created_at)
        """
        import sqlite3, json
        from datetime import datetime

        db_path = "/mnt/c/Users/WINGO/Documents/WorkSpace/trading-system/data/stockexpert.db"
        trade_date = trade_date or datetime.now().strftime("%Y-%m-%d")

        try:
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS strategy_tuning_log (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    field_name  TEXT NOT NULL,
                    old_value   TEXT,
                    new_value   TEXT,
                    reason      TEXT,
                    confidence  REAL,
                    trade_date  TEXT,
                    created_at  TEXT DEFAULT (datetime('now', 'localtime'))
                )
            """)
            for change in tune_result.get("changes", []):
                conn.execute("""
                    INSERT INTO strategy_tuning_log
                        (field_name, old_value, new_value, reason, confidence, trade_date)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    change.get("param"),
                    change.get("old_value"),
                    change.get("new_value"),
                    change.get("reason"),
                    tune_result.get("confidence"),
                    trade_date,
                ))
            conn.commit()
            conn.close()
            return {"status": "success", "count": len(tune_result.get("changes", []))}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _calculate_confidence(self, review_result: Dict) -> float:
        """计算置信度"""
        summary = review_result.get("summary", {})
        total_trades = summary.get("total_trades", 0)

        # 样本数量得分
        if total_trades >= 30:
            sample_score = 1.0
        elif total_trades >= 20:
            sample_score = 0.7
        elif total_trades >= 10:
            sample_score = 0.5
        else:
            sample_score = 0.3

        # 趋势得分（基于胜率）
        win_rate = summary.get("win_rate", 0.5)
        if win_rate >= 0.7 or win_rate <= 0.3:
            trend_score = 1.0
        elif win_rate >= 0.6 or win_rate <= 0.4:
            trend_score = 0.6
        else:
            trend_score = 0.3

        # 综合置信度
        confidence = sample_score * 0.6 + trend_score * 0.4

        return min(1.0, confidence)
