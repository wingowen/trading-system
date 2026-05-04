# 主流财经网站数据覆盖度检测报告

**日期**: 2026-05-03
**方法**: CDP 浏览器自动化 + curl HTTP 探测
**数据源**: 东方财富、新浪、同花顺、凤凰财经、网易财经、雪球、大智慧、和讯网、华尔街见闻、财联社、中金在线

---

## 一、数据源可用性总览

| 数据源 | 状态 | 行情数据 | 新闻/资讯 | 备注 |
|--------|------|---------|----------|------|
| 东方财富 | ✅ 可用 | ✅ 全面 | ✅ | 主力数据源，ut token 需 CDP 拦截 |
| 新浪财经 | ✅ 可用 | ✅ 较全 | ✅ | 股票数量/涨停池可用 curl 直连 |
| 同花顺 | ⚠️ 限制 | ❌ 需登录 | ✅ | API 为内部爬虫系统(cbasspider) |
| 凤凰财经 | ❌ 新闻 | ❌ 无行情 | ✅ | shankapi.ifeng.com 有 24h 财经数据 |
| 网易财经 | ❌ 新闻 | ❌ 无行情 | ✅ | 纯新闻聚合，无行情 API |
| 雪球 | ⚠️ 严格限制 | ⚠️ 需认证 | ⚠️ 需登录 | Cloudflare + IP 黑名单，部分 API 需 Cookie |
| 大智慧 | ❌ 无 | ❌ 无 | ❌ | 官网产品展示，无公开数据 API |
| 和讯网 | ✅ 有限 | ⚠️ 黄金/期货 | ✅ | homeway.com.cn API，股票数据少 |
| 华尔街见闻 | ⚠️ 需认证 | ⚠️ 需登录 | ✅ | robots.txt 允许 AI 爬虫，API 需要身份 |
| 财联社 | ❌ WAF拦截 | ❌ 无 | ✅ | CloudWAF 保护，curl 被拦截 |
| 中金在线 | ❌ 跳转 | ❌ 无 | ❌ | 全部 302 重定向，无公开数据 API |

---

## 二、各数据源详细分析

### 2.1 东方财富 (eastmoney.com) — ⭐ 主数据源

**CDP 探索结果:**

| 数据类型 | API 端点 | 认证 | rc | 数据质量 |
|---------|---------|------|-----|---------|
| 涨停池 | `push2.eastmoney.com/api/qt/clist/get?fs=m:0+t:6+f:10,...` | ut token | 0 | **total=401** |
| 跌停池 | 同接口 f:11 | ut token | 0 | total=61 |
| 北向资金 | `push2.eastmoney.com/api/qt/kamt/get` | ut token | 0 | ✅ 沪股通+深股通+北上净流入 |
| 涨跌平统计 | `data.eastmoney.com/zjlx/dpzjlx.html` | 无 | N/A | 页面文本：上证1164涨/58平/1104跌；深证1536涨/67平/1300跌 |
| 主力净流入 | f62 字段 | ut token | 0 | ✅ 超大单+大单 |
| 行业板块 | `push2.eastmoney.com/api/qt/clist/get?fs=m:90+t:2` | ut token | 0 | ✅ |
| 概念板块 | `push2.eastmoney.com/api/qt/clist/get?fs=m:90+t:3` | ut token | 0 | ✅ |
| 全A股票总数 | 同涨停池接口 total | ut token | 0 | **5528** |

**`ut` token 获取方案:** `Fetch.takePausedRequest` + `Fetch.continueRequest`（CDP 拦截）
固定值: `fa5fd1943c7b386f172d6893dbfba10b`

---

### 2.2 新浪财经 (sina.com.cn) — ⭐ 重要备选

**curl 直连验证可用:**

