# StockExpert 数据交叉验证报告 v2
> 验证时间: 2026-05-03

## 1. akshare vs 东财CDP 精确对比

### 1.1 涨停/跌停池数量对比

| 指标 | akshare (`stock_zt_pool_strong_em`) | 东财CDP API (`f:10=1`) | 说明 |
|------|-----------------------------------|------------------------|------|
| 涨停池 | 352只 | 401 (CDP日志) / 5528 (最新API) | 差异大，需精确过滤 |
| 跌停池 | 11只 | 61 (CDP日志) | 差异大 |
| 连板池 | 14条 | - | akshare独有 |
| 昨日涨停 | 100只 | - | akshare独有 |

**关键发现**: 东财 `push2.eastmoney.com/api/qt/clist/get` API 的 `f:10` 字段含义不是"涨停标记"，而是"连续涨停天数"（数值=连续涨停天数，非0/1布尔值）。5528是全部A股数量，非涨停数量。

akshare `stock_zt_pool_strong_em` = 352只（强势股涨停池）
akshare `stock_zt_pool_dtgc_em` = 11只（跌停池）
akshare `stock_zt_pool_zbgc_em` = 14条（昨日涨停且今日继续涨停=连板池）

### 1.2 北向资金对比

| 指标 | akshare (`stock_hsgt_hist_em`) | 东财CDP innerText |
|------|-------------------------------|-------------------|
| 日期覆盖 | 2014-11-17 ~ 2026-04-30 | 2026-04-30 ~ 2026-05-03 |
| 净买额数据 | **NaN (2025-11-10起)** | ✅ -520.29亿 (2026-04-30) |
| 主力净流入 | ❌ 无此字段 | ✅ -520.29亿 |
| 超大单净流入 | ❌ 无此字段 | ✅ -209.70亿 |
| 大单净流入 | ❌ 无此字段 | ✅ -310.58亿 |
| 中单净流入 | ❌ 无此字段 | ✅ +60.65亿 |
| 小单净流入 | ❌ 无此字段 | ✅ +459.64亿 |
| 涨跌平 | ❌ 无 | ✅ 上证1164/58/1104 |

**关键发现**: akshare `stock_hsgt_hist_em` 的"当日成交净买额"在2025-11-10之后全部为NaN（数据断供）。东财CDP innerText 读取的 `data.eastmoney.com/zjlx/dpzjlx.html` 是**唯一**有近期（2026年）主力资金流数据的来源。

**最佳策略**: 
- 历史数据（2014~2025-10）: 用 akshare `stock_hsgt_hist_em`
- 近期数据（2025-11~至今）: 用东财CDP innerText

### 1.3 指数行情对比（2026-04-30）

| 指数 | akshare `stock_zh_index_spot_em` | 东财CDP innerText |
|------|----------------------------------|-------------------|
| 上证收盘 | 4112.16 ✅ | 4112.16 ✅ |
| 上证涨跌幅 | +0.11% ✅ | +0.11% ✅ |
| 深证收盘 | 15107.55 ✅ | 15107.55 ✅ |
| 深证涨跌幅 | -0.09% ✅ | -0.09% ✅ |

**结论**: akshare 和 CDP 数据完全一致。

### 1.4 连板高度（highest_board）

akshare `stock_zt_pool_zbgc_em` 返回的"涨停统计"字段格式为 `X/Y`：
- X = 累计涨停次数
- Y = 连板中断次数

示例：`"3/2"` 表示该股历史上涨停3次，其中2次连板后中断。

**但这不是"当前连板高度"**。真正的"连板高度"需要 CDP 从东财涨停详情页读取。

## 2. 最终数据源推荐

| 字段 | 推荐数据源 | 备注 |
|------|----------|------|
| `limit_up_count` | akshare `stock_zt_pool_strong_em` | 352只 ✅ |
| `limit_down_count` | akshare `stock_zt_pool_dtgc_em` | 11只 ✅ |
| `highest_board` | CDP: 东财涨停详情页 `data.eastmoney.com/ztb/` | 需点击读详情 |
| `yesterday_limit_up` | akshare `stock_zt_pool_previous_em` | 100只 ✅ |
| `north_net_inflow` (近期) | 东财CDP innerText `data.eastmoney.com/zjlx/dpzjlx.html` | -520.29亿 ✅ |
| `north_net_inflow` (历史) | akshare `stock_hsgt_hist_em` | 2014~2025-10有效 |
| `market_breadth_*` | 东财CDP innerText | 涨跌平 ✅ |
| `sector_hot` | akshare `stock_fund_flow_industry` | 90条 ✅ |
| `sector_fund_flow` | akshare `stock_fund_flow_concept` | 387条 ✅ |
| `index_spot` | akshare `stock_zh_index_spot_em` | 268条 ✅ |

## 3. 剩余精确度缺口

### 🔴 连板高度（highest_board）
- akshare 连板池的"涨停统计"=`X/Y` 是历史累计，非当前连板
- 需要 CDP 打开 `data.eastmoney.com/ztb/` 某只股票详情，读"连板高度"字段
- **建议**: 直接从 CDP 东财涨停板页面提取

### ⚫ 炸板率
- akshare 连板池有"炸板次数"列
- 炸板率 = 炸板次数 / 总封板次数 × 100%
- akshare 没有直接字段，需计算

---
*验证完成，报告写入 test/cdp/2026-05-03-cross-validation-report-v2.md*
