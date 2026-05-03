"""
Tushare 数据源测试脚本
测试所有可用的数据类型

数据源说明:
- Tushare: 国内知名 A 股数据平台，提供全面基本面+行情数据
- 官网: https://tushare.pro
- 安装: pip install tushare
- 注册: https://tushare.pro/register?reg=3159 (需要注册获取 token)
- 数据: 股票/指数/基金/期货/期权/财务/基本面等
- 积分: 不同数据需要不同积分权限，免费用户基础权限已覆盖本测试大部分数据
- Token 设置: export TUSHARE_TOKEN="你的token"
  或在代码中直接设置: tushare.set_token("你的token")
"""
import os
import tushare as ts
import pandas as pd
from datetime import datetime, timedelta

# 尝试设置 token
TUSHARE_TOKEN='d2730fc05c99cf3b4acdb9d7bd58af0385e8116185de1809550b11f4'
if TUSHARE_TOKEN:
    ts.set_token(TUSHARE_TOKEN)
    print(f"  [Token已设置] {TUSHARE_TOKEN[:8]}...")
else:
    # 尝试读取本地配置文件
    token_file = os.path.expanduser("~/.tushare_token")
    if os.path.exists(token_file):
        with open(token_file) as f:
            TUSHARE_TOKEN = f.read().strip()
            ts.set_token(TUSHARE_TOKEN)
            print(f"  [Token从文件加载] {TUSHARE_TOKEN[:8]}...")
    else:
        print("  [警告] 未设置 TUSHARE_TOKEN，环境变量 ~/.tushare_token 均不存在")
        print("  [提示] 免费注册 https://tushare.pro/register?reg=3159 获取 token")
        print("  [提示] export TUSHARE_TOKEN='你的token' 后重试")
        print("  [提示] 部分接口无需 token 即可调用")

PRO_API = None

def get_api():
    global PRO_API
    if PRO_API is None:
        try:
            PRO_API = ts.pro_api()
            print("  [API 初始化成功]")
        except Exception as e:
            print(f"  [API 初始化失败] {e}")
            PRO_API = None
    return PRO_API

def to_sample(df, n=3):
    if df is None or df.empty:
        return {}
    return {"rows": len(df), "columns": list(df.columns), "sample": df.tail(n).to_dict(orient='records')}

# ============================================================
# 测试函数
# ============================================================

