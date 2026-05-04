# CDP 数据补齐测试记录

**日期**: 2026-05-03  
**目标**: 用 CDP 爬取全市场情绪数据（涨停计数、跌停计数、涨跌平家数、北向资金）  
**结论**: CDP 浏览器方案不通，改用直接 API 调用

---

## 一、CDP 环境搭建（WSL → Windows Chrome）

### 问题
Chrome 跑在 Windows 上，WSL 无法访问 `DevToolsActivePort` 文件（Windows 专用路径），导致 `cdp.mjs` 报 `No DevToolsActivePort found`。

### 解决：直接用 HTTP JSON API 拿 WebSocket URL

```powershell
# Windows 侧启动 Chrome
Start-Process 'C:\Program Files\Google\Chrome\Application\chrome.exe' `
  -ArgumentList '--remote-debugging-port=9222','--user-data-dir=C:\tmp\chrome-debug' `
  -WindowStyle Hidden
```

```bash
# WSL 侧获取 WebSocket URL
curl -s http://127.0.0.1:9222/json/version
# → {"webSocketDebuggerUrl": "ws://127.0.0.1:9222/devtools/browser/..."}

# 直接用 WebSocket URL 连接（Node 22 内置 WebSocket）
```

### 正确结论
`--remote-debugging-port` 启动时 Chrome **不写** `DevToolsActivePort` 文件，只有从 `chrome://inspect` 点击才写。用 HTTP API 绕过这个问题。

---

## 二、东方财富 URL 探索

### 问题
CDP 导航到东方财富涨停页面后，页面内容是 404 Not Found 页面（标题："抱歉，您访问的页面不存在或已删除"）。

### 诊断过程

```
curl -I https://data.eastmoney.com/zt/
HTTP/1.1 404 Not Found   ← 服务器直接返回，不是 JS 跳转

CDP 导航后 document.title 也显示 404 页面
最终 URL 被重定向到 www.eastmoney.com
```

### 尝试过的 URL（全部 404）

| URL | HTTP 状态 |
|-----|---------|
| `https://data.eastmoney.com/zt/` | 404 |
| `https://data.eastmoney.com/ztb` | 404 |
| `https://data.eastmoney.com/ztb.html` | 404 |
| `https://data.eastmoney.com/zdt` | 404 |
| `https://quote.eastmoney.com/zt/ztb.html` | 404 |
| `https://quote.eastmoney.com/zt3.html` | 404 |

### 首页可用链接

```
东方财富首页 → "昨日涨停" → so.eastmoney.com/web/s?keyword=昨日涨停
```

说明：旧版涨停/跌停专用页面已下线，新版需要走搜索/选股入口。

---

## 三、结论

| 数据缺口 | CDP 可行性 | 推荐方案 |
|---------|-----------|---------|
| 涨停家数 `limit_up_count` | ❌ URL 404，需找新入口 | API：`push2.eastmoney.com`（见下） |
| 跌停家数 `limit_down_count` | ❌ 同上 | 同上 |
| 涨跌平家数 | ❌ 同上 | 同上 |
| 北向资金 `north_net_inflow` | 待探索 | API 方案更稳定 |
| 连板高度 `highest_board` | ⚠️ 需进板块详情页 | CDP 可行，但需要找对入口 |

---

## 四、替代方案：东方财富 API 直接调用

### 成功案例

**全部 A 股列表（含涨幅）**:
```
https://push2.eastmoney.com/api/qt/clist/get?fs=m:0+t:6,m:90+t:3&fields=f12,f14,f3,f6
```
- `f3=10.12` → 涨停股（涨幅接近 10%）
- `total: 2123` → 全部股票总数
- 无需浏览器，纯 HTTP，速度快

**板块数据**:
```
https://push2.eastmoney.com/api/qt/clist/get?pn=1&pz=5&po=1&np=1&fid=f3&fs=m:90+t:3&fields=f12,f14,f3,f6,f7,f8,f10,f15,f16,f17,f18
```

---

## 五、下一步

1. 找到涨停/跌停池的 API 接口（`f3=10` 的过滤器）
2. 找到市场整体涨跌平家数的 API
3. 找到北向资金 API
4. CDP 方案保留用于：条件选股页面（需交互）的结果抓取
