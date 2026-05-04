# StockExpert 本地数据存储设计

## 一、设计原则

1. **溯源**：每个字段记录来源（akshare / CDP / 涨停客 / 东财API / 新浪）
2. **可观测**：每条记录带 fetch_time / status / error_message
3. **自包含**：SQLite 单文件，晨报/午盘/收评共用同一库
4. **可查**：支持按日期 / 字段 / 数据源查询

---

## 二、数据库 Schema

### 表：trading_days

每个交易日一行，主键 `trade_date`。

```sql
CREATE TABLE trading_days (
    trade_date         TEXT PRIMARY KEY,  -- '2026-05-03'
    weekday            INTEGER,            -- 0=周一 ... 4=周五
    is_trading         INTEGER DEFAULT 1,  -- 1=交易日 0=假日
    created_at         TEXT DEFAULT (datetime('now', 'localtime')),
    updated_at         TEXT DEFAULT (datetime('now', 'localtime')),
    morning_done       INTEGER DEFAULT 0,  -- 晨报已采集
    midday_done        INTEGER DEFAULT 0,  -- 午盘已采集
    close_done         INTEGER DEFAULT 0   -- 收评已采集
);
```

### 表：index_quotes

4 大指数（上证 / 深证 / 创业板 / 科创50）每日 OHLCV。

```sql
CREATE TABLE index_quotes (
    trade_date         TEXT,
    index_code         TEXT,               -- '000001.SH' / '399001.SZ' / '399006.SZ' / '000688.SH'
    index_name         TEXT,               -- '上证指数' / '深证成指' / '创业板指' / '科创50'
    open               REAL,
    high               REAL,
    low                REAL,
    close              REAL,
    volume             INTEGER,            -- 股数
    amount             REAL,               -- 元
    change_pct         REAL,               -- 涨跌幅%
    source             TEXT,               -- 'akshare:stock_zh_index_spot_em'
    fetched_at         TEXT DEFAULT (datetime('now', 'localtime')),
    PRIMARY KEY (trade_date, index_code)
);
```

### 表：market_sentiment

全市场情绪（涨跌平家数 + 涨跌停家数）。

```sql
CREATE TABLE market_sentiment (
    trade_date         TEXT PRIMARY KEY,
    up_count           INTEGER,
    down_count         INTEGER,
    flat_count         INTEGER,
    limit_up_count     INTEGER,
    limit_down_count   INTEGER,
    total_stocks       INTEGER,            -- up+down+flat 总数
    up_ratio           REAL,               -- up_count / total_stocks
    source             TEXT,
    source_detail      TEXT,               -- 'CDP:dpzjlx.html:innerText' / 'akshare:stock_zt_pool_strong_em'
    fetched_at         TEXT DEFAULT (datetime('now', 'localtime'))
);
```

### 表：board_metrics

连板 + 炸板核心指标。

```sql
CREATE TABLE board_metrics (
    trade_date         TEXT PRIMARY KEY,
    highest_board      INTEGER,            -- 当日最高连板天数
    highest_board_stock TEXT,              -- 最高连板股票名
    break_board_rate   REAL,              -- 今炸板率 %
    break_board_count  INTEGER,            -- 炸板只数
    limit_up_count     INTEGER,            -- 涨停只数（冗余，同 market_sentiment）
    source             TEXT,               -- 'zhangtingke:vip_today_lbtd' / 'zhangtingke:zt_lbgd_line'
    fetched_at         TEXT DEFAULT (datetime('now', 'localtime'))
);
```

### 表：board_promotion

连板晋级率（昨1进2 / 2进3 / 3进4）。

```sql
CREATE TABLE board_promotion (
    trade_date         TEXT PRIMARY KEY,
    level_1_to_2       REAL,               -- 1进2晋级率 %
    level_2_to_3       REAL,               -- 2进3晋级率 %
    level_3_to_4       REAL,               -- 3进4晋级率 %
    level_1_to_2_cnt   INTEGER,            -- 昨1板总数
    level_2_to_3_cnt   INTEGER,
    level_3_to_4_cnt   INTEGER,
    source              TEXT,
    fetched_at          TEXT DEFAULT (datetime('now', 'localtime'))
);
```

### 表：north_flow

北向资金（实时 + 历史，历史仅CDP可补）。

```sql
CREATE TABLE north_flow (
    trade_date         TEXT PRIMARY KEY,
    north_net_inflow   REAL,               -- 北向净买额（元），负=净卖出
    hgt_net_inflow     REAL,               -- 沪股通净买额
    sgt_net_inflow     REAL,               -- 深股通净买额
    main_net_inflow    REAL,               -- 主力净流入（万元）
    super_large_net     REAL,               -- 超大单净流入
    large_net           REAL,               -- 大单净流入
    medium_net          REAL,               -- 中单净流入
    small_net           REAL,               -- 小单净流入
    source             TEXT,
    source_detail      TEXT,
    fetched_at         TEXT DEFAULT (datetime('now', 'localtime'))
);
```

### 表：field_fetch_log

