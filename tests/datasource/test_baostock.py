"""
Baostock 数据源测试脚本
测试所有可用的数据类型

数据源说明:
- baostock: 免费开源 A 股数据接口，无需注册
- 官网: http://www.baostock.com
- 数据: 个股/指数历史 K 线、财务报表、融资融券等
- 限制: 日内实时数据需付费，盘后数据免费
"""
import baostock as bs
import pandas as pd
from datetime import datetime, timedelta

LOGIN_OK = False

def ensure_login():
    global LOGIN_OK
    if not LOGIN_OK:
        rs = bs.login()
        if rs.error_code == '0':
            LOGIN_OK = True
            print(f"  [登录成功]")
        else:
            print(f"  [登录失败] {rs.error_msg}")
            return False
    return True

# ============================================================
# 测试函数
# ============================================================

def test_index_daily():
    """测试指数日线数据"""
    print("\n--- test_index_daily: 沪深300指数日线 ---")
    if not ensure_login():
        return False
    rs = bs.query_history_k_data_plus(
        "sh.000300",
        "date,code,open,high,low,close,volume,amount",
        start_date='2026-04-01', end_date='2026-05-03',
        frequency="d", adjustflag="3"
    )
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  最新: {df.tail(2).to_dict(orient='records')}")
    return len(df) > 0

def test_stock_daily():
    """测试个股日线数据"""
    print("\n--- test_stock_daily: 平安银行日线 ---")
    if not ensure_login():
        return False
    rs = bs.query_history_k_data_plus(
        "sz.000001",
        "date,code,open,high,low,close,volume,amount,turn",
        start_date='2026-04-01', end_date='2026-05-03',
        frequency="d", adjustflag="2"
    )
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  最新: {df.tail(2).to_dict(orient='records')}")
    return len(df) > 0

def test_adjust_factor():
    """测试复权因子数据"""
    print("\n--- test_adjust_factor: 平安银行复权因子 ---")
    if not ensure_login():
        return False
    rs = bs.query_adjust_factor(
        code="sz.000001",
        start_date='2026-04-01', end_date='2026-05-03'
    )
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  最新: {df.tail(2).to_dict(orient='records')}")
    return len(df) > 0

def test_stock_basic():
    """测试股票基本信息"""
    print("\n--- test_stock_basic: 股票基本信息 ---")
    if not ensure_login():
        return False
    rs = bs.query_stock_basic(code="sz.000001")
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  数据: {df.to_dict(orient='records')}")
    return len(df) > 0

def test_trade_dates():
    """测试交易日历"""
    print("\n--- test_trade_dates: 交易日历 ---")
    if not ensure_login():
        return False
    rs = bs.query_trade_dates(start_date='2026-04-01', end_date='2026-05-03')
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  示例: {df[df['is_trading_day']=='1'].tail(3).to_dict(orient='records')}")
    return len(df) > 0

def test_hs300():
    """测试沪深300成分股"""
    print("\n--- test_hs300: 沪深300成分股 ---")
    if not ensure_login():
        return False
    rs = bs.query_hs300_stocks()
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  示例: {df.head(3).to_dict(orient='records')}")
    return len(df) > 0

def test_sz50():
    """测试上证50成分股"""
    print("\n--- test_sz50: 上证50成分股 ---")
    if not ensure_login():
        return False
    rs = bs.query_sz50_stocks()
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  示例: {df.head(3).to_dict(orient='records')}")
    return len(df) > 0

def test_zz500():
    """测试中证500成分股"""
    print("\n--- test_zz500: 中证500成分股 ---")
    if not ensure_login():
        return False
    rs = bs.query_zz500_stocks()
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  示例: {df.head(3).to_dict(orient='records')}")
    return len(df) > 0

def test_profit_data():
    """测试盈利指标数据"""
    print("\n--- test_profit_data: 平安银行盈利指标 ---")
    if not ensure_login():
        return False
    rs = bs.query_profit_data(code="sz.000001", year='2024', quarter='4')
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  数据: {df.to_dict(orient='records')}")
    return len(df) > 0

