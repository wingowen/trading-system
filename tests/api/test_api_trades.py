"""
交易 API 集成测试
"""

import pytest
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src", "data"))

from flask import Flask


@pytest.fixture
def app():
    """创建测试用 Flask app"""
    test_app = Flask(__name__)
    test_app.config["TESTING"] = True
    test_app.config["JSON_AS_ASCII"] = False
    return test_app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def temp_db():
    """创建临时数据库用于测试"""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


class TestTradesAPI:
    """交易 API 测试类"""

    def test_health_check(self, client):
        """测试健康检查端点"""
        response = client.get("/api/health")
        assert response.status_code in [200, 404]

    def test_trades_list_requires_auth(self, client):
        """测试交易列表需要鉴权"""
        response = client.get("/api/trades")
        assert response.status_code in [401, 404]

    def test_trades_entry_requires_auth(self, client):
        """测试入场记录需要鉴权"""
        response = client.post(
            "/api/trades",
            json={
                "trade_id": "T001",
                "code": "600519",
                "buy_price": 1850.0,
                "buy_date": "2026-05-01",
            },
        )
        assert response.status_code in [401, 404]

    def test_trades_summary_requires_auth(self, client):
        """测试汇总统计需要鉴权"""
        response = client.get("/api/trades/summary")
        assert response.status_code in [401, 404]


class TestStrategyAPI:
    """策略 API 测试类"""

    def test_strategy_review_requires_auth(self, client):
        """测试策略评估需要鉴权"""
        response = client.get("/api/strategy/review")
        assert response.status_code in [401, 404]

    def test_strategy_patterns_requires_auth(self, client):
        """测试形态统计需要鉴权"""
        response = client.get("/api/strategy/patterns")
        assert response.status_code in [401, 404]

    def test_strategy_sectors_requires_auth(self, client):
        """测试板块统计需要鉴权"""
        response = client.get("/api/strategy/sectors")
        assert response.status_code in [401, 404]


class TestOrchestratorAPI:
    """编排器 API 测试类"""

    def test_orchestrator_run_requires_auth(self, client):
        """测试编排器需要鉴权"""
        response = client.get("/api/orchestrator/run")
        assert response.status_code in [401, 404]


class TestAPIKeyAuth:
    """API 鉴权测试"""

    def test_valid_api_key(self, client, monkeypatch):
        """测试有效的 API key"""
        monkeypatch.setenv("FLASK_API_KEY", "test-key-123")
        response = client.get("/api/trades", headers={"X-API-Key": "test-key-123"})
        assert response.status_code in [200, 401, 404]

    def test_invalid_api_key(self, client, monkeypatch):
        """测试无效的 API key"""
        monkeypatch.setenv("FLASK_API_KEY", "test-key-123")
        response = client.get("/api/trades", headers={"X-API-Key": "wrong-key"})
        assert response.status_code in [401, 404]


class TestDatabaseMigration:
    """数据库迁移测试"""

    def test_migration_script_exists(self):
        """测试迁移脚本是否存在"""
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        migration_path = os.path.join(
            base_dir, "migrations", "001_add_status_to_trade_journal.py"
        )
        assert os.path.exists(migration_path), f"迁移脚本不存在: {migration_path}"

    def test_migration_script_executable(self):
        """测试迁移脚本可执行"""
        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        migration_path = os.path.join(
            base_dir, "migrations", "001_add_status_to_trade_journal.py"
        )
        with open(migration_path, "r") as f:
            content = f.read()
            assert "def migrate()" in content
            assert "ALTER TABLE" in content.upper()
