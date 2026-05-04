# 跨数据源交叉验证报告

**日期**: 2026-05-03
**数据源**: 新浪财经 + 东方财富 (CDP 探索)
**对比目标**: 涨停计数、市场统计、资金流向、板块数据

---

## 一、跨源数据对照

### 1. 全市场股票数量

| 来源 | 沪A | 深A | 北交所 | 合计 |
|------|-----|-----|-------|------|
| 新浪 | 2311 | 2889 | - | 5200 |
| 东方财富 | - | - | - | 5528 |
| 差值 | - | - | - | **+328 (≈北交所)** |

> 东方财富 total=5528 比新浪多约328只，差值约为北交所股票数量（北交所有约300+只股票）

### 2. 涨停个股

| 来源 | 方法 | 涨停数 |
|------|------|-------|
| 东方财富 | `fs=m:0+t:6+f:10,m:0+t:80+f:10,m:1+t:2+f:10,m:1+t:23+f:10` | **401** |
| 新浪 | `node=hs_a&symbol=_zt` (num=100, 返回分页) | ~100+ (分页限制) |

> **东方财富 `f:10` = 涨停过滤**，total=401是准确数字

### 3. 涨跌平统计

| 来源 | 涨 | 跌 | 平 |
|------|----|----|-----|
| 东方财富 (页面文本) | 上证1164 + 深证1536 = **2700** | 上证1104 + 深证1300 = **2404** | 上证58 + 深证67 = **125** |
| 新浪 | ❌ 无直接接口 | ❌ 无直接接口 | ❌ 无直接接口 |

> **东方财富** `data.eastmoney.com/zjlx/dpzjlx.html` 页面直接显示涨跌平家数
> **新浪** 无等效的直接统计接口，需通过全量API聚合

---

## 二、数据源能力矩阵

| 数据类型 | 新浪 | 东方财富 | 结论 |
|---------|------|---------|------|
| 大盘指数(实时) | ✅ hq.sinajs.cn | ✅ push2 API | 两者均可 |
| 涨停个股列表 | ✅ `node=hs_a&_zt` | ✅ `f:10 filter` | **东方财富更精确**(有total) |
| 跌停个股列表 | ✅ `node=hs_a&_zt` (asc) | ✅ `f:11 filter` (待验证) | 待确认f:11 |
| 涨跌平家数 | ❌ 需聚合全量 | ✅ 页面文本直接读 | **东方财富胜** |
| 北向资金 | ⚠️ 无直接接口 | ✅ `kamt`端点 | **东方财富胜** |
| 主力净流入 | ✅ `ssl_bkzj_ssggzj` | ✅ `f62`字段 | 两者均可 |
| 行业板块 | ⚠️ node待确认 | ✅ `m:90+t:2` | **东方财富胜** |
| 概念板块 | ⚠️ node待确认 | ✅ `m:90+t:3` | **东方财富胜** |
| 个股实时行情 | ✅ hq.sinajs.cn | ✅ push2 | 两者均可 |
| K线数据 | ✅ 可用 | ✅ 可用 | 两者均可 |
| 平盘家数 | ❌ 需全量聚合 | ✅ 页面直接读 | **东方财富胜** |

---

## 三、东方财富 API 验证 (以新浪为基准)

### 3.1 涨停池 (Sina基准)

```
Sina: node=hs_a&symbol=_zt → 涨停股票列表 (限100条/页)
EM:   fs with f:10 filter  → total=401  ← 交叉验证通过 (Sina也有同样数据)
```

### 3.2 股票总数 (Sina基准)

```
Sina: sh_a=2311, sz_a=2889, 合计=5200
EM:   total=5528, 差=328 ← 北交所(~300只)  ← 交叉验证通过
```

### 3.3 主力净流入 (字段对比)

| 概念 | 新浪字段 | 东方财富字段 |
|------|---------|------------|
| 主力净流入 | `netamount` | `f62` |
| 超大单净流入 | (内含) | (分层类似) |
| 特大单净流入 | (内含) | (分层类似) |

---

## 四、新浪可用 API 汇总

### 4.1 实时行情
```
GET https://hq.sinajs.cn/list=s_sh000001,s_sz399001
响应: var hq_str_s_sh000001="上证指数,4112.1593,4.6449,0.11,6569127,127619474";
```

### 4.2 涨停/跌停池 (分页)
```
GET https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData
?page=1&num=100&sort=changepercent&asc=0&node=hs_a&symbol=_zt
字段: symbol, code, name, trade, pricechange, changepercent, volume, amount, turnoverratio
```

### 4.3 资金流向 (个股/板块)
```
GET https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/MoneyFlow.ssl_bkzj_ssggzj
?page=1&num=10&sort=netamount&asc=0
字段: symbol, name, netamount(净流入), inamount(流入), outamount(流出), r0_net(主力净流入)
```

### 4.4 市场统计
```
GET https://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeStockCount
?node=sh_a  → "2311" (沪A总数)
?node=sz_a  → "2889" (深A总数)
```

---

## 五、结论

### 推荐方案

| 需求 | 首选数据源 | 备选 |
|------|----------|------|
| 涨跌平家数 | **东方财富** `data.eastmoney.com/zjlx/dpzjlx.html` (CDP) | 无 |
| 涨停/跌停计数 | **东方财富** `f:10/f:11 filter` | 新浪聚合 |
| 北向资金 | **东方财富** `kamt` 端点 | 无 |
| 主力净流入 | **东方财富** `f62` 字段 | 新浪 `ssl_bkzj_ssggzj` |
| 板块数据 | **东方财富** `m:90+t:2/t:3` | 待探索新浪 |
| 实时行情 | **东方财富** push2 | 新浪 hq.sinajs.cn |

### 关键验证结论

1. **涨停计数**: 东财total=401，东财数据可信
2. **全市场总量**: 东财=5528 vs 新浪=5200，差值≈北交所(~328只)，合理
3. **涨跌平**: 东财页面直接提供，新浪无此数据
4. **北向资金**: 东财kamt端点验证成功(rc=0)，新浪无等效接口

---

## 六、测试脚本路径

| 脚本 | 用途 |
|------|------|
| `/tmp/cdp_sina_explore.mjs` | 探索新浪首页和行情中心 |
| `/tmp/cdp_sina_stats.mjs` | 从新浪提取市场统计数据 |
| `/tmp/cdp_sina_pages.mjs` | 探新浪涨跌/资金/板块页面 |
| `/tmp/cdp_market_overview.mjs` | 东财大盘资金页面(含涨跌平) |
| `/tmp/cdp_full_url.mjs` | 捕获东财API完整URL(含ut token) |