def test_index_daily():
    """测试指数日线数据"""
    print("\n--- test_index_daily: 上证指数日线 ---")
    api = get_api()
    if api is None:
        return False
    try:
        today = datetime.today().strftime('%Y%m%d')
        start = (datetime.today() - timedelta(days=30)).strftime('%Y%m%d')
        df = api.index_daily(ts_code='000001.SH', start_date=start, end_date=today)
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_index_basic():
    """测试指数基本信息"""
    print("\n--- test_index_basic: 指数基本信息 ---")
    api = get_api()
    if api is None:
        return False
    try:
        df = api.index_basic(ts_code='000001.SH')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        if len(df) > 0:
            print(f"  数据: {df.to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_stock_daily():
    """测试个股日线数据（前复权）"""
    print("\n--- test_stock_daily: 平安银行日线 ---")
    api = get_api()
    if api is None:
        return False
    try:
        today = datetime.today().strftime('%Y%m%d')
        start = (datetime.today() - timedelta(days=30)).strftime('%Y%m%d')
        df = api.daily(ts_code='000001.SZ', start_date=start, end_date=today)
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_stock_basic():
    """测试股票基本信息"""
    print("\n--- test_stock_basic: 股票基本信息 ---")
    api = get_api()
    if api is None:
        return False
    try:
        df = api.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name,area,industry,list_date')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df.head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_suspend():
    """测试停牌数据"""
    print("\n--- test_suspend: 停牌数据 ---")
    api = get_api()
    if api is None:
        return False
    try:
        today = datetime.today().strftime('%Y%m%d')
        df = api.suspend_d(ts_code='', suspend_date=today, fields='ts_code,suspend_date,resume_date')
        print(f"  今日停牌数: {len(df)}, 字段: {list(df.columns)}")
        if len(df) > 0:
            print(f"  示例: {df.head(3).to_dict(orient='records')}")
        return True  # 停牌数可能为0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_financial():
    """测试财务报表（利润表）"""
    print("\n--- test_financial: 平安银行利润表 ---")
    api = get_api()
    if api is None:
        return False
    try:
        df = api.fina_indicator(ts_code='000001.SZ', start_date='2024-01-01', end_date='2024-12-31')
        print(f"  记录数: {len(df)}, 字段数: {len(df.columns)}")
        print(f"  字段(前10): {list(df.columns)[:10]}")
        if len(df) > 0:
            print(f"  最新: {df.tail(2)[['ts_code','ann_date','roe','gross_profit_margin']].to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_income():
    """测试利润表"""
    print("\n--- test_income: 贵州茅台利润表 ---")
    api = get_api()
    if api is None:
        return False
    try:
        df = api.income(ts_code='600519.SH', start_date='2024-01-01', end_date='2024-12-31', fields='ts_code,ann_date,f_ann_date,report_type,revenue,income,total_profit,nincome')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        if len(df) > 0:
            print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_balance():
    """测试资产负债表"""
    print("\n--- test_balance: 贵州茅台资产负债表 ---")
    api = get_api()
    if api is None:
        return False
    try:
        df = api.balancesheet(ts_code='600519.SH', start_date='2024-01-01', end_date='2024-12-31', fields='ts_code,ann_date,total_liab,total_assets')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        if len(df) > 0:
            print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_cashflow():
    """测试现金流量表"""
    print("\n--- test_cashflow: 贵州茅台现金流量表 ---")
    api = get_api()
    if api is None:
        return False
    try:
        df = api.cashflow(ts_code='600519.SH', start_date='2024-01-01', end_date='2024-12-31', fields='ts_code,ann_date,net_profit,operate_cash_flow,invest_cash_flow')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        if len(df) > 0:
            print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_moneyflow():
    """测试资金流向（南向/北向）"""
    print("\n--- test_moneyflow: 个股资金流 ---")
    api = get_api()
    if api is None:
        return False
    try:
        today = datetime.today().strftime('%Y%m%d')
        start = (datetime.today() - timedelta(days=5)).strftime('%Y%m%d')
        df = api.moneyflow(ts_code='000001.SZ', start_date=start, end_date=today)
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        if len(df) > 0:
            print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_hsgt():
    """测试沪深港通数据"""
    print("\n--- test_hsgt: 北向资金流向 ---")
    api = get_api()
    if api is None:
        return False
    try:
        today = datetime.today().strftime('%Y%m%d')
        start = (datetime.today() - timedelta(days=10)).strftime('%Y%m%d')
        df = api.hk_hold(start_date=start, end_date=today)
        print(f"  北向资金持股记录: {len(df)}, 字段: {list(df.columns)}")
        if len(df) > 0:
            print(f"  示例: {df.head(2).to_dict(orient='records')}")
        return True
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_top_list():
    """测试龙虎榜数据"""
    print("\n--- test_top_list: 每日龙虎榜 ---")
    api = get_api()
    if api is None:
        return False
    try:
        today = datetime.today().strftime('%Y%m%d')
        start = (datetime.today() - timedelta(days=5)).strftime('%Y%m%d')
        df = api.top_list(start_date=start, end_date=today)
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        if len(df) > 0:
            print(f"  最新: {df.head(2).to_dict(orient='records')}")
        return True  # 可能无数据
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_market_activity():
    """测试市场情绪（涨跌停统计）"""
    print("\n--- test_market_activity: 涨跌停统计 ---")
    api = get_api()
    if api is None:
        return False
    try:
        today = datetime.today().strftime('%Y%m%d')
        df = api.limit_list(trade_date=today)
        print(f"  涨停统计: {len(df)}, 字段: {list(df.columns)}")
        if len(df) > 0:
            print(f"  示例: {df.head(3).to_dict(orient='records')}")
        return True
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_stk_rewards():
    """测试个股机构调研/评级"""
    print("\n--- test_stk_rewards: 个股评级数据 ---")
    api = get_api()
    if api is None:
        return False
    try:
        df = api.stk_rewards(ts_code='000001.SZ', start_date='2026-01-01', end_date='2026-05-03')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        if len(df) > 0:
            print(f"  示例: {df.head(2).to_dict(orient='records')}")
        return True  # 研报数据可能为空
    except Exception as e:
        print(f"  失败: {e}")
        return False

if __name__ == "__main__":
    tests = [
        ("test_index_daily", test_index_daily),
        ("test_index_basic", test_index_basic),
        ("test_stock_daily", test_stock_daily),
        ("test_stock_basic", test_stock_basic),
        ("test_suspend", test_suspend),
        ("test_financial", test_financial),
        ("test_income", test_income),
        ("test_balance", test_balance),
        ("test_cashflow", test_cashflow),
        ("test_moneyflow", test_moneyflow),
        ("test_hsgt", test_hsgt),
        ("test_top_list", test_top_list),
        ("test_market_activity", test_market_activity),
        ("test_stk_rewards", test_stk_rewards),
    ]
    
    results = {}
    print(f"\n{'='*60}")
    print(f"Tushare 数据源测试 - 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    for name, fn in tests:
        try:
            results[name] = fn()
        except Exception as e:
            print(f"  [异常] {e}")
            results[name] = False
    
    print(f"\n{'='*60}")
    print("测试结果汇总:")
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"{'='*60}")