| 数据类型 | API 端点 | 认证 | 验证结果 |
|---------|---------|------|---------|
| 沪A股票总数 | `Market_Center.getHQNodeStockCount?node=sh_a` | 无 | **2311** ✅ |
| 深A股票总数 | `Market_Center.getHQNodeStockCount?node=sz_a` | 无 | **2889** ✅ |
| 涨停池 | `Market_Center.getHQNodeData?node=hs_a&symbol=_zt&num=100` | 无 | ✅ 返回100条含 symbol/name/trade/changepercent |
| 跌停池 | `Market_Center.getHQNodeData?node=hs_a&asc=1&symbol=_zt` | 无 | ✅ asc 升序前几条即跌停 |
| 个股资金流向 | `MoneyFlow.ssl_bkzj_ssggzj` | 无 | ✅ 主力净流入/流入/流出/特大单净流入 |
| 指数行情 | `hq.sinajs.cn/list=s_sh000001,s_sz399001` | 无 | ✅ var hq_str 格式，含现价/涨跌幅/成交量 |
| 北向资金 | ❌ 无等效接口 | — | — |
| 涨跌平统计 | ❌ 需全量聚合 | — | — |

**与东财交叉验证:**
- 东财全A: 5528 vs 新浪: 5200 → 差 328 ≈ 北交所
- 涨停数: 东财 401 远大于新浪单页 100（新浪分页限制）

---

### 2.3 同花顺 (10jqka.com.cn)

**CDP 探索结果:**
- 页面含丰富实时行情：上证、深证、创业板、科创板指数实时成交额
- 概念板块（CPO/PCB/算力租赁/商业航天/小金属等）
- **关键发现**: 所有拦截到的 API 均来自 `cbasspider.10jqka.com.cn:8443`：
  - `/spider/api/v1/access_token` — 内部爬虫认证
  - `/spider/api/v1/report/track_config` — 配置
  - `/spider/api/v1/report/track_info` — 埋点数据
- **结论**: 同花顺数据系统为内部使用，无公开 API

---

### 2.4 凤凰财经 (finance.ifeng.com)

**CDP 探索结果:**
- 主要是新闻内容（巴菲特股东大会、DeepSeek、五一票房等热点）
- 拦截到的 API:
  - `shankapi.ifeng.com/api/finance/studio/24h/latest/` — 24h 财经快讯 ✅
  - `c01049em.ifeng.com/get.php` — 评论数据
  - `err.ifengcloud.ifeng.com/v1/api/hb|perf` — 性能监控
- **结论**: 无行情数据，纯新闻媒体

---

### 2.5 网易财经 (money.163.com)

**CDP 探索结果:**
- 大量新闻内容（巴菲特股东大会、美联储、芯片等）
- 拦截到的 API:
  - `gw.m.163.com/commons-user-main/api/v1/commons/user/pc/getUserByCookie` — 用户认证
  - `revive.outin.cn` — 广告投放
- **结论**: 纯新闻媒体，无行情 API

---

### 2.6 雪球 (xueqiu.com)

**curl 探测结果（IP 被黑名单，403）:**

| 端点 | 状态 | 说明 |
|------|------|------|
| robots.txt | 403 | IP 被雪球黑名单拦截 |
| `/v5/stock/realtime/quotec.json` | 200 空 body | 需 Cookie 才能取数据 |
| `/service/v5/stock/screener/quote/list` | 200 ✅ | **无需认证可用**，返回选股器行情数据 |
| `/service/v5/stock/capital/flow` | 200 ✅（items 为空） | 资金流向，数据受限 |
| `/v4/statuses/public_timeline_by_category.json` | 400 | 需认证 |

**结论**: Cloudflare 保护严格，大部分接口需要有效 Cookie/Session。`/service/v5/stock/screener/quote/list` 是唯一已知无需认证的可用接口（需股票代码过滤）。

---

### 2.7 大智慧 (gw.com.cn)

**CDP 探索结果:**
- 官网为产品介绍（PC/手机版/VIP服务）
- 唯一拦截到的数据 API: `https://mnews.dzh.com.cn/wap/data/officialAdv/gw.json`
- **结论**: 无公开行情数据，是行情软件而非数据源

---

### 2.8 和讯网 (hexun.com)

**CDP 探索结果:**

| API 端点 | 数据类型 | 可用性 |
|---------|---------|--------|
| `gw.homeway.com.cn/lhjx/api/choice/goldStock/list` | 黄金股票列表 | ✅ |
| `gw.homeway.com.cn/zhibo/api/search/important_points_cd` | 直播重点摘要 | ✅ |
| `nwapi.hexun.com/api/operation/position/webDetail` | 运营位数据 | ✅ |
| `m.hexun.com/api/checkNewsWhiteList` | 新闻白名单 | ✅ |

**结论**: 和讯有少量数据 API，但以财经新闻和黄金/期货为主，A股行情数据有限。