def test_balance_data():
    """测试资产负债数据"""
    print("\n--- test_balance_data: 平安银行资产负债 ---")
    if not ensure_login():
        return False
    rs = bs.query_balance_data(code="sz.000001", year='2024', quarter='4')
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  数据: {df.to_dict(orient='records')}")
    return len(df) > 0

def test_cash_flow_data():
    """测试现金流数据"""
    print("\n--- test_cash_flow_data: 平安银行现金流 ---")
    if not ensure_login():
        return False
    rs = bs.query_cash_flow_data(code="sz.000001", year='2024', quarter='4')
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  数据: {df.to_dict(orient='records')}")
    return len(df) > 0

def test_dupont_data():
    """测试杜邦分析数据"""
    print("\n--- test_dupont_data: 平安银行杜邦分析 ---")
    if not ensure_login():
        return False
    rs = bs.query_dupont_data(code="sz.000001", year='2024', quarter='4')
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  数据: {df.to_dict(orient='records')}")
    return len(df) > 0

def test_operation_data():
    """测试运营能力数据"""
    print("\n--- test_operation_data: 平安银行运营能力 ---")
    if not ensure_login():
        return False
    rs = bs.query_operation_data(code="sz.000001", year='2024', quarter='4')
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  数据: {df.to_dict(orient='records')}")
    return len(df) > 0

def test_growth_data():
    """测试成长能力数据"""
    print("\n--- test_growth_data: 平安银行成长能力 ---")
    if not ensure_login():
        return False
    rs = bs.query_growth_data(code="sz.000001", year='2024', quarter='4')
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  数据: {df.to_dict(orient='records')}")
    return len(df) > 0

def test_dividend_data():
    """测试分红配股数据"""
    print("\n--- test_dividend_data: 平安银行分红数据 ---")
    if not ensure_login():
        return False
    rs = bs.query_dividend_data(code="sz.000001", year='2024')
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  最新: {df.tail(2).to_dict(orient='records')}")
    return True  # 无分红也正常

def test_stock_industry():
    """测试股票所属行业"""
    print("\n--- test_stock_industry: 平安银行所属行业 ---")
    if not ensure_login():
        return False
    rs = bs.query_stock_industry()
    data = []
    while rs.error_code == '0' and rs.next():
        data.append(rs.get_row_data())
    df = pd.DataFrame(data, columns=rs.fields)
    # 过滤出平安银行
    df_pa = df[df['code'] == 'sz.000001'] if 'code' in df.columns else df
    print(f"  全量行业股票数: {len(df)}, 字段: {list(df.columns)}")
    print(f"  平安银行: {df_pa.to_dict(orient='records')}")
    return len(df) > 0

if __name__ == "__main__":
    tests = [
        ("test_index_daily", test_index_daily),
        ("test_stock_daily", test_stock_daily),
        ("test_adjust_factor", test_adjust_factor),
        ("test_stock_basic", test_stock_basic),
        ("test_trade_dates", test_trade_dates),
        ("test_hs300", test_hs300),
        ("test_sz50", test_sz50),
        ("test_zz500", test_zz500),
        ("test_profit_data", test_profit_data),
        ("test_balance_data", test_balance_data),
        ("test_cash_flow_data", test_cash_flow_data),
        ("test_dupont_data", test_dupont_data),
        ("test_operation_data", test_operation_data),
        ("test_growth_data", test_growth_data),
        ("test_dividend_data", test_dividend_data),
        ("test_stock_industry", test_stock_industry),
    ]

    results = {}
    start_time = datetime.now()
    print(f"\n{'='*60}")
    print(f"Baostock 数据源测试 - 开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    for name, fn in tests:
        try:
            results[name] = fn()
        except Exception as e:
            print(f"  [异常] {e}")
            results[name] = False

    if LOGIN_OK:
        bs.logout()

    end_time = datetime.now()
    print(f"\n{'='*60}")
    print("测试结果汇总:")
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"耗时: {(end_time - start_time).total_seconds():.1f}s")
    print(f"{'='*60}")
