# Phase 1 实现计划：交易日志后端 API

> **For Hermes:** 按 Task 顺序执行，每个 Task 包含 TDD 完整循环。

**目标：** 创建 `src/data/api_trades.py`，提供交易日志 CRUD API，支持入场录入、平仓、列表查询、汇总统计。

**架构：** Flask Blueprints，复用 `app.py` 的 `require_api_key` 装饰器，`trade_journal.py` 提供底层数据操作。

---

## 前置检查

**1. 查看 trade_journal.py 现有方法**

文件已读（143行），`TradeJournal` 类已有：
- `record_entry(trade_data)` — 写入入场记录
- `record_exit(trade_data)` — 写入出场记录
- `get_trade(trade_id)` — 查询单笔
- `get_all_trades()` — 查询全部
- `_ensure_schema()` — 建表

**缺失：**
- 无 `status` 字段维护
- 无分页/过滤查询
- 无汇总统计方法
- 无 `update_exit`（平仓时更新 entry 记录的状态）

**2. ALTER TABLE trade_journal**

数据库路径：`/mnt/c/Users/WINGO/Documents/WorkSpace/trading-system/data/stockexpert.db`

```sql
ALTER TABLE trade_journal ADD COLUMN status TEXT DEFAULT 'holding';
```

---

## Task 1: ALTER TABLE 添加 status 字段

**Files:**
- Modify: `src/data/evolution/trade_journal.py`

**Step 1: 写 ALTER TABLE**

在 `_ensure_schema()` 方法末尾追加（CREATE TABLE IF NOT EXISTS 之后追加字段）：

```python
# 确保 status 字段存在（ALTER TABLE for existing dbs）
try:
    conn.execute("ALTER TABLE trade_journal ADD COLUMN status TEXT DEFAULT 'holding'")
except Exception:
    pass  # 字段已存在
```

**Step 2: 验证**

```bash
cd /mnt/c/Users/WINGO/Documents/WorkSpace/trading-system
python3 -c "
from src.data.evolution.trade_journal import TradeJournal
j = TradeJournal()
print('TradeJournal init OK')
print(j._ensure_schema() or 'schema OK')
"
```

预期：输出 "TradeJournal init OK" 和 "schema OK"，无报错。

**Step 3: Commit**

```bash
git add src/data/evolution/trade_journal.py
git commit -m "feat(trades): add status column to trade_journal table"
```

---

## Task 2: 扩展 TradeJournal 类

**Files:**
- Modify: `src/data/evolution/trade_journal.py`

**Step 1: 添加 query_trades 方法**

在 `get_all_trades()` 之后追加：

```python
def query_trades(
    self,
    status: str = None,        # 'holding' / 'exited' / None (all)
    start_date: str = None,
    end_date: str = None,
    sector: str = None,
    pattern: str = None,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """分页查询交易记录（仅查 entry 记录，按日期降序）"""
    conn = _conn()
    conditions = ["action = 'entry'"]
    params: list = []

    if status == 'holding':
        conditions.append("status = 'holding'")
    elif status == 'exited':
        conditions.append("status = 'exited'")
    # status == None / 'all' : 不加 status 条件

    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)
    if sector:
        conditions.append("sector = ?")
        params.append(sector)
    if pattern:
        conditions.append("pattern = ?")
        params.append(pattern)

    where = " AND ".join(conditions)

    # 总数
    total = conn.execute(
        f"SELECT COUNT(*) as cnt FROM trade_journal WHERE {where}", params
    ).fetchone()["cnt"]

    # 分页
    offset = (page - 1) * page_size
    rows = conn.execute(
        f"""
        SELECT * FROM trade_journal
        WHERE {where}
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """,
        params + [page_size, offset],
    ).fetchall()
    conn.close()

    return {
        "trades": [dict(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
```

**Step 2: 添加 get_summary 方法**

在 `query_trades` 之后追加：

```python
def get_summary(self) -> Dict[str, Any]:
    """交易汇总统计"""
    conn = _conn()
    row = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status='holding' THEN 1 ELSE 0 END) as holding,
            SUM(CASE WHEN status='exited' AND pnl_percent > 0 THEN 1 ELSE 0 END) as win_count,
            SUM(CASE WHEN status='exited' AND pnl_percent < 0 THEN 1 ELSE 0 END) as loss_count
        FROM trade_journal
        WHERE action = 'entry'
    """).fetchone()
    conn.close()

    total = row["total"] or 0
    holding = row["holding"] or 0
    closed = total - holding
    wins = row["win_count"] or 0
    losses = row["loss_count"] or 0
    win_rate = round(wins / closed, 3) if closed > 0 else 0.0

    return {
        "total": total,
        "holding": holding,
        "closed": closed,
        "win_count": wins,
        "loss_count": losses,
        "win_rate": win_rate,
    }
```

**Step 3: 修改 record_entry 添加 status**

找到 `record_entry` 方法中的 INSERT 语句，将 `'entry'` 之后加入 `status`:

