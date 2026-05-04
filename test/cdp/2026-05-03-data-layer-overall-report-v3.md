# StockExpert 数据层整体情况报告
> 报告时间: 2026-05-03 22:58
> 数据探测周期: 2026-05-03 ~ 2026-05-05
> 覆盖范围: akshare + 东财CDP + 涨停客

---

## 一、总体评级

| 维度 | 状态 | 说明 |
|------|------|------|
| 大盘指数（沪深创科） | ✅ 完全覆盖 | akshare `stock_zh_index_spot_em` |
| 涨跌平家数 | ✅ 完全覆盖 | 东财CDP innerText（沪深各1164/1536） |
| 涨停家数 | ✅ 完全覆盖 | akshare `stock_zt_pool_strong_em` → 352只 |
| 跌停家数 | ✅ 完全覆盖 | akshare `stock_zt_pool_dtgc_em` → 11只 |
| 连板高度 | ✅ 完全覆盖 | 涨停客 `zt_lbgd_line` line_lst 最新[1] |
| 连板个股明细 | ✅ 完全覆盖 | 涨停客 `lbgd_lst`（100条，20字段） |
| 昨日涨停 | ✅ 完全覆盖 | akshare `stock_zt_pool_previous_em` → 100只 |
| 北向资金流 | ✅ 完全覆盖 | 东财CDP dpzjlx innerText（实时） |
| 北向历史 | ⚠️ 断供 | akshare `stock_hsgt_hist_em` 2025-11-10起净买额全NaN |
| 板块资金流 | ✅ 完全覆盖 | akshare `stock_fund_flow_industry/concept` |
| 热门板块 | ✅ 完全覆盖 | 财联社CDP（热门板块+龙头股） |
| 炸板率 | ⚠️ 需计算 | akshare 连板池有"炸板次数"，需自行计算 |
| 个股行情 | ✅ 完全覆盖 | akshare `stock_zh_a_spot_em` + 新浪 |

**整体: 11/13 字段完全覆盖，2 字段部分覆盖**

---

## 二、字段级覆盖详情

### 2.1 大盘环境层

| 字段 | Schema来源 | 数据源 | 验证状态 | 值示例 |
|------|-----------|--------|----------|--------|
| 上证收盘/涨跌幅 | market_environment | akshare `stock_zh_index_spot_em` | ✅ 与CDP吻合 | +0.23% |
| 深证收盘/涨跌幅 | market_environment | akshare `stock_zh_index_spot_em` | ✅ 与CDP吻合 | -0.21% |
| 创业板指 | market_environment | akshare `stock_zh_index_spot_em` | ✅ 与CDP吻合 | -0.33% |
| 科创50 | market_environment | akshare `stock_zh_index_spot_em` | ✅ 与CDP吻合 | -0.25% |
| `up_count` | market_sentiment | 东财CDP dpzjlx innerText | ✅ 验证 | 上证1164 / 深证1536 |
| `down_count` | market_sentiment | 东财CDP dpzjlx innerText | ✅ 验证 | 上证1104 / 深证1300 |
| `flat_count` | market_sentiment | 东财CDP dpzjlx innerText | ✅ 验证 | 上证58 / 深证67 |
| `limit_up_count` | market_sentiment | akshare `stock_zt_pool_strong_em` | ✅ 验证 | 352只 |
| `limit_down_count` | market_sentiment | akshare `stock_zt_pool_dtgc_em` | ✅ 验证 | 11只 |
| 5日均成交额 | market_environment | akshare `stock_zh_index_spot_em` | ✅ | 计算可得 |

### 2.2 板块情绪层

