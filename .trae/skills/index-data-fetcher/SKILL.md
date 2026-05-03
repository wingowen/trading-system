---
name: "index-data-fetcher"
description: "Fetches A-share market index daily data (SSE, SZSE, ChiNext, etc.) via AkShare. Invoke when user requests大盘指数数据, index_daily, or needs to query major market indices like 上证指数, 深证成指, 创业板指."
---

# Index Data Fetcher

## 概述

通过 AkShare 获取 A 股大盘指数日线数据，支持上证指数、深证成指、创业板指等主要指数。

## 支持的指数代码

| 指数名称 | 代码 | 说明 |
|---------|------|------|
| 上证指数 | sh000001 | 上海证券交易所综合指数 |
| 深证成指 | sz399001 | 深圳证券交易所成份指数 |
| 创业板指 | sz399006 | 创业板指数 |
| 沪深300 | sh000300 | 沪深300指数 |
| 中证500 | sh000905 | 中证500指数 |
| 科创50 | sh000688 | 科创板50指数 |

## 使用方法

### 1. 获取指数日线数据

```python
import akshare as ak

# 获取上证指数日线数据
df = ak.stock_zh_index_daily(symbol="sh000001")

# 返回字段: date, open, high, low, close, volume
```

### 2. 获取主要指数实时行情

```python
import akshare as ak

# 获取所有主要指数实时行情
df = ak.stock_zh_index_spot_em()

# 返回字段: 序号, 代码, 名称, 最新价, 涨跌幅, 涨跌额, 成交量, 成交额, 振幅, 最高, 最低, 今开, 昨收, 量比
```

## 输入格式

```json
{
  "action": "get_index_daily",
  "symbol": "sh000001",
  "start_date": "2026-04-01",
  "end_date": "2026-05-03"
}
```

或

```json
{
  "action": "get_index_spot"
}
```

## 输出格式

### 日线数据输出

```json
{
  "status": "success",
  "data": [
    {
      "trade_date": "2026-05-03",
      "open": 3240.00,
      "high": 3260.50,
      "low": 3235.20,
      "close": 3250.50,
      "volume": 285000000
    }
  ]
}
```

### 实时行情输出

```json
{
  "status": "success",
  "data": [
    {
      "code": "000001",
      "name": "上证指数",
      "price": 3250.50,
      "change_percent": 0.85,
      "change_amount": 27.35,
      "volume": 285000000,
      "amount": 38500000000
    }
  ]
}
```

## 注意事项

1. 数据仅供学术研究，不构成投资建议
2. 接口可能因目标网站变动而失效
3. 建议添加异常处理和重试机制
4. 当前环境网络问题可能导致测试失败，请在本地环境测试