INSERT 语句改为：
```python
conn.execute("""
    INSERT OR REPLACE INTO trade_journal
        (trade_id, action, status, code, name, price, date,
         pattern, sector, market_env_score, sector_score,
         stop_loss, take_profit, position_size, created_at, updated_at)
    VALUES ('entry', 'holding', ?, ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))
""", (
    trade_id,
    trade_data.get("code", ""),
    # ... 补全其余参数
))
```

**更简单的方式**：在 `values` 列表中把 `'entry'` 拆出来，`status` 单独加。

注意：INSERT OR REPLACE 会触发 DELETE 再 INSERT，字段顺序必须和 VALUES 完全对应。

**Step 4: 修改 record_exit 更新 status**

在 `record_exit` INSERT 之后，新增 UPDATE 更新 status：

```python
# 出场记录写入后，同步更新入场记录的 status 为 exited
conn.execute(
    "UPDATE trade_journal SET status='exited', updated_at=datetime('now', 'localtime') WHERE trade_id=? AND action='entry'",
    (trade_id,)
)
```

**Step 5: 语法验证**

```bash
python3 -m py_compile src/data/evolution/trade_journal.py && echo "OK"
```

**Step 6: Commit**

```bash
git add src/data/evolution/trade_journal.py
git commit -m "feat(trades): extend TradeJournal with query_trades, get_summary, status management"
```

---

## Task 3: 创建 api_trades.py

**Files:**
- Create: `src/data/api_trades.py`

**Step 1: 创建文件**

```python
"""
交易日志 API
路由: GET/POST /api/trades, GET/PUT /api/trades/<trade_id>, GET /api/trades/summary
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Blueprint, request, jsonify
from functools import wraps
from src.data.evolution.trade_journal import TradeJournal

# 复用 app.py 的 require_api_key 逻辑
_api_key = os.environ.get("FLASK_API_KEY", "")

def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if _api_key:
            if request.headers.get("X-API-Key", "") != _api_key:
                return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

trades_bp = Blueprint("trades", __name__)

_journal = TradeJournal()


@trades_bp.route("/api/trades", methods=["GET"])
@require_api_key
def api_list():
    """查询交易记录列表（分页/过滤）"""
    status = request.args.get("status", "all")
    if status == "all":
        status = None
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    sector = request.args.get("sector")
    pattern = request.args.get("pattern")
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
    except ValueError:
        return jsonify({"error": "invalid page/page_size"}), 400

    result = _journal.query_trades(
        status=status,
        start_date=start_date,
        end_date=end_date,
        sector=sector,
        pattern=pattern,
        page=page,
        page_size=page_size,
    )
    summary = _journal.get_summary()
    result["summary"] = summary
    return jsonify(result)


@trades_bp.route("/api/trades", methods=["POST"])
@require_api_key
def api_entry():
    """录入入场记录"""
    data = request.get_json(silent=True) or {}
    required = ["trade_id", "code", "buy_price", "buy_date"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"missing field: {field}"}), 400

    # 自动填入当日市场评分（从 db_reader 读取）
    buy_date = data.get("buy_date", "")
    if buy_date and not data.get("market_env_score"):
        try:
            from src.data.db_reader import get_field
            idx_chg = get_field(buy_date, "index_chg_sh000001", "morning")
            if idx_chg is not None:
                data["market_env_score"] = round(float(idx_chg) * 10 + 50, 1)
        except Exception:
            pass  # 无法获取则留空

    result = _journal.record_entry(data)
    status_code = 200 if result["status"] == "success" else 400
    return jsonify(result), status_code


@trades_bp.route("/api/trades/<trade_id>", methods=["GET"])
@require_api_key
def api_get(trade_id):
    """获取单笔交易详情"""
    result = _journal.get_trade(trade_id)
    status_code = 200 if result["status"] == "success" else 404
    return jsonify(result), status_code


@trades_bp.route("/api/trades/<trade_id>", methods=["PUT"])
@require_api_key
def api_exit(trade_id):
    """更新出场记录（平仓）"""
    data = request.get_json(silent=True) or {}

    # 计算持仓天数
    trade = _journal.get_trade(trade_id)
    if trade["status"] != "success" or not trade["records"]:
        return jsonify({"error": "trade not found"}), 404

    entry_record = next((r for r in trade["records"] if r["action"] == "entry"), None)
    if not entry_record:
        return jsonify({"error": "entry record not found"}), 404

    if not data.get("holding_days"):
        try:
            from datetime import date as date_cls
            buy_d = date_cls.fromisoformat(entry_record["date"])
            sell_d = date_cls.fromisoformat(data.get("sell_date", ""))
            data["holding_days"] = (sell_d - buy_d).days
        except Exception:
            data["holding_days"] = 0

    # 计算盈亏百分比
    if not data.get("pnl_percent") and entry_record.get("price"):
        try:
            buy_p = float(entry_record["price"])
            sell_p = float(data.get("sell_price", 0))
            data["pnl_percent"] = round((sell_p - buy_p) / buy_p * 100, 2)
        except Exception:
            pass

    result = _journal.record_exit({"trade_id": trade_id, **data})
    status_code = 200 if result["status"] == "success" else 400
    return jsonify(result), status_code


@trades_bp.route("/api/trades/summary", methods=["GET"])
@require_api_key
def api_summary():
    """交易汇总统计"""
    return jsonify(_journal.get_summary())
```