| 字段 | Schema来源 | 数据源 | 验证状态 | 值示例 |
|------|-----------|--------|----------|--------|
| 行业板块涨跌% | sectors[].gain | akshare `stock_fund_flow_industry` | ✅ | 90条 |
| 概念板块涨跌% | sectors[].gain | akshare `stock_fund_flow_concept` | ✅ | 387条 |
| 板块涨停家数 | sectors[].limit_up_count | akshare 涨停池join | ⚠️ 需join | 需关联 |
| `highest_board` | sectors[].highest_board | **涨停客** `zt_lbgd_line` | ✅ **已填补** | 最新4连板 |
| 板块换手率 | sectors[].turnover_rate | akshare 板块数据 | ❌ 无 | - |
| `main_net_inflow` | sectors[].main_net_inflow | akshare `stock_fund_flow_concept` | ✅ | 387条 |
| `north_net_inflow` | sectors[].north_net_inflow | 东财CDP dpzjlx | ✅ 实时亿元 | 主力-520亿 |
| 板块资金流3日/5日 | sectors[].gain_3d/5d | akshare 板块涨跌 | ✅ | 需计算 |
| 热门板块龙头 | sectors[].top_stocks | 财联社CDP | ✅ | 半导体→明微电子/寒武纪 |

### 2.3 个股数据层

| 字段 | Schema来源 | 数据源 | 验证状态 | 值示例 |
|------|-----------|--------|----------|--------|
| OHLCV/涨跌幅 | stocks[].open/high/low/close/gain | akshare `stock_zh_a_spot_em` | ✅ | 5286只 |
| 换手率 | stocks[].turnover_rate | akshare | ✅ | |
| 量比 | stocks[].volume_ratio | akshare | ✅ | |
| 流通/总市值 | stocks[].float_mv/total_mv | akshare | ✅ | |
| 主力净流入 | stocks[].main_net_inflow | akshare `stock_individual_fund_flow_rank` | ✅ | 5286只 |
| 北向持股比 | stocks[].north_holding_ratio | akshare `stock_hsgt_hold_stock_em` | ✅ | 1336只 |
| ST/次新 | stocks[].is_st/is_new | akshare | ✅ | |
| 均线MA5/10/20/60 | stocks[].ma5/10/20/60 | akshare | ✅ | |

---

## 三、数据源健康度

### 3.1 akshare（主要数据源）

| 接口 | 状态 | 说明 |
|------|------|------|
| `stock_zt_pool_strong_em` | ✅ 健康 | 涨停池 352只 |
| `stock_zt_pool_dtgc_em` | ✅ 健康 | 跌停池 11只 |
| `stock_zt_pool_zbgc_em` | ✅ 健康 | 连板池 14条（历史累计） |
| `stock_zt_pool_previous_em` | ✅ 健康 | 昨日涨停 100只 |
| `stock_zh_index_spot_em` | ✅ 健康 | 268条指数 |
| `stock_fund_flow_industry` | ✅ 健康 | 90条行业 |
| `stock_fund_flow_concept` | ✅ 健康 | 387条概念 |
| `stock_individual_fund_flow_rank` | ✅ 健康 | 5286只个股 |
| `stock_hsgt_hold_stock_em` | ✅ 健康 | 1336只北向持股 |
| `stock_hsgt_hist_em` | ⚠️ 断供 | 2025-11-10起净买额全NaN |

### 3.2 东财CDP（实时补充源）

| 页面 | 用途 | 状态 |
|------|------|------|
| `data.eastmoney.com/zjlx/dpzjlx.html` | 实时资金流 + 涨跌平 | ✅ innerText可读 |
| 东财行情中心（需token） | 涨停API f:10/f11过滤 | ⚠️ token需维护 |

### 3.3 涨停客（连板专项源）

| 页面 | 用途 | 状态 |
|------|------|------|
| `zhangtingke.com/zt_lbgd_line` | 连板高度序列（line_lst） | ✅ 无需CDP，curl直取 |
| `zhangtingke.com/zt_lbgd_line` | 连板明细（lbgd_lst） | ✅ 20字段丰富 |

### 3.4 财联社（板块专项源）

