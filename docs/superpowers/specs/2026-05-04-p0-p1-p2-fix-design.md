# Trading System P0/P1/P2 修复设计

## 修复日期：2026-05-04

## 问题清单

### P0 — 阻断性
1. `pyproject.toml` 缺少 Flask/pytest 依赖
2. `fix/schema-unification` 分支长期未合并

### P1 — 影响功能
3. `api_trades.py` 导入路径不统一（`from evolution.trade_journal` 应为 `from .evolution.trade_journal`）
4. `app.py` 第 245 行硬编码 hermes-agent venv path

### P1 — 维护性
5. DB 路径硬编码在三处（`app.py`、`db_writer.py`、`trade_journal.py`）
6. `AGENTS.md` 与 `CLAUDE.md` 内容完全重复

### P2 — 小问题
7. `.venv/bin/python` 是二进制非解释器脚本
8. `app.py` 冗余 import（`sys as _sys`）
9. `.trae/skills/` 与 `.claude/skills/` 重复
10. `test/` 与 `tests/` 目录混乱

---

## 修复方案

### P0-1: pyproject.toml 添加依赖

```toml
[project]
dependencies = [
    "akshare>=1.18.60",
    "baostock>=0.9.1",
    "efinance>=0.5.8",
    "pytdx>=1.72",
    "tushare>=1.4.29",
    "pandas",
    "websocket-client>=1.7.0",
    "flask>=3.0.0",
    "werkzeug>=3.0.0",
    "jinja2>=3.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "pytest-asyncio>=0.23.0"]
```

### P0-2: 分支合并

修复完成后，将 `fix/schema-unification` 通过 PR 合并回 master。

### P1-3: 统一导入路径

`api_trades.py` 第 8 行：
```python
# 改前
from evolution.trade_journal import TradeJournal
# 改后
from .evolution.trade_journal import TradeJournal
```

### P1-4: 移除硬编码 hermes path

`app.py` 第 245 行改为直接 import，不依赖 hermes venv：
```python
# 删掉这行
# _sys.path.insert(0, "/home/wingo/.hermes/hermes-agent/venv/lib/python3.11/site-packages")
# 改为函数内直接 import websocket
```

### P1-5: DB 路径统一为环境变量

新建 `src/data/config.py`：
```python
import os
from pathlib import Path

DB_PATH = os.environ.get(
    "STOCKEXPERT_DB",
    str(Path(__file__).parent.parent.parent / "data" / "stockexpert.db")
)
```

三处修改：
- `app.py` → `from .config import DB_PATH`
- `db_writer.py` → `from .config import DB_PATH`
- `trade_journal.py` → `from .config import DB_PATH`

### P1-6: 删除重复文件

删除 `CLAUDE.md`（内容与 `AGENTS.md` 完全相同）

### P2-7: 修复 venv python 解释器

`.venv/bin/python` 是二进制脚本（不是可执行文本），在 pyproject.toml 中明确指定 python 版本：
```toml
requires-python = ">=3.11"
```

### P2-8: 清理冗余 import

`app.py` 第 13 行：`import sys` 后函数内重复 import，保留全局 `sys` 并移除函数内冗余引用。

### P2-9: 清理重复 skill 目录

删除 `.trae/skills/` 整个目录。

### P2-10: 合并测试目录

移动 `test/datasource/*.py` → `tests/datasource/`。

---

## 架构影响

- 无架构变更，纯修复
- 所有改动向后兼容
- 新增 `src/data/config.py` 作为 DB_PATH 单一真相源

## 验收标准

1. `uv pip install -e ".[dev]"` 成功
2. `.venv/bin/python -m pytest tests/ -v` 通过
3. `python src/data/app.py` 能启动（Flask 服务）
4. 无硬编码 Windows path
5. `git branch -a` 无未合并长期分支
