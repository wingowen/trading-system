# A 股免费数据源测试汇总报告

> 测试时间: 2026-05-03 20:28:28
> 测试环境: Python 3.11, WSL

---

## 数据源概览

| 数据源 | 版本 | 安装 | Token | 测试项 | 通过 | 通过率 | 综合评价 |
|--------|------|------|-------|--------|------|--------|----------|
| `akshare` | 1.18.60 | `pip install akshare` | 无需 | 19 | 15 | 78% | ⭐⭐⭐⭐⭐ 数据最全，稳定可靠，首选 |
| `baostock` | 0.9.10 | `pip install baostock` | 无需 | 16 | 15 | 93% | ⭐⭐⭐⭐ 财务数据全，K线免费无限制 |
| `efinance` | 0.5.8 | `pip install efinance` | 无需 | 19 | 10 | 52% | ⭐⭐⭐ 实时行情好，但部分接口有bug |
| `pytdx` | 1.72 | `pip install pytdx` | 无需 | 10 | 0 | 0% | ⭐ 公开服务器不可用，需自建 |
| `tushare` | 1.4.29 | `pip install tushare` | 需注册（有token，积分不足） | 14 | 1 | 7% | ⭐ 仅 stock_basic 可用，需充积分 |


---

## 数据类型覆盖矩阵

| 数据类型 | akshare | baostock | efinance | pytdx | tushare |
|----------|---------|----------|----------|-------|---------|
| **大盘/指数** | ✅ 2项 | ✅ 1项 | - | - | ❌ 2项 |
| **个股行情** | ✅ 2项 | ✅ 1项 | ✅ 1项 | ❌ 1项 | ❌ 1项 |
| **板块数据** | ✅ 4项 | - | ✅ 4项 | - | - |
| **资金流** | ✅ 4项 | - | - | - | ❌ 2项 |
| **龙虎榜** | ✅ 1项 | - | - | - | - |
| **基本面** | ✅ 2项 | ✅ 9项 | ✅ 1项 | - | ❌ 5项 |
| **成分股/指数** | - | ✅ 3项 | ✅ 4项 | - | - |
| **其他** | ❌ 2项 | ✅ 1项 | - | - | ❌ 3项 |


---

## 详细测试结果

### akshare (⭐⭐⭐⭐⭐ 推荐)

**优点**: 数据最全面，接口稳定，免费无需注册，覆盖行情/板块/资金流/龙虎榜/基本面

**可用数据类型**:
- ✅ `test_index_daily`
- ✅ `test_index_spot`
- ✅ `test_stock_daily`
- ✅ `test_industry_board`
- ✅ `test_concept_board`
- ✅ `test_board_cons`
- ✅ `test_board_hist`
- ✅ `test_market_activity`
- ✅ `test_margin_sse`
- ✅ `test_individual_fund_flow`
- ✅ `test_sector_fund_flow`
- ✅ `test_lhb_detail`
- ✅ `test_stock_info`
- ✅ `test_stock_spot`
- ✅ `test_history_dividend`
- ❌ `test_stock_minute` (接口已变更或数据源限制)
- ❌ `test_lhb_start` (接口已变更或数据源限制)
- ❌ `test_limit_list` (接口已变更或数据源限制)
- ❌ `test_profit_predict` (接口已变更或数据源限制)

**失败原因**:
- `test_stock_minute`: akshare 分钟接口名已变更
- `test_lhb_start`: 龙虎榜机构接口名已变更
- `test_limit_list`: 涨停池接口名已变更
- `test_profit_predict`: 业绩预告接口名已变更

---

### baostock (⭐⭐⭐⭐ 推荐)

**优点**: 财务数据最全（杜邦/成长/盈利/运营/资产负债/现金流），历史K线免费无限制，沪深300/上证50/中证500成分股

**可用数据类型**:
- ✅ `test_index_daily`
- ✅ `test_stock_daily`
- ❌ `test_adjust_factor`
- ✅ `test_stock_basic`
- ✅ `test_trade_dates`
- ✅ `test_hs300`
- ✅ `test_sz50`
- ✅ `test_zz500`
- ✅ `test_profit_data`
- ✅ `test_balance_data`
- ✅ `test_cash_flow_data`
- ✅ `test_dupont_data`
- ✅ `test_operation_data`
- ✅ `test_growth_data`
- ✅ `test_dividend_data`
- ✅ `test_stock_industry`

**注意**: `test_adjust_factor` 返回空数据（近期无复权事件，属正常）

---

### efinance (⭐⭐⭐ 补充)

**优点**: 实时行情覆盖全面（行业/概念/沪A/深A/科创板/沪股通），板块成分股、所属板块查询强

