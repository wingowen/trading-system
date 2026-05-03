"""
pytdx 数据源测试脚本
测试所有可用的数据类型

数据源说明:
- pytdx: 通达信数据接口的 Python 实现
- 官网: https://github.com/peerfinance/pytdx
- 安装: pip install pytdx
- 数据: A 股/期货/港股实时行情、历史 K 线
- 限制: 需要连接通达信行情服务器（免费公开服务器不稳定）
- 特点: 速度快，实时性好，但公开服务器质量参差不齐
- 建议: 生产环境建议自建通达信服务器或使用付费行情服务

已知问题: 公开服务器 118.244.123.178:7709 可连接但数据返回 None，可能已失效
"""
from pytdx.hq import TdxHq_API
import pandas as pd
from datetime import datetime

API = None
SERVER = ('118.244.123.178', 7709)

def get_api():
    global API
    if API is None:
        API = TdxHq_API(heartbeat=True, auto_retry=True)
        try:
            API.connect(*SERVER)
            print(f"  [连接成功] {SERVER}")
        except Exception as e:
            print(f"  [连接失败] {e}")
            return None
    return API

# ============================================================
# 测试函数
# ============================================================

def test_realtime_quote():
    """测试实时行情（多股票）"""
    print("\n--- test_realtime_quote: 实时行情快照 ---")
    api = get_api()
    if api is None:
        return False
    try:
        data = api.get_security_quotes([(0, '000001'), (1, '000001'), (0, '600519')])
        print(f"  记录数: {len(data) if data else 0}")
        if data:
            print(f"  示例: {data[:1]}")
            return True
        else:
            print("  [警告] 返回空数据，服务器可能不可用")
            return False
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_index_kline():
    """测试指数 K 线数据"""
    print("\n--- test_index_kline: 上证指数日 K 线 ---")
    api = get_api()
    if api is None:
        return False
    try:
        # category: 9=日线, 0=1分钟, 1=5分钟, 4=日线
        # market: 0=上证, 1=深证
        data = api.get_security_bars(category=9, market=0, code='000001', start=0, count=10)
        print(f"  记录数: {len(data) if data else 0}")
        if data:
            print(f"  最新: {data[-2:]}")
            return True
        else:
            print("  [警告] 返回空数据，服务器可能不可用")
            return False
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_stock_kline():
    """测试个股 K 线数据"""
    print("\n--- test_stock_kline: 平安银行日 K 线 ---")
    api = get_api()
    if api is None:
        return False
    try:
        data = api.get_security_bars(category=9, market=1, code='000001', start=0, count=10)
        print(f"  记录数: {len(data) if data else 0}")
        if data:
            print(f"  字段: {list(data[0].keys())}")
            print(f"  最新: {data[-2:]}")
            return True
        else:
            print("  [警告] 返回空数据")
            return False
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_minute_kline():
    """测试分钟 K 线数据"""
    print("\n--- test_minute_kline: 平安银行5分钟线 ---")
    api = get_api()
    if api is None:
        return False
    try:
        data = api.get_security_bars(category=1, market=1, code='000001', start=0, count=10)
        print(f"  记录数: {len(data) if data else 0}")
        if data:
            print(f"  最新: {data[-2:]}")
            return True
        else:
            print("  [警告] 返回空数据")
            return False
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_index_list():
    """测试指数列表"""
    print("\n--- test_index_list: 上证指数列表 ---")
    api = get_api()
    if api is None:
        return False
    try:
        data = api.get_index_list(0, start=0, count=20)
        print(f"  记录数: {len(data) if data else 0}")
        if data:
            print(f"  示例: {data[:2]}")
            return True
        else:
            print("  [警告] 返回空数据")
            return False
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_stock_list():
    """测试股票列表"""
    print("\n--- test_stock_list: 深市股票列表 ---")
    api = get_api()
    if api is None:
        return False
    try:
        data = api.get_stock_list(1, start=0, count=20)
        print(f"  记录数: {len(data) if data else 0}")
        if data:
            print(f"  示例: {data[:2]}")
            return True
        else:
            print("  [警告] 返回空数据")
            return False
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_finance():
    """测试财务数据"""
    print("\n--- test_finance: 平安银行财务数据 ---")
    api = get_api()
    if api is None:
        return False
    try:
        data = api.get_finance_info(1, '000001')
        print(f"  字段数: {len(data) if data else 0}")
        if data:
            key_fields = ['code', 'name', 'total_mv', 'circulating_mv', 'pe', 'pb']
            sample = {k: data.get(k) for k in key_fields if k in data}
            print(f"  关键字段: {sample}")
            return True
        else:
            print("  [警告] 返回空数据")
            return False
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_xdxr():
    """测试除权除息数据"""
    print("\n--- test_xdxr: 平安银行除权除息 ---")
    api = get_api()
    if api is None:
        return False
    try:
        data = api.get_xdxr_info(1, '000001')
        print(f"  记录数: {len(data) if data else 0}")
        if data:
            print(f"  最新: {data[-2:]}")
            return True
        else:
            return True  # 无数据也正常
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_history_bars():
    """测试历史K线（含日期范围）"""
    print("\n--- test_history_bars: 历史日K数据 ---")
    api = get_api()
    if api is None:
        return False
    try:
        data = api.get_history_security_bars(
            category=9, market=1, code='000001',
            start_date='2026-01-01', end_date='2026-05-03'
        )
        print(f"  记录数: {len(data) if data else 0}")
        if data:
            print(f"  最新: {data[-2:]}")
            return True
        else:
            print("  [警告] 返回空数据")
            return False
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_instrument_count():
    """测试市场股票数量"""
    print("\n--- test_instrument_count: 市场股票数量 ---")
    api = get_api()
    if api is None:
        return False
    try:
        count = api.get_instrument_count()
        print(f"  市场股票总数: {count}")
        return count > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

if __name__ == "__main__":
    tests = [
        ("test_realtime_quote", test_realtime_quote),
        ("test_index_kline", test_index_kline),
        ("test_stock_kline", test_stock_kline),
        ("test_minute_kline", test_minute_kline),
        ("test_index_list", test_index_list),
        ("test_stock_list", test_stock_list),
        ("test_finance", test_finance),
        ("test_xdxr", test_xdxr),
        ("test_history_bars", test_history_bars),
        ("test_instrument_count", test_instrument_count),
    ]

    results = {}
    start_time = datetime.now()
    print(f"\n{'='*60}")
    print(f"pytdx 数据源测试 - 开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    for name, fn in tests:
        try:
            results[name] = fn()
        except Exception as e:
            print(f"  [异常] {e}")
            results[name] = False

    if API:
        try:
            API.disconnect()
        except:
            pass

    end_time = datetime.now()
    print(f"\n{'='*60}")
    print("测试结果汇总:")
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"耗时: {(end_time - start_time).total_seconds():.1f}s")
    print(f"{'='*60}")