**Step 2: 注册到 app.py**

在 `app.py` 中 import 并注册 Blueprint：

在 `app.py` 顶部（其他 imports 附近）添加：
```python
from api_trades import trades_bp
```

在 `if __name__ == "__main__":` 之前添加：
```python
app.register_blueprint(trades_bp)
```

**Step 3: 语法验证**

```bash
python3 -m py_compile src/data/api_trades.py && echo "api_trades OK"
python3 -m py_compile src/data/app.py && echo "app.py OK"
```

**Step 4: Commit**

```bash
git add src/data/api_trades.py src/data/app.py
git commit -m "feat(api): add trades REST API (list/entry/exit/summary)"
```

---

## Task 4: 写单元测试

**Files:**
- Create: `tests/test_api_trades.py`

**Step 1: 写测试**

```python
"""
交易 API 单元测试
"""
import pytest, os, tempfile
from src.data.evolution.trade_journal import TradeJournal

# 使用临时数据库
@pytest.fixture
def journal():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    j = TradeJournal(db_path=path)
    yield j
    os.unlink(path)

def test_entry_and_query(journal):
    r = journal.record_entry({
        "trade_id": "T001",
        "code": "600519",
        "name": "贵州茅台",
        "buy_price": 1850.0,
        "buy_date": "2026-05-01",
        "quantity": 100,
        "pattern": "突破",
        "sector": "白酒",
        "stop_loss": 1757.5,
        "take_profit": 2035.0,
    })
    assert r["status"] == "success"

    result = journal.query_trades(status="holding")
    assert result["total"] == 1
    assert result["trades"][0]["code"] == "600519"
    assert result["summary"]["holding"] == 1

def test_exit_and_summary(journal):
    journal.record_entry({
        "trade_id": "T002",
        "code": "000001",
        "buy_price": 15.0,
        "buy_date": "2026-04-01",
    })
    r = journal.record_exit({
        "trade_id": "T002",
        "sell_price": 16.5,
        "sell_date": "2026-05-01",
        "reason": "止盈",
    })
    assert r["status"] == "success"

    s = journal.get_summary()
    assert s["total"] == 1
    assert s["closed"] == 1
    assert s["win_count"] == 1
    assert s["win_rate"] == 1.0

def test_query_pagination(journal):
    for i in range(5):
        journal.record_entry({
            "trade_id": f"T{i:03d}",
            "code": f"60000{i}",
            "buy_price": 10.0,
            "buy_date": "2026-05-01",
        })
    result = journal.query_trades(page=1, page_size=2)
    assert result["total"] == 5
    assert len(result["trades"]) == 2
    assert result["page"] == 1
```

**Step 2: 运行测试**

```bash
cd /mnt/c/Users/WINGO/Documents/WorkSpace/trading-system
python -m pytest tests/test_api_trades.py -v
```

预期：3 passed

**Step 3: Commit**

```bash
git add tests/test_api_trades.py
git commit -m "test(trades): add unit tests for trades API"
```

---

## Task 5: 集成测试（Flask test client）

**Step 1: 写 Flask 集成测试**

在 `tests/test_api_trades.py` 末尾追加：

```python
from src.data.app import app

@pytest.fixture
def client(journal):
    # Monkeypatch TradeJournal
    import src.data.api_trades as api_trades
    api_trades._journal = journal
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c

def test_flask_entry(client):
    resp = client.post("/api/trades",
        json={
            "trade_id": "T003",
            "code": "600519",
            "buy_price": 1850.0,
            "buy_date": "2026-05-01",
        },
        headers={"X-API-Key": ""},  # 无 FLASK_API_KEY，不校验
    )
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "success"

def test_flask_list(client):
    resp = client.get("/api/trades?status=all")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "trades" in data
    assert "summary" in data

def test_flask_summary(client):
    resp = client.get("/api/trades/summary")
    assert resp.status_code == 200
    s = resp.get_json()
    assert "total" in s and "win_rate" in s
```

**Step 2: 运行**

```bash
python -m pytest tests/test_api_trades.py::test_flask_entry tests/test_api_trades.py::test_flask_list tests/test_api_trades.py::test_flask_summary -v
```

**Step 3: Commit**

```bash
git add tests/test_api_trades.py
git commit -m "test(trades): add Flask integration tests for trades API"
```

---

## 验证汇总

所有 Task 完成后，运行：

```bash
cd /mnt/c/Users/WINGO/Documents/WorkSpace/trading-system

# 1. 语法检查
python3 -m py_compile src/data/api_trades.py src/data/app.py src/data/evolution/trade_journal.py

# 2. 单元测试
python -m pytest tests/test_api_trades.py -v

# 3. 现有测试不受影响
python -m pytest tests/ -q --ignore=tests/test_api_trades.py
```

预期：Phase 1 相关测试全 PASS，现有测试无回归。