**可用数据类型**:
- ✅ `test_realtime_quote_industry`
- ✅ `test_realtime_quote_concept`
- ✅ `test_realtime_quote_sh`
- ✅ `test_realtime_quote_sz`
- ✅ `test_realtime_quote_kcb`
- ✅ `test_realtime_quote_hgt`
- ❌ `test_quote_history`
- ❌ `test_quote_history_minute`
- ✅ `test_quote_snapshot`
- ✅ `test_base_info`
- ✅ `test_members`
- ✅ `test_belong_board`
- ❌ `test_deal_detail`
- ❌ `test_top10_holder`
- ❌ `test_all_report_dates`
- ❌ `test_all_performance`
- ❌ `test_latest_holder_number`
- ❌ `test_latest_ipo`
- ❌ `test_getter`

**已知问题**: jsonpath 内部与 efinance.utils 冲突，导致以下接口报错:
- `test_quote_history` / `test_quote_history_minute` / `test_getter`: K线历史数据
- `test_top10_holder`: 前10股东
- `test_all_report_dates` / `test_all_performance`: 财报日期/业绩
- `test_latest_ipo`: 新股列表
- `test_latest_holder_number`: 股东户数
- `test_deal_detail`: 成交明细

---

### pytdx (⭐ 不推荐)

**问题**: 公开通达信服务器 `118.244.123.178:7709` 被防火墙封锁，无法连接。

**可用接口**（理论）:
- 实时行情 / K线 / 分钟数据 / 财务数据 / 除权除息

**建议**: 
- 如需 pytdx，建议自建通达信行情服务器
- 或使用付费行情服务

---

### tushare (⭐ 积分不足)

**现状**: Token 已配置，但免费账号积分不足，仅 `stock_basic` 可用（1/14）。

**实际测试结果**:
- ✅ `stock_basic` — 5512条全市场股票列表，免费
- ❌ `index_daily` / `index_basic` — 需120积分
- ❌ `daily` — 需2000积分
- ❌ `suspend_d` / `fina_indicator` / `income` / `balancesheet` / `cashflow` — 需120~2000积分
- ❌ `moneyflow` / `hk_hold` / `top_list` / `limit_list` / `stk_rewards` — 需1000~1200积分

**如需解锁**: 充积分（120起步能跑日线/停牌，2000能跑财务），或放弃 tushare 用免费方案。

---

## 推荐数据源组合

### 🥇 方案一：全免费，无需注册
> **akshare + baostock + efinance**

| 数据需求 | 推荐数据源 | 说明 |
|---------|-----------|------|
| **大盘指数日线** | akshare / baostock | akshare 字段全，baostock 无限制 |
| **个股日线** | akshare / baostock | 两者均可，akshare 含更多字段 |
| **实时行情** | efinance / akshare | efinance 全市场快照更快 |
| **行业板块** | akshare / efinance | akshare 含上涨下跌家数 |
| **概念板块** | akshare / efinance | 两者均可 |
| **板块成分股** | akshare / efinance | akshare 实时行情更丰富 |
| **板块历史行情** | akshare | ✅ 仅 akshare 支持 |
| **资金流（个股）** | akshare | 主力/超大单/大单/中单/小单 |
| **资金流（板块）** | akshare | ✅ 仅 akshare 支持 |
| **融资融券** | akshare | 上交所融资融券历史全 |
| **龙虎榜** | akshare | 含上榜后N日收益统计 |
| **股票基本信息** | baostock / akshare | baostock 含行业分类 |
| **杜邦分析** | baostock | ✅ 仅 baostock 支持 |
| **成长能力** | baostock | ✅ 仅 baostock 支持 |
| **运营能力** | baostock | ✅ 仅 baostock 支持 |
| **资产负债** | baostock | ✅ 仅 baostock 支持 |
| **现金流量** | baostock | ✅ 仅 baostock 支持 |
| **分红数据** | baostock / akshare | baostock 更规范 |
| **指数成分股** | baostock | 沪深300/上证50/中证500 |
| **实时全市场快照** | efinance | ✅ 最全最快 |

### 🥈 方案二：tushare（需注册）
> **tushare pro token** → 数据最全面，含期货/期权/基金/基本面等

---

## 目录结构

```
test/
├── datasource/                     # 数据源测试脚本
│   ├── test_akshare.py             # akshare (19项, 15通过)
│   ├── test_baostock.py            # baostock (16项, 15通过)
│   ├── test_efinance.py            # efinance (19项, 10通过)
│   ├── test_pytdx.py               # pytdx (10项, 0通过，服务器不可用)
│   └── test_tushare.py             # tushare (14项, 1通过，积分不足)
├── run_all_tests.py                # 批量测试 + 汇总报告
└── DATA_SOURCES_SUMMARY.md         # 本报告
```

---

*报告生成: 2026-05-03 20:28:28*
