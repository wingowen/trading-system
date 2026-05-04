# Trading System 新功能设计规格

**作者：** Hermes Agent  
**日期：** 2026-05-04  
**状态：** 已批准  
**版本：** 1.0

---

## 概述

为 StockExpert 交易系统新增 3 个前端页面 + 3 个后端 API，扩展数据看板为完整的交易记录与策略分析平台。

---

## 一、整体架构

### 1.1 页面结构

在现有单页看板基础上，新增 **Tab 切换** 导航：

```
┌─────────────────────────────────────────────────────────┐
│  📊 StockExpert                                          │
│  [数据看板] [交易日志] [策略评估] [编排器]                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│            各 Tab 对应独立内容区                         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

- 复用现有 `app.py` Flask 服务（端口 5789）
- 每个 Tab 内容区对应一个 `<div id="tab-xxx">`
- Tab 切换用 JS 控制 `display: none/block`，不刷新页面
- API 保持 JSON，跨 Tab 共用 `/api/*`

### 1.2 路由设计

| 路由 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/trades` | GET | 查询交易记录列表（支持分页/过滤） | ✅ |
| `/api/trades` | POST | 录入入场记录 | ✅ |
| `/api/trades/<trade_id>` | PUT | 更新出场记录 | ✅ |
| `/api/trades/<trade_id>` | GET | 获取单笔交易详情 | ✅ |
| `/api/trades/summary` | GET | 交易汇总统计（胜率/盈亏等） | ✅ |
| `/api/strategy-review` | GET | 策略评估报告 | ✅ |
| `/api/orchestrator/run` | POST | 触发编排器执行 | ✅ |
| `/api/orchestrator/history` | GET | 编排器历史执行记录 | ✅ |

---

## 二、交易日志页面

### 2.1 界面布局

```
┌─────────────────────────────────────────────────────────┐
│  交易日志                              [+ 新增入场]      │
├─────────────────────────────────────────────────────────┤
│  状态: [全部▼] [持仓中] [已平仓] [全部]    日期: 2024-01-01 ~ 2024-12-31  [搜索] │
├─────────────────────────────────────────────────────────┤
│  #   代码   名称    形态   入场日期  持仓天数  盈亏%   状态   操作 │
│  1  600519 贵州茅台 突破   2026-01-10  5天    +3.2%  持仓中  [平仓] │
│  2  002475 立讯精密 回调   2026-01-05  8天    -1.5%  已平仓  [查看] │
└─────────────────────────────────────────────────────────┘
```

### 2.2 入场录入弹窗

点击「新增入场」弹出：

```
┌────────────────────────────────────────┐
│  📝 记录入场                        [×] │
├────────────────────────────────────────┤
│  交易ID: auto-generated (可编辑)        │
│  股票代码: [          ] 名称: [自动填充] │
│  入场日期: [2026-05-04]                  │
│  入场价格: [      ]  数量: [      ]     │
│  形态:   [突破▼]                        │
│  板块:   [AI/消费电子/...]              │
│  ── 市场环境（自动带入，可修改）──       │
│  大盘评分: [80]  板块共振: [75]         │
│  止损价格: [      ]  止盈价格: [      ] │
│  仓位:   [10%]                          │
│  入场原因: [                        ]   │
│                    [取消]  [确认入场]   │
└────────────────────────────────────────┘
```

**入场时自动带入逻辑：**
- 调用 `/api/records?date=<入场日期>&session=morning` 获取当日市场评分
- `大盘评分` → 从 `index_chg_sh000001` 换算（涨跌幅 ×10，+50 基线）
- `板块共振` → 暂固定填 50，后续编排器完善后接入

### 2.3 平仓弹窗

点击「平仓」弹出：

```
┌────────────────────────────────────────┐
│  📤 记录平仓                        [×] │
├────────────────────────────────────────┤
│  股票: 贵州茅台 (600519)               │
│  入场: 2026-01-10 @ 1850.00            │
│  持仓天数: 5天                         │
│  ── 平仓信息 ──                        │
│  平仓日期: [2026-05-04]                │
│  平仓价格: [      ]                    │
│  平仓原因: [主动止盈▼]                 │
│           [触及止损] [基本面变化] [其他] │
│  ── 计算结果 ──                        │
│  盈亏: +3.2% (+2960元)                │
│                    [取消]  [确认平仓]   │
└────────────────────────────────────────┘
```

### 2.4 交易列表 API

**GET `/api/trades`**

Query params:
- `status`: `holding` | `closed` | `all`（默认 `all`）
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD
- `sector`: 板块过滤
- `pattern`: 形态过滤
- `page`: 页码（默认 1）
- `page_size`: 每页条数（默认 20）

Response:
```json
{
  "trades": [
    {
      "trade_id": "T20260105001",
      "code": "600519",
      "name": "贵州茅台",
      "pattern": "突破",
      "sector": "白酒",
      "buy_date": "2026-01-10",
      "buy_price": 1850.0,
      "quantity": 100,
      "stop_loss": 1757.5,
      "take_profit": 2035.0,
      "market_env_score": 78,
      "sector_score": 72,
      "status": "holding",
      "pnl_percent": null,
      "pnl_amount": null,
      "holding_days": null,
      "created_at": "2026-01-10 09:30:00"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20,
  "summary": {
    "total": 10,
    "holding": 2,
    "closed": 8,
    "win_count": 5,
    "loss_count": 3,
    "win_rate": 0.625
  }
}
```

**POST `/api/trades`** — 入场

Request:
```json
{
  "trade_id": "T20260504001",
  "code": "600519",
  "name": "贵州茅台",
  "buy_price": 1850.0,
  "buy_date": "2026-05-04",
  "quantity": 100,
  "pattern": "突破",
  "sector": "白酒",
  "market_env_score": 78,
  "sector_score": 72,
  "stop_loss": 1757.5,
  "take_profit": 2035.0,
  "position_size": 10.0,
  "reason": "突破前高，量价齐升"
}
```

**PUT `/api/trades/<trade_id>`** — 平仓

Request:
```json
{
  "sell_price": 1910.0,
  "sell_date": "2026-05-04",
  "reason": "主动止盈",
  "pnl_percent": 3.24,
  "holding_days": 5
}
```

---

## 三、策略评估页面

### 3.1 界面布局

```
┌─────────────────────────────────────────────────────────┐
│  策略效果评估                        时间范围: [近30天▼]  │
├─────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ 总交易数  │ │ 胜率     │ │ 盈亏比   │ │ 平均持仓 │   │
│  │   28     │ │  64.3%   │ │  1.82    │ │  6.2天   │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
├───────────────────────────┬─────────────────────────────┤
│  按形态分析                │  按板块分析                  │
│  ┌─────────────────────┐  │  ┌─────────────────────┐    │
│  │ 突破    12次  75%  ✅│  │  │ AI       8次  80%  ✅│    │
│  │ 回调    10次  50%   │  │  │ 白酒      6次  66%   │    │
│  │ 盘整     6次  33%   │  │  │ 半导体   5次  40%   │    │
│  └─────────────────────┘  │  └─────────────────────┘    │
├───────────────────────────┴─────────────────────────────┤
│  按市场环境分析                                          │
│  高分(80-100)  10次  80% ✅                             │
│  中分(60-80)   12次  58%                                 │
│  低分(<60)      6次  33% ⚠️                             │
├─────────────────────────────────────────────────────────┤
│  结论: 整体胜率64.3%表现良好。突破形态胜率75%最佳。       │
│  建议: 可适当提高突破形态覆盖率；低分市场环境减少仓位      │
└─────────────────────────────────────────────────────────┘
```

### 3.2 API

**GET `/api/strategy-review`**

Query params:
- `start_date`: YYYY-MM-DD
- `end_date`: YYYY-MM-DD
- `min_trades`: 最小交易样本数（默认 3）

Response:
```json
{
  "summary": {
    "total_trades": 28,
    "win_trades": 18,
    "loss_trades": 10,
    "win_rate": 0.643,
    "avg_pnl": 2.8,
    "avg_win": 5.2,
    "avg_loss": -2.86,
    "profit_loss_ratio": 1.82,
    "avg_holding_days": 6.2
  },
  "pattern_analysis": {
    "突破": {"trades": 12, "win_rate": 0.75, "avg_pnl": 4.1},
    "回调": {"trades": 10, "win_rate": 0.50, "avg_pnl": 1.2}
  },
  "sector_analysis": {
    "AI": {"trades": 8, "win_rate": 0.80, "avg_pnl": 5.5},
    "白酒": {"trades": 6, "win_rate": 0.66, "avg_pnl": 2.1}
  },
  "market_env_analysis": {
    "high_score_80_100": {"trades": 10, "win_rate": 0.80},
    "mid_score_60_80":  {"trades": 12, "win_rate": 0.58},
    "low_score_below_60": {"trades": 6, "win_rate": 0.33}
  },
  "conclusion": "整体胜率64.3%表现良好。突破形态胜率75%最佳。",
  "suggestions": [
    "可适当提高突破形态覆盖率",
    "低分市场环境(60以下)建议减少仓位"
  ]
}
```

---

## 四、编排器面板

### 4.1 界面布局

```
┌─────────────────────────────────────────────────────────┐
│  交易编排器                    [▶ 执行分析]   [历史记录]  │
├─────────────────────────────────────────────────────────┤
│  日期: [2026-05-04]  Session: [晨报▼]                   │
├─────────────────────────────────────────────────────────┤
│  ┌─ 大盘环境 ──────────────────────────────┐            │
│  │  评分: 78/100  ✅ 可交易                │            │
│  │  上证: +1.2%  创业板: +0.8%  科创50: -0.3%│          │
│  │  涨停: 38家  跌停: 5家                  │            │
│  │  通过项: ✓ 上证站上5日线 ✓ 涨停≥12     │            │
│  │  未通过: ✗ 成交量正常                   │            │
│  └──────────────────────────────────────────┘            │
│                                                         │
│  ┌─ 强势板块 ──────────────────────────────────┐        │
│  │  1. AI/人工智能    得分 82  3日涨幅 +4.2%   │        │
│  │  2. 半导体         得分 76  3日涨幅 +2.8%   │        │
│  │  3. 新能源车       得分 68  3日涨幅 +1.5%   │        │
│  └──────────────────────────────────────────────┘        │
│                                                         │
│  ┌─ 候选股票 ──────────────────────────────────┐        │
│  │  [AI板块] 科大讯飞  突破右侧形态  流通市值中│        │
│  │  [AI板块] 寒武纪    量比 2.3  MACD 金叉    │        │
│  └──────────────────────────────────────────────┘        │
│                                                         │
│  ┌─ 持仓状态 ──────────────────────────────────┐        │
│  │  贵州茅台 100股  成本1850  现价1910  +3.2%  │        │
│  │  止损: 1757.5   止盈: 2035                │        │
│  │  状态: ✅ 正常（未触发）                    │        │
│  └──────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
```

### 4.2 API

**POST `/api/orchestrator/run`**

Request:
```json
{
  "date": "2026-05-04",
  "session": "morning",
  "positions": [
    {
      "code": "600519",
      "name": "贵州茅台",
      "quantity": 100,
      "buy_price": 1850.0,
      "stop_loss": 1757.5,
      "take_profit": 2035.0
    }
  ]
}
```

Response:
```json
{
  "mode": "daily_scan",
  "market_env": {
    "tradable": true,
    "score": 78,
    "reasons": ["上证站上5日线", "涨停家数≥12"],
    "checks": {
      "above_ma5": true,
      "limit_up_ok": true,
      "volume_ok": false
    },
    "index_data": {
      "shanghai": {"close": 1.2},
      "sz399001": {"close": 0.9}
    }
  },
  "strong_sectors": [
    {"name": "AI/人工智能", "score": 82, "metrics": {"daily_gain": 4.2}}
  ],
  "candidates": [
    {"code": "000230", "name": "科大讯飞", "pattern": "突破右侧形态", "sector": "AI/人工智能"}
  ],
  "positions_status": [
    {
      "code": "600519",
      "name": "贵州茅台",
      "holding_days": 5,
      "current_price": 1910.0,
      "pnl_percent": 3.24,
      "stop_loss_triggered": false,
      "take_profit_triggered": false,
      "alert": null
    }
  ],
  "alerts": []
}
```

**GET `/api/orchestrator/history`**

Query params: `date`, `limit`（默认 10）

---

## 五、技术实现

### 5.1 新增后端文件

| 文件 | 说明 |
|------|------|
| `src/data/api_trades.py` | 交易日志 CRUD API |
| `src/data/api_strategy.py` | 策略评估 API |
| `src/data/api_orchestrator.py` | 编排器 API + 数据采集 |

**注意：** 所有新 API 复用现有 `app.py` 的 `require_api_key` 装饰器模式。

### 5.2 数据库变更

**trade_journal 表已有**，但**缺少 `status` 字段**（用于快速判断持仓/已平仓）。新增字段：

```sql
ALTER TABLE trade_journal ADD COLUMN status TEXT DEFAULT 'holding';
-- holding / exited
```

并在使用时同步维护：`record_entry` 时设为 `holding`，`record_exit` 时设为 `exited`。

### 5.3 前端变更

在 `app.py` 的 `HTML_TEMPLATE` 中：

1. **新增 Tab 导航栏**（Header 区）
2. **新增 4 个 Tab 内容区**：
   - `<div id="tab-dashboard">` — 现有内容（重命名）
   - `<div id="tab-trades">` — 交易日志
   - `<div id="tab-strategy">` — 策略评估
   - `<div id="tab-orchestrator">` — 编排器
3. **Tab 切换 JS**：用 `display` 控制显隐，不刷新
4. **Modal 组件**：新增入场弹窗、平仓弹窗
5. **API 调用**：新增 `loadTrades()`, `loadStrategyReview()`, `loadOrchestrator()` 等

### 5.4 入口时序

```
页面加载 → loadDates() → loadData()
                    ↓
            同时加载 4 个 Tab 的初始数据（按需懒加载）
            Tab 切换时触发各自 loadXxx()
```

---

## 六、实现顺序

1. **Phase 1**: 后端 API — `api_trades.py`（交易日志 CRUD）
2. **Phase 2**: 前端 — Tab 导航 + 交易日志页面（列表+录入+平仓）
3. **Phase 3**: 后端 API — `api_strategy.py`（策略评估）
4. **Phase 4**: 前端 — 策略评估页面
5. **Phase 5**: 后端 API — `api_orchestrator.py`（编排器）
6. **Phase 6**: 前端 — 编排器面板

---

## 七、待确认事项

- [x] `trade_journal` 表已有，但无 `status` 字段，需 ALTER TABLE ADD COLUMN status。
- [x] 板块数据来源：akshare 行业板块历史接口，按需精准获取强势板块（前5）。
- [x] 个股数据来源：只查强势板块成分股（前10/板块），不拉全市场。

---

## 八、成功标准

- [ ] 交易日志可正常录入入场/出场记录
- [ ] 策略评估页面显示胜率/盈亏比/形态/板块分组数据
- [ ] 编排器面板显示大盘评分、板块、候选股（真实数据）
- [ ] 所有 API 均需 `X-API-Key` 认证
- [ ] Tab 切换流畅，不刷新页面
- [ ] 现有数据看板功能不受影响

## 九、数据采集规格（按需精准获取）

### 9.1 采集原则

只获取需要的数据，不批量拉全市场。采集链路：

```
获取板块列表 -> 筛选强势板块 Top5 -> 获取成分股 Top10/板块 -> 获取成分股实时行情 -> 组装喂入 analyzers
```

### 9.2 新增采集文件

`src/data/fetchers/sector_stock_fetcher.py`

```python
def fetch_strong_sectors(top_n: int = 5) -> list[dict]:
    # 1. ak.stock_board_industry_name_em() 获取全部行业板块
    # 2. ak.stock_board_industry_hist_em() 取近5日历史
    # 3. 计算5日涨幅，筛选 TopN
    # 返回 [{name, daily_gain, gain_5d, up_ratio, volume_rank}, ...]

def fetch_sector_stocks(sector_name: str, top_n: int = 10) -> list[dict]:
    # 1. ak.stock_board_industry_cons_em(symbol=sector_name)
    # 2. 取成交量排名 TopN
    # 返回 [{code, name, close, volume, amount, is_st}, ...]

def enrich_stock_metrics(code: str) -> dict:
    # 1. ak.stock_zh_a_hist() 取近25日数据
    # 2. 计算 MA5/MA10/MA20
    # 3. 计算量比 = 今日成交量 / 5日均量
    # 返回 {code, close, ma5, ma10, ma20, volume_ratio, is_st, float_mv}
```

### 9.3 编排器执行数据流

```
POST /api/orchestrator/run
  ├─ Step 1: _fetch_market_data()       <- db_reader.get_field() 已有
  ├─ Step 2: fetch_strong_sectors()      <- akshare，按需精准
  │     └─ sector_resonance.analyze()
  ├─ Step 3: 对每个强势板块调用 fetch_sector_stocks()
  │     └─ 对每只股票调用 enrich_stock_metrics()
  │           └─ stock_screener.analyze()
  └─ Step 4: position_tracker.track()
```

### 9.4 性能注意事项

- 不并发：单线程顺序采集，避免 akshare 服务器压力
- 超时控制：单板块采集超时 15s，整次编排器执行超时 60s
- 错误容忍：单板块/单股票失败不影响全局，记录错误继续

