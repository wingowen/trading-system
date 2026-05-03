# 数据格式规范

## 概述

定义系统各层 Skill 之间通信的标准化 JSON Schema，确保数据格式统一、可互操作。

## 统一字段命名规范

以下字段在所有 Skill 之间统一使用，避免同名异义或异名同义：

| 标准字段名 | 类型 | 含义 | 禁用别名 |
|-----------|------|------|---------|
| `volume` | number | 成交量（股数） | ~~vol~~ |
| `amount` | number | 成交额（元） | ~~total_amount~~, ~~total_volume~~ |
| `gain` | number | 涨跌幅（%） | ~~change_pct~~ |
| `volume_ratio` | number | 量比（当日每分钟均量 / 5日每分钟均量） | - |
| `turnover_rate` | number | 换手率（%） | - |
| `float_mv` | number | 流通市值（元） | - |
| `total_mv` | number | 总市值（元） | - |
| `up_count` | number | 上涨个股数 | - |
| `down_count` | number | 下跌个股数 | - |
| `flat_count` | number | 平盘个股数 | - |
| `limit_up_count` | number | 涨停家数 | - |
| `limit_down_count` | number | 跌停家数 | - |

> **注意**：Tushare API 原始返回使用 `vol` 表示成交量、`amount` 表示成交额，tushare-data-fetcher 在输出时需将 `vol` 映射为 `volume`。

## 通用响应格式

所有 Skill 的输出遵循统一格式：

> **约定**：Orchestrator 内部调用各 Skill 时，Skill 返回裸业务数据（即 `data` 字段内容），由 Orchestrator 负责组装通用响应包装。各 Skill 文档中的输入输出示例均展示裸业务数据格式。Orchestrator 对外（面向用户）的输出使用完整的通用响应包装。

```json
{
  "timestamp": "2026-05-03T15:00:00Z",
  "status": "success",
  "skill_name": "market-environment-analyzer",
  "version": "1.0.0",
  "data": {...},
  "error": null
}
```

### 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| timestamp | string | 是 | ISO 8601 时间戳 |
| status | string | 是 | "success" 或 "error" |
| skill_name | string | 是 | Skill 名称 |
| version | string | 是 | Skill 版本 |
| data | object | 否 | 业务数据（status=success 时） |
| error | object | 否 | 错误信息（status=error 时） |

### 错误格式

```json
{
  "timestamp": "2026-05-03T15:00:00Z",
  "status": "error",
  "skill_name": "tushare-data-fetcher",
  "version": "1.0.0",
  "data": null,
  "error": {
    "code": "API_RATE_LIMIT",
    "message": "API 调用频率超限",
    "retry_after": 60
  }
}
```

---

## 大盘数据格式

### 输入格式

