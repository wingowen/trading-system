# 东方财富 CDP 探索覆盖度报告

**日期**: 2026-05-03
**方法**: CDP (Chrome DevTools Protocol) + curl 验证
**Chrome 调试端口**: 127.0.0.1:9222

---

## 概览

| 数据类型 | Tushare 已有 | EastMoney API 发现 | 缺口 |
|---------|-------------|------------------|------|
| 大盘指数 | ✅ 完整 | ✅ 验证 | - |
| 市场情绪(涨跌平) | ❌ | ✅ | limit_up/down count 需进一步处理 |
| 行业板块 | ✅ 基础字段 | ✅ 完整(含主力净流入) | - |
| 概念板块 | ✅ 基础字段 | ✅ 完整 | - |
| 涨停个股 | ❌ | ✅ f:10 filter | 板块级涨停计数需聚合 |
| 跌停个股 | ❌ | ✅ f:11 filter | 数字待验证 |
| 北向资金 | ✅ | ✅ kamt端点 | - |
| 主力净流入 | ✅ | ✅ f62字段 | - |

---

## API 端点汇总

### 1. 行业板块
```
GET https://push2.eastmoney.com/api/qt/clist/get
fs=m:90+t:2
fields=f12,f13,f14,f1,f2,f4,f3,f152,f62
rc=0, total=496
```

### 2. 概念板块
```
GET https://push2.eastmoney.com/api/qt/clist/get
fs=m:90+t:3
fields=f12,f13,f14,f1,f2,f4,f3,f152,f62
rc=0, total=486
```

### 3. 涨停个股
```
GET https://push2.eastmoney.com/api/qt/clist/get
fs=m:0+t:6+f:10,m:0+t:80+f:10,m:1+t:2+f:10,m:1+t:23+f:10
# f:10 = 涨停过滤
total=401只
```

### 4. 跌停个股
```
GET https://push2.eastmoney.com/api/qt/clist/get
fs=m:0+t:6+f:11,m:0+t:80+f:11,m:1+t:2+f:11,m:1+t:23+f:11
# f:11 = 跌停过滤
# 注意: 数字待验证(当前total=5287异常)
```

### 5. 沪深港通北向资金
```
GET https://push2.eastmoney.com/api/qt/kamt/get
fields1=f1,f2,f3,f4
fields2=f62,f63,f64,f65,f66
rc=0

响应:
- hk2sh: 沪深股通净流入
- sh2hk: 沪股通净流入
- hk2sz: 深股通净流入
```

### 6. 大盘资金流向 + 涨跌平统计
```
URL: https://data.eastmoney.com/zjlx/dpzjlx.html
状态: ✅ 页面存活

页面直接显示:
- 上证: 涨:1164 平:58 跌:1104
- 深证: 涨:1536 平:67 跌:1300
- 主力净流入/超大单净流入/大单净流入/中单净流入/小单净流入

底层API: /api/qt/stock/fflow/daykline/get
```

---

## 字段映射 (EastMoney f-fields)

| 字段 | 含义 |
|------|------|
| f12 | 股票代码(6位数字) |
| f13 | 市场ID (0=深圳, 1=上海) |
| f14 | 股票/板块名称 |
| f3 | 涨跌幅 (*100, 即百分比×100) |
| f4 | 振幅 (*100) |
| f62 | 主力净流入 (元) |
| f128 | 股票名称 (涨停池场景) |
| f140 | 股票代码(6位, 涨停池场景) |
| f141 | 市场ID (0=深, 1=沪, 涨停池场景) |
| f152 | 成交量 (手) |
| f184 | 成交额 (元) |

---

## 数据缺口与解决方案

### 🔴 高优先级

**1. limit_up_count (板块级)**
- 问题: 板块API (m:90+t:2) 没有涨停家数字段
- 方案: 用 `m:90+s:4` (涨停板块候选池) + 交叉比对
- 替代: 从涨停个股API (f:10) 筛选出属于该板块的个股数

**2. highest_board (连板高度)**
- 问题: 需要时间序列数据
- 方案: 拉取涨停个股历史K线，统计连续涨停次数

### 🟡 中优先级

**3. limit_down_count**
- 问题: f:11 filter 返回数字异常
- 方案: CDP访问 data.eastmoney.com 页面提取，或换用其他API

**4. volume_ratio (量比)**
- 问题: tushare无，akshare有
- 方案: EastMoney字段探索，或继续用akshare

**5. is_st / is_new**
- 方案: 从名称含"ST"判断；上市日期<6个月判断

---

## 活页面清单

| 页面 | URL | 状态 |
|------|-----|------|
| 行情中心 | https://quote.eastmoney.com/center/ | ✅ |
| 行业板块 | https://quote.eastmoney.com/center/ (SPA tab) | ✅ |
| 概念板块 | https://quote.eastmoney.com/center/ (SPA tab) | ✅ |
| 大盘资金流向 | https://data.eastmoney.com/zjlx/dpzjlx.html | ✅ |
| 沪深资金流向 | https://data.eastmoney.com/zjlx/dpzjlx.html | ✅ |
| 涨停板行情 | https://quote.eastmoney.com/center/gridlist.html#hs_a_board | ✅ |

## 死页面清单 (404)

| 旧URL | 原因 |
|-------|------|
| data.eastmoney.com/zt/ | 东方财富改版 |
| quote.eastmoney.com/zt/ztb.html | 东方财富改版 |
| quote.eastmoney.com/zt/ | 东方财富改版 |

---

## CDP 技术要点

1. **SPA 路由**: hash 路由 (`#hs_a_board`) 不会触发 `Page.navigate`，需用 JS click 交互
2. **ut token**: API 需携带 `ut=fa5fd1943c7b386f172d6893dbfba10b` 参数，否则 rc=102
3. **WebSocket 复用**: 同一个 CDP Tab 可持续使用，不用每次新建连接
4. **Fetch interception**: 用 `Fetch.enable` + `Fetch.requestPaused` 捕获完整 URL (含 ut 参数)

---

## 测试脚本

| 脚本 | 用途 |
|------|------|
| /tmp/cdp_homepage.mjs | 探索东方财富首页链接 |
| /tmp/cdp_explore2.mjs | 验证多个页面是否存活 |
| /tmp/cdp_full_url.mjs | 捕获完整API URL (含ut token) |
| /tmp/cdp_market_overview.mjs | 加载大盘资金流向页面并提取文本 |