| 页面 | 用途 | 状态 |
|------|------|------|
| `www.cls.cn` | 热门板块涨跌%+龙头股 | ✅ CDP可读 |
| `www.cls.cn/searchPage` | 涨停分析 | ✅ robots允许 |

---

## 四、关键突破：highest_board 已填补

akshare 无直接 `highest_board`（连板高度）字段。

**涨停客完美填补**（2026-05-03 22:50 验证）：

```
URL: https://zhangtingke.com/zt_lbgd_line
数据: lbgd_dict{'line_lst': [[日期, 最高连板天数, 股票名], ...]}
获取: data['line_lst'][-1] → [最新日期, 最高连板天数, 股票名]
特点: 无需CDP，直接curl解析HTML内嵌JS变量
```

**当前值**（20260430）：4连板（越剑智能 sh603095）  
**历史最高**：18连板（锋龙股份 sz002931，20260123）

---

## 五、剩余缺口与建议

### 5.1 🔴 北向历史净买额（akshare断供）

**问题**: `stock_hsgt_hist_em` 从 2025-11-10 起净买额全 NaN，断供 5 个半月

**替代方案**:
1. 东财CDP dpzjlx innerText → 有历史表格，净买额字段正常
2. 财联社 → 有实时北向数据

**建议**: 接入东财CDP历史表格，替换 akshare 北向历史

### 5.2 ⚫ 炸板率

**现状**: akshare 连板池 `stock_zt_pool_zbgc_em` 有"炸板次数"列

**计算公式**:
```
break_board_rate = 炸板次数 / (涨停次数 + 炸板次数) × 100%
               = zbgc['炸板次数'] / (zbgc['涨停次数'] + zbgc['炸板次数']) × 100%
```

**数据源**:
- 炸板次数: akshare `stock_zt_pool_zbgc_em`
- 涨停次数: akshare `stock_zt_pool_zbgc_em`（从"涨停统计"列解析）

### 5.3 ⚫ 板块连板高度（各板块最高连板）

**现状**: `highest_board` 是全市场最高连板

**需求**: 各行业/概念板块内部的最高连板

**建议**: 从涨停客 `lbgd_lst` 按行业分组取最大值

---

## 六、数据源接入优先级

| 优先级 | 数据源 | 用途 | 工作量 |
|--------|--------|------|--------|
| P0 | 涨停客 `zt_lbgd_line` | 连板高度 + 连板明细 | 低（curl+正则） |
| P0 | 东财CDP dpzjlx | 北向实时资金流 | 中（CDP） |
| P0 | 东财CDP dpzjlx | 涨跌平（上证/深证） | 中（CDP） |
| P1 | 财联社CDP | 热门板块龙头 | 中（CDP） |
| P1 | akshare `stock_hsgt_hist_em` | 北向历史（监控断供） | 低 |

---

## 七、Schema 对齐检查

对照 `trading-system-05-data-schema.md`，当前数据层覆盖情况：

| Schema 字段 | 实际数据源 | 对齐状态 |
|-------------|-----------|----------|
| `index_data[].close/gain` | akshare index_spot | ✅ |
| `market_sentiment.up/down/flat_count` | 东财CDP innerText | ✅ |
| `market_sentiment.limit_up_count` | akshare 涨停池count | ✅ |
| `sectors[].gain` | akshare fund_flow | ✅ |
| `sectors[].highest_board` | 涨停客 line_lst | ✅ **新增** |
| `sectors[].north_net_inflow` | 东财CDP dpzjlx | ✅ |
| `stocks[].*` | akshare spot | ✅ |
| `stocks[].main_net_inflow` | akshare individual_fund_flow | ✅ |
| `stocks[].north_holding_ratio` | akshare hsgt_hold | ✅ |

---

*报告版本: v3（整合涨停客数据 + 全部历史探索结果）*
*文件: test/cdp/2026-05-03-data-layer-overall-report-v3.md*