**溯源核心表**：每个字段每次采集的详细日志。

```sql
CREATE TABLE field_fetch_log (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    trade_date         TEXT,
    stage              TEXT,               -- 'morning' / 'midday' / 'close'
    field_group        TEXT,               -- 'index_quotes' / 'market_sentiment' / 'board_metrics' / 'north_flow' / 'board_promotion'
    field_name         TEXT,
    source             TEXT,               -- 'akshare' / 'cdp' / 'zhangtingke' / 'eastmoney_api' / 'sina'
    source_detail      TEXT,               -- 'stock_zh_index_spot_em' / 'dpzjlx.html' / 'zt_lbgd_line'
    status             TEXT,               -- 'success' / 'failed' / 'partial' / 'stale'
    value              TEXT,               -- 采集到的值（JSON序列化）
    error_message      TEXT,
    fetched_at         TEXT DEFAULT (datetime('now', 'localtime')),
    UNIQUE(trade_date, stage, field_group, field_name)
);
```

---

## 三、数据源映射表

| 字段 | 主数据源 | 备数据源 | 备注 |
|------|---------|---------|------|
| index OHLCV | akshare `stock_zh_index_spot_em` | CDP 东财行情中心 | akshare 已覆盖 |
| up/down/flat_count | CDP 东财行情中心 innerText | 东财 push2 API | CDP 精度更高 |
| limit_up_count | akshare `stock_zt_pool_strong_em` | 东财 CDP 涨停池 | akshare 更稳定 |
| limit_down_count | akshare `stock_zt_pool_dtgc_em` | - | akshare 更稳定 |
| highest_board | 涨停客 `zt_lbgd_line` | CDP 东财涨停详情 | 涨停客直curl ✅ |
| break_board_rate | 涨停客 `vip_today_lbtd` | CDP 东财炸板率 | 涨停客直curl ✅ |
| 板晋级率 | 涨停客 `lbtd_yesterday_jinji` | - | 直curl ✅ |
| north_net_inflow（今） | CDP 东财 dpzjlx.html | akshare `stock_hsgt_fund_flow_summary_em` | CDP实时✅ / 历史🔴 |
| north_net_inflow（历史） | CDP 东财 dpzjlx.html（翻页） | **暂无** | 需CDP模拟翻页 |

---

## 四、溯源查询示例

```sql
-- 今日各字段采集状态（用户 dashboard 核心查询）
SELECT field_name, source, source_detail, status,
       CASE status WHEN 'success' THEN '✅' WHEN 'failed' THEN '🔴' WHEN 'partial' THEN '⚠️' ELSE '❓' END AS icon,
       fetched_at, error_message
FROM field_fetch_log
WHERE trade_date = '2026-05-03' AND stage = 'morning'
ORDER BY field_group, field_name;

-- 某字段历史成功率
SELECT field_name, source,
       COUNT(*) AS total,
       SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) AS success_cnt,
       ROUND(1.0*SUM(CASE WHEN status='success' THEN 1 ELSE 0 END)/COUNT(*)*100, 1) AS success_rate
FROM field_fetch_log
GROUP BY field_name, source
ORDER BY field_name;

-- 某日市场情绪完整数据
SELECT * FROM market_sentiment WHERE trade_date = '2026-05-03';
SELECT * FROM board_metrics WHERE trade_date = '2026-05-03';
SELECT * FROM north_flow WHERE trade_date = '2026-05-03';
```

---

## 五、实现文件结构

```
docs/superpowers/specs/
  2026-05-03-trading-system-07-data-storage.md   ← 本文档

data/
  stockexpert.db                                   ← SQLite 数据库文件

src/
  data/
    db_schema.py                                   ← 建表脚本
    db_writer.py                                   ← 写入每日数据
    db_reader.py                                   ← 查询接口（溯源 dashboard）
    fetchers/
      akshare_fetcher.py                          ← akshare 数据采集
      cdp_fetcher.py                              ← CDP 数据采集
      zhangtingke_fetcher.py                      ← 涨停客直采集
      eastmoney_fetcher.py                         ← 东财 API 直采集
```

---

## 六、字段完整性检查视图

```sql
CREATE VIEW v_field_coverage AS
SELECT
    trade_date,
    stage,
    COUNT(*) AS total_fields,
    SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) AS success_cnt,
    ROUND(1.0*SUM(CASE WHEN status='success' THEN 1 ELSE 0 END)/COUNT(*)*100, 1) AS coverage_pct,
    GROUP_CONCAT(CASE WHEN status != 'success' THEN field_name || ':' || status ELSE NULL END) AS failed_fields
FROM field_fetch_log
WHERE trade_date IS NOT NULL
GROUP BY trade_date, stage
ORDER BY trade_date DESC, stage;
```

---

## 七、优先级

1. **第一期**：实现 `db_schema.py` + `db_writer.py`，写入今日所有 13 字段 + 溯源日志
2. **第二期**：实现 `db_reader.py`，溯源 dashboard 查询
3. **第三期**：集成进 hermes_stock scheduler，早/午/晚三次自动写入