```json
{
  "index_data": {
    "shanghai": {
      "code": "000001.SH",
      "trade_date": "2026-05-03",
      "open": 3240.00,
      "high": 3260.50,
      "low": 3235.20,
      "close": 3250.50,
      "volume": 285000000,
      "amount": 38500000000,
      "ma5": 3230.20,
      "ma10": 3210.80,
      "ma20": 3180.50
    },
    "chi_next": {
      "code": "399006.SZ",
      "trade_date": "2026-05-03",
      "close": 2180.50,
      "ma5": 2165.30,
      "ma10": 2150.80,
      "ma20": 2130.50
    }
  },
  "market_sentiment": {
    "trade_date": "2026-05-03",
    "limit_up_count": 28,
    "limit_down_count": 3,
    "up_count": 3200,
    "down_count": 1500,
    "flat_count": 300,
    "amount": 95000000000
  },
  "volume_5d_avg": 82000000000
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| index_data.shanghai | object | 上证指数数据 |
| index_data.chi_next | object | 创业板指数据 |
| market_sentiment | object | 全市场情绪数据 |
| volume_5d_avg | number | 5日平均成交额 |

---

## 板块数据格式

### 输入格式

```json
{
  "sectors": [
    {
      "name": "半导体",
      "code": "BK0921",
      "type": "industry",
      "trade_date": "2026-05-03",
      "open": 1250.00,
      "high": 1280.50,
      "low": 1245.20,
      "close": 1275.80,
      "gain": 2.5,
      "gain_3d": 4.2,
      "gain_5d": 6.8,
      "volume": 8500000000,
      "amount": 8500000000,
      "ma5": 1260.50,
      "ma10": 1245.80,
      "ma20": 1230.50,
      "up_count": 78,
      "down_count": 22,
      "flat_count": 5,
      "limit_up_count": 3,
      "highest_board": 4,
      "volume_market_ratio": 0.08,
      "main_net_inflow": 2500000000,
      "north_net_inflow": 800000000
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 板块名称 |
| code | string | 板块代码 |
| type | string | "industry" 或 "concept" |
| gain | number | 当日涨幅(%) |
| gain_3d | number | 3日累计涨幅(%) |
| gain_5d | number | 5日累计涨幅(%) |
| up_count | number | 上涨个股数 |
| down_count | number | 下跌个股数 |
| limit_up_count | number | 涨停家数 |
| highest_board | number | 连板高度 |
| volume_market_ratio | number | 成交额占全市场比例 |
| ma5 | number | 5日均线 *(可选，tushare-data-fetcher 提供)* |
| ma10 | number | 10日均线 *(可选)* |
| ma20 | number | 20日均线 *(可选)* |
| flat_count | number | 平盘个股数 *(可选)* |
| main_net_inflow | number | 主力净流入 *(可选，需 money_flow 数据源)* |
| north_net_inflow | number | 北向资金净流入 *(可选，需 money_flow 数据源)* |

---

## 个股数据格式

### 输入格式

```json
{
  "stocks": [
    {
      "code": "688981",
      "name": "中芯国际",
      "sector": "半导体",
      "trade_date": "2026-05-03",
      "open": 44.80,
      "high": 45.50,
      "low": 44.60,
      "close": 45.20,
      "gain": 1.8,
      "volume": 85000000,
      "amount": 3850000000,
      "turnover_rate": 3.2,
      "volume_ratio": 1.5,
      "amplitude": 2.5,
      "float_mv": 18000000000,
      "total_mv": 22000000000,
      "ma5": 44.80,
      "ma10": 44.20,
      "ma20": 43.50,
      "ma60": 42.00,
      "is_st": false,
      "is_new": false,
      "list_date": "2020-07-16",
      "main_net_inflow": 500000000,
      "north_holding_ratio": 0.02
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| code | string | 股票代码 |
| name | string | 股票名称 |
| sector | string | 所属板块 |
| gain | number | 当日涨幅(%) |
| turnover_rate | number | 换手率(%) |
| volume_ratio | number | 量比 |
| amplitude | number | 振幅(%) |
| float_mv | number | 流通市值 |
| total_mv | number | 总市值 |
| is_st | boolean | 是否 ST |
| is_new | boolean | 是否次新股 |
| list_date | string | 上市日期 |
| main_net_inflow | number | 主力净流入 |
| north_holding_ratio | number | 北向持股比例 |

---

## 交易信号格式

### 输出格式

```json
{
  "signal": {
    "code": "688981",
    "name": "中芯国际",
    "sector": "半导体",
    "pattern": "突破右侧",
    "score": 88,
    "current_price": 45.20,
    "suggested_entry": 45.00,
    "stop_loss": 42.94,
    "take_profit": 48.82,
    "position_size": 0.2,
    "risk_reward_ratio": 2.0,
    "entry_reason": "放量突破20日线，均线多头排列",
    "market_env_score": 85,
    "sector_score": 92
  }
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| pattern | string | "突破右侧" 或 "回踩右侧" |
| score | number | 综合评分(0-100) |
| suggested_entry | number | 建议入场价 |
| stop_loss | number | 止损价 |
| take_profit | number | 止盈价 |
| position_size | number | 建议仓位(0-1) |
| risk_reward_ratio | number | 盈亏比（计算公式：(take_profit - suggested_entry) / (suggested_entry - stop_loss)） |

---

## 持仓状态格式

### 输出格式

```json
{
  "positions": [
    {
      "code": "688981",
      "name": "中芯国际",
      "sector": "半导体",
      "buy_price": 45.20,
      "buy_date": "2026-05-03",
      "current_price": 46.50,
      "pnl": 1.30,
      "pnl_percent": 2.87,
      "holding_days": 3,
      "stop_loss": 42.94,
      "take_profit": 48.82,
      "position_size": 0.2,
      "action": "hold",
      "reason": "板块强势延续，未触及止损止盈"
    }
  ]
}
```

---

## 交易日志格式

### 存储格式

```json
{
  "trade_id": "T20260503-001",
  "entry": {
    "code": "688981",
    "name": "中芯国际",
    "price": 45.20,
    "date": "2026-05-03",
    "pattern": "突破右侧",
    "sector": "半导体",
    "market_env_score": 85,
    "sector_score": 92,
    "stop_loss": 42.94,
    "take_profit": 48.82,
    "position_size": 0.2
  },
  "exit": {
    "price": 48.50,
    "date": "2026-05-08",
    "reason": "止盈",
    "pnl_percent": 7.30,
    "holding_days": 5
  },
  "outcome": "win",
  "tags": ["半导体", "突破右侧", "强势板块"],
  "created_at": "2026-05-03T15:00:00Z",
  "updated_at": "2026-05-08T15:00:00Z"
}
```

---

## 策略参数格式

### 存储格式

```json
{
  "version": "v1.0",
  "date": "2026-05-01",
  "params": {
    "market": {
      "min_limit_up_count": 12,
      "max_limit_down_count": 5,
      "min_volume_ratio": 0.8
    },
    "sector": {
      "min_daily_gain": 1.5,
      "min_5d_gain": 5.0,
      "min_up_ratio": 0.70,
      "min_volume_top_rank": 20
    },
    "stock": {
      "min_volume_ratio": 1.2,
      "min_float_mv": 3000000000,
      "max_new_stock_months": 6
    },
    "position": {
      "max_total_position": 0.8,
      "max_per_sector": 2,
      "stop_loss_percent": 5.0,
      "take_profit_percent": 10.0
    }
  }
}
```
