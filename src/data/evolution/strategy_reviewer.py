"""
策略效果评估器
根据 spec 04-layer4-evolution.md：
- 按形态/板块/市场环境分组分析
- 计算胜率、盈亏比
- 生成评估报告和建议
"""

from typing import Any, Dict, List
from collections import defaultdict


class StrategyReviewer:
    """策略效果评估器"""

    def analyze(
        self, trades: List[Dict[str, Any]], start_date: str = None, end_date: str = None
    ) -> Dict[str, Any]:
        """分析交易记录

        Args:
            trades: 交易记录列表
            start_date, end_date: 时间范围

        Returns:
            dict: 包含 summary, pattern_analysis, sector_analysis,
                  market_env_analysis, conclusion, suggestions
        """
        if not trades:
            return self._empty_result()

        # 总体统计
        total = len(trades)
        wins = sum(1 for t in trades if t.get("outcome") == "win")
        losses = sum(1 for t in trades if t.get("outcome") == "loss")

        win_rate = wins / total if total > 0 else 0

        # 计算平均盈亏
        pnls = [t.get("pnl_percent", 0) for t in trades]
        avg_pnl = sum(pnls) / total if total > 0 else 0

        win_pnls = [p for p in pnls if p > 0]
        loss_pnls = [p for p in pnls if p < 0]
        avg_win = sum(win_pnls) / len(win_pnls) if win_pnls else 0
        avg_loss = sum(loss_pnls) / len(loss_pnls) if loss_pnls else 0
        profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        summary = {
            "total_trades": total,
            "win_trades": wins,
            "loss_trades": losses,
            "win_rate": round(win_rate, 2),
            "avg_pnl": round(avg_pnl, 2),
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_loss_ratio": round(profit_loss_ratio, 2),
        }

        # 按形态分析
        pattern_analysis = self._analyze_by_pattern(trades)

        # 按板块分析
        sector_analysis = self._analyze_by_sector(trades)

        # 按市场环境分析
        market_analysis = self._analyze_by_market(trades)

        # 生成结论
        conclusion = self._generate_conclusion(
            summary, pattern_analysis, sector_analysis, market_analysis
        )

        # 生成建议
        suggestions = self._generate_suggestions(
            pattern_analysis, sector_analysis, market_analysis
        )

        return {
            "summary": summary,
            "pattern_analysis": pattern_analysis,
            "sector_analysis": sector_analysis,
            "market_env_analysis": market_analysis,
            "conclusion": conclusion,
            "suggestions": suggestions,
        }

    def _empty_result(self) -> Dict:
        return {
            "summary": {"total_trades": 0, "win_trades": 0},
            "pattern_analysis": {},
            "sector_analysis": {},
            "market_env_analysis": {},
            "conclusion": "无交易数据",
            "suggestions": [],
        }

    def _analyze_by_pattern(self, trades: List[Dict]) -> Dict:
        groups = defaultdict(list)
        for t in trades:
            pattern = t.get("pattern", "unknown")
            groups[pattern].append(t)

        result = {}
        for pattern, group in groups.items():
            total = len(group)
            wins = sum(1 for t in group if t.get("outcome") == "win")
            pnls = [t.get("pnl_percent", 0) for t in group]

            result[pattern] = {
                "trades": total,
                "win_rate": round(wins / total, 2),
                "avg_pnl": round(sum(pnls) / total, 2),
            }

        return result

    def _analyze_by_sector(self, trades: List[Dict]) -> Dict:
        groups = defaultdict(list)
        for t in trades:
            sector = t.get("sector", "unknown")
            groups[sector].append(t)

        result = {}
        for sector, group in groups.items():
            total = len(group)
            wins = sum(1 for t in group if t.get("outcome") == "win")
            pnls = [t.get("pnl_percent", 0) for t in group]

            result[sector] = {
                "trades": total,
                "win_rate": round(wins / total, 2),
                "avg_pnl": round(sum(pnls) / total, 2),
            }

        return result

    def _analyze_by_market(self, trades: List[Dict]) -> Dict:
        groups = defaultdict(list)
        for t in trades:
            score = t.get("market_env_score", 0)
            if score >= 80:
                key = "high_score_80_100"
            elif score >= 60:
                key = "mid_score_60_80"
            else:
                key = "low_score_below_60"
            groups[key].append(t)

        result = {}
        for key, group in groups.items():
            total = len(group)
            wins = sum(1 for t in group if t.get("outcome") == "win")

            result[key] = {
                "trades": total,
                "win_rate": round(wins / total, 2) if total > 0 else 0,
            }

        return result

    def _generate_conclusion(
        self, summary: Dict, pattern: Dict, sector: Dict, market: Dict
    ) -> str:
        lines = []

        if summary.get("win_rate", 0) >= 0.6:
            lines.append(f"整体胜率 {summary['win_rate'] * 100:.0f}% 表现良好")
        elif summary.get("win_rate", 0) < 0.4:
            lines.append(f"整体胜率 {summary['win_rate'] * 100:.0f}% 需要改进")

        # 找出最佳形态
        if pattern:
            best_pattern = max(pattern.items(), key=lambda x: x[1].get("win_rate", 0))
            lines.append(
                f"'{best_pattern[0]}' 形态表现最佳，胜率 {best_pattern[1]['win_rate'] * 100:.0f}%"
            )

        return " ".join(lines) if lines else "数据不足以生成结论"

    def _generate_suggestions(
        self, pattern: Dict, sector: Dict, market: Dict
    ) -> List[str]:
        suggestions = []

        # 根据形态
        for p, data in pattern.items():
            if data.get("win_rate", 0) < 0.4:
                suggestions.append(f"提高 '{p}' 形态筛选阈值")
            elif data.get("win_rate", 0) > 0.7:
                suggestions.append(f"可降低 '{p}' 形态阈值提高覆盖率")

        # 根据市场环境
        for m, data in market.items():
            if data.get("win_rate", 0) < 0.4:
                suggestions.append(f"市场环境 {m} 时减少仓位")

        return suggestions[:3]  # 最多3条建议