---

### 2.9 华尔街见闻 (wallstreetcn.com)

**curl 探测结果:**
- `robots.txt`: 全站允许 AI 爬虫(GPTBot/ClaudeBot/PerrplexityBot 等)
- `sitemap.xml`: 发现 `news/live/markets/calendar/vip/master/articles` 等子站
- **关键**: 所有 `api.wallstreetcn.com` 端点返回 `{"code":71404,"message":"Not Found"}`
- `quotes.wallstreetcn.com` → 行情报价，需要身份认证

**结论**: 数据 API 需要认证，普通爬虫无法直接获取

---

### 2.10 财联社 (cls.cn)

**curl 探测结果:**
- `robots.txt`: Disallow:/（禁止所有爬虫）
- `sitemap.xml`: CloudWAF 拦截，返回拦截页面
- API 请求: 全部返回 SPA HTML（非 JSON）
- **结论**: CloudWAF 保护，无法直接爬取

---

### 2.11 中金在线 (cnfol.com)

**curl 探测结果:**
- 所有路径返回 HTTP 302 → nginx 重定向
- robots.txt: 302 跳转
- API 路径: 全部 302
- **结论**: 无法直接访问，无公开数据 API

---

## 三、最终数据源推荐

```
优先级梯队:

┌─────────────────────────────────────────────────────┐
│ 第一梯队 (无认证/curl 直连)                          │
│  东方财富: 涨停/跌停/北向/涨跌平/板块 全覆盖        │
│  新  浪:  股票数量/涨停池/资金流向/指数 直连可用    │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 第二梯队 (CDP 拦截认证 / 限制)                       │
│  雪  球:  /service/v5/stock/screener/quote/list     │
│  和讯网:  黄金/期货/直播数据 (CDP 可探)            │
│  凤凰:    24h 财经快讯 (shankapi.ifeng.com)         │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│ 不可用 (需登录/WAF/无 API)                          │
│  同花顺:  内部爬虫系统，无公开 API                   │
│  大智慧:  产品官网，无行情 API                       │
│  网易:    纯新闻，无行情                            │
│  华尔街见闻: API 需认证                             │
│  财联社:  CloudWAF 拦截                             │
│  中金在线:  全部 302 重定向                         │
└─────────────────────────────────────────────────────┘
```

---

## 四、与 akshare 缺口的对应关系

| 数据缺口 | 东财方案 | 新浪方案 | 其他可用 |
|---------|---------|---------|---------|
| `limit_up_count` 涨停家数 | ✅ f:10 total=401 | ✅ 聚合 symbol=_zt | 无 |
| `limit_down_count` 跌停家数 | ✅ f:11 total=61 | ✅ asc 升序前几条 | 无 |
| `north_net_inflow` 北向资金 | ✅ kamt 端点 | ❌ 无等效 | 无 |
| `up_count/down_count/flat_count` | ✅ 东财页面文本 | ❌ 需聚合全量 | 无 |
| `highest_board` 连板高度 | ⚠️ 待探 f:10+时间序列 | ⚠️ 待探 | 无 |
| 主力净流入 | ✅ f62 | ✅ ssl_bkzj_ssggzj | 无 |
| 行业/概念板块 | ✅ m:90+t:2/t:3 | ⚠️ 待探 node | 无 |
| 全市场股票数 | ✅ total=5528 | ✅ 2311+2889 | 无 |

---

## 五、测试文件清单

| 文件 | 用途 |
|------|------|
| `/tmp/cdp_result_tonghuashun.json` | 同花顺 CDP 探索 |
| `/tmp/cdp_result_fenghuang.json` | 凤凰财经 CDP 探索 |
| `/tmp/cdp_result_wangyi.json` | 网易财经 CDP 探索 |
| `/tmp/cdp_result_dazhihui.json` | 大智慧 CDP 探索 |
| `/tmp/cdp_result_hexun.json` | 和讯网 CDP 探索 |
| `/tmp/curl_probe_xueqiu.json` | 雪球 curl 探测 |
| `/tmp/curl_probe_wallstreet.json` | 华尔街见闻 curl 探测 |
| `test/cdp/2026-05-03-eastmoney-coverage-report.md` | 东方财富单独报告 |
| `test/cdp/2026-05-03-cross-source-validation.md` | 东财 vs 新浪交叉验证 |
