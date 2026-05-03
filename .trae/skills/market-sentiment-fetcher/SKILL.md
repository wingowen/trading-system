---
name: "market-sentiment-fetcher"
description: "Fetches A-share market sentiment data (market activity, margin trading) via AkShare. Invoke when user requests 市场情绪数据, index_sentiment, or needs to query market breadth, activity levels, or margin trading statistics."
---

# Market Sentiment Fetcher

## 概述

通过 AkShare 获取 A 股市场情绪数据，包括市场活跃度、融资融券等指标。

## 支持的功能

### 1. 市场活跃度数据

```python
import akshare as ak

# 获取市场活跃度数据（涨跌家数、涨停跌停、活跃度等）
df = ak.stock_market_activity_legu()

# 返回字段: item, value
# 包含: 上涨家数, 下跌家数, 涨停家数, 跌停家数, 停牌, 活跃度, 统计日期
```

### 2. 融资融券数据

```python
import akshare as ak

# 获取上海证券交易所融资融券数据
df = ak.stock_margin_sse()

# 返回字段: 信用交易日期, 融资余额, 融资买入额, 融券余量, 融券余量金额, 融券卖出量, 融资融券余额
```

## 输入格式

```json
{
  "action": "get_market_activity"
}
```

或

```json
{
  "action": "get_margin_trading"
}
```

## 输出格式

### 市场活跃度输出

```json
{
  "status": "success",
  "data": {
    "trade_date": "2026-05-03",
    "up_count": 2850,
    "down_count": 1200,
    "limit_up_count": 85,
    "limit_down_count": 12,
    "suspended_count": 50,
    "activity_rate": "51.34%"
  }
}
```

### 融资融券输出

```json
{
  "status": "success",
  "data": [
    {
      "trade_date": "2026-05-03",
      "margin_balance": 934271207261,
      "margin_buy": 108699727868,
      "short_selling_volume": 272290354,
      "short_selling_amount": 1857208347,
      "total_margin_balance": 936128415608
    }
  ]
}
```

## 注意事项

1. 数据仅供学术研究，不构成投资建议
2. 接口可能因目标网站变动而失效
3. 建议添加异常处理和重试机制
4. 当前环境网络问题可能导致测试失败，请在本地环境测试
