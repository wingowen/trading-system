# StockExpert 数据覆盖度报告 v2
> 生成时间: 2026-05-03 22:46

## 1. 数据缺口排查结果

| 字段 | 优先级 | 数据源 | akshare | 东财CDP | 状态 |
|------|--------|--------|---------|---------|------|
| `limit_up_count` | 🔴 | 涨停池 strong | ✅ stock_zt_pool_strong_em → 352只 | ✅ (f:10 total=401) | **已覆盖** |
| `limit_down_count` | 🔴 | 跌停池 | ✅ stock_zt_pool_dtgc_em → 11只 | ✅ (f:11 total=61) | **已覆盖** |
| `highest_board` | 🔴 | 连板高度 | ⚠️ stock_zt_pool_zbgc_em → 14条（"涨停统计"列=连板高度）| ❓ 待CDP深挖 | **部分覆盖** |
| `yesterday_limit_up` | 🟡 | 昨日涨停 | ✅ stock_zt_pool_previous_em → 100只 | ❓ | **已覆盖** |
| `north_net_inflow` | 🔴 | 北向资金 | ✅ stock_hsgt_fund_flow_summary_em（各板块涨跌数据）| ✅ 主页 innerText | **已覆盖** |
| `north_net_inflow_hist` | 🟡 | 北向历史 | ✅ stock_hsgt_hist_em → 2661条 | ✅ 40+交易日表格 | **已覆盖** |
| `market_breadth_*` | 🟡 | 涨跌平 | ❌ akshare无此数据 | ✅ 沪深主页innerText | **CDP已覆盖** |
| `sector_hot` | 🟡 | 板块涨跌 | ✅ stock_fund_flow_industry (90条) | ✅ 财联社热门板块 | **已覆盖** |
| `sector_fund_flow` | 🟡 | 板块资金流 | ✅ stock_fund_flow_concept (387条) | ❓ | **已覆盖** |
| `limit_up_detail` | 🟡 | 涨停股详情 | ✅ stock_zt_pool_strong_em (含行业/换手率) | ❓ | **已覆盖** |
| `break_board_rate` | ⚫ | 炸板率 | ⚠️ 连板数据含"炸板次数" | ❓ | **待深挖** |

## 2. 详细验证结果

### 2.1 akshare 覆盖度（2026-05-05 数据）

```
涨停池:       stock_zt_pool_strong_em  → 352 只 ✅
跌停池:       stock_zt_pool_dtgc_em    → 11 只  ✅
连板池:       stock_zt_pool_zbgc_em    → 14 条  ✅（含涨停统计/炸板次数）
昨日涨停:     stock_zt_pool_previous_em → 100 只 ✅

北向资金流:   stock_hsgt_fund_flow_summary_em → ✅
  - 沪股通北向: 成交净买额=0（交易状态3=已休市）
  - 深股通北向: 成交净买额=0
  - 上涨数/持平数/下跌数: 沪693/48/791, 深828/41/848

北向历史:     stock_hsgt_hist_em(symbol="北向资金") → 2661条 ✅

大盘指数:     stock_zh_index_spot_em → 268条 ✅

行业资金流:   stock_fund_flow_industry → 90条 ✅
概念资金流:   stock_fund_flow_concept → 387条 ✅
个股资金流:   stock_individual_fund_flow_rank(indicator="今日") → 5286只 ✅
北向持仓:     stock_hsgt_hold_stock_em → 1336条 ✅
```

### 2.2 东财CDP 人类浏览数据（2026-05-03 数据）

**东财-北向页面** (`data.eastmoney.com/zjlx/dpzjlx.html`)：
```
✅ 完整历史资金流表格（40+交易日）：
  日期 | 上证收盘价/涨跌幅 | 深证收盘价/涨跌幅 | 主力净流入/净占比 | 超大单/大单/中单/小单 净流入/净占比

✅ 实时大盘资金流：
  主力净流入: -520.29亿, 净占比: -1.90%
  超大单净流入: -209.70亿, 净占比: -0.77%
  大单净流入: -310.58亿, 净占比: -1.13%
  中单净流入: +60.65亿, 净占比: +0.22%
  小单净流入: +459.64亿, 净占比: +1.68%

✅ 涨跌平统计（实时）：
  上证: 涨1164 / 平58 / 跌1104
  深证: 涨1536 / 平67 / 跌1300
```

**财联社页面** (`www.cls.cn`)：
```
✅ 上证指数: 4112.16 (+0.11%)
✅ 深证成指: 15107.55 (-0.09%)
✅ 创业板指: 3677.15 (-0.27%)
✅ 热门板块涨跌%：半导体+3.38% | 能源金属+2.50% | 国防军工+1.70% | 电子+1.39% | 房地产+1.29% | 纺服+1.15%
✅ 热门板块龙头：半导体→明微电子/寒武纪
```

### 2.3 东财API vs CDP对比

| 数据 | 东财API | 东财CDP(innerText) |
|------|---------|-------------------|
| 涨停数 | 401 (f:10) | - |
| 跌停数 | 61 (f:11) | - |
| 涨跌平 | ❌ | ✅ 上证1164/58/1104 |
| 北向历史 | ❌ | ✅ 40+交易日 |
| 主力净流入 | ❌ | ✅ -520.29亿 |

## 3. 剩余数据缺口

### 🔴 `highest_board`（连板高度）- 待精确验证
akshare连板池 `stock_zt_pool_zbgc_em` 返回的"涨停统计"列值格式为 `"0/0"`（历史涨停次数/连板中断次数），需要确认这个字段能否直接作为连板高度使用，或者需要CDP从涨停详情页提取。

### ⚫ `break_board_rate`（炸板率）
akshare 连板池有"炸板次数"列，但炸板率 = 炸板次数/涨停次数，需要计算。

### ❓ `market_breadth_*` 精确字段
akshare 无涨跌平数据，需要确认 Layer3 是否接受"涨跌平家数"作为替代，或者只在 CDP 场景下使用。

## 4. 下一步行动

1. **CDP深挖连板详情页**：东财 `data.eastmoney.com/ztb/` 涨停详情页点击某只股票，读取"连板高度"字段
2. **验证连板池字段**：`stock_zt_pool_zbgc_em` 的"涨停统计"列是否为连板高度
3. **CDP获取涨跌平**：东方财富行情中心已有涨跌平数字（沪深各1164/1536涨），确认是否需要精确到个股

---
*报告版本: v2（基于 2026-05-03 CDP人类浏览 + akshare 批量验证）*
