"""
efinance 数据源测试脚本
测试所有可用的数据类型

数据源说明:
- efinance: 基于 Eastmoney 的免费 A 股数据库
- 官网: https://github.com/MicroCSV/efinance
- 安装: pip install efinance
- 数据: 实时行情/板块/K线/基本面
- 限制: jsonpath 内部冲突导致部分接口报错（已标注）
- 字段名: 中文列名（股票代码/名称/最新价等）
"""
import efinance as ef
import pandas as pd
from datetime import datetime

# ============================================================
# 测试函数
# ============================================================

def test_realtime_quote_industry():
    """测试行业板块实时行情"""
    print("\n--- test_realtime_quote_industry: 行业板块实时行情 ---")
    try:
        df = ef.stock.get_realtime_quotes('行业板块')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df[['股票代码','股票名称','涨跌幅','最新价','成交额']].head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_realtime_quote_concept():
    """测试概念板块实时行情"""
    print("\n--- test_realtime_quote_concept: 概念板块实时行情 ---")
    try:
        df = ef.stock.get_realtime_quotes('概念板块')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df[['股票代码','股票名称','涨跌幅','最新价','成交额']].head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_realtime_quote_sh():
    """测试沪市 A 股实时行情"""
    print("\n--- test_realtime_quote_sh: 沪市A股实时行情 ---")
    try:
        df = ef.stock.get_realtime_quotes('沪A')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df[['股票代码','股票名称','涨跌幅','最新价','总市值']].head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_realtime_quote_sz():
    """测试深市 A 股实时行情"""
    print("\n--- test_realtime_quote_sz: 深市A股实时行情 ---")
    try:
        df = ef.stock.get_realtime_quotes('深A')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df[['股票代码','股票名称','涨跌幅','最新价','流通市值']].head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_realtime_quote_kcb():
    """测试科创板实时行情"""
    print("\n--- test_realtime_quote_kcb: 科创板实时行情 ---")
    try:
        df = ef.stock.get_realtime_quotes('科创板')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df[['股票代码','股票名称','涨跌幅','最新价']].head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_realtime_quote_hgt():
    """测试沪股通实时行情"""
    print("\n--- test_realtime_quote_hgt: 沪股通实时行情 ---")
    try:
        df = ef.stock.get_realtime_quotes('沪股通')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df[['股票代码','股票名称','涨跌幅','最新价']].head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_quote_history():
    """测试股票历史 K 线"""
    print("\n--- test_quote_history: 贵州茅台日K线 ---")
    try:
        df = ef.stock.get_quote_history('600519', beg='20260401', end='20260503', klt=101, fqt=1)
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_quote_history_minute():
    """测试股票分钟 K 线"""
    print("\n--- test_quote_history_minute: 平安银行5分钟K线 ---")
    try:
        df = ef.stock.get_quote_history('000001', beg='20260503', end='20260503', klt=5, fqt=1)
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_quote_snapshot():
    """测试股票行情快照"""
    print("\n--- test_quote_snapshot: 平安银行行情快照 ---")
    try:
        series = ef.stock.get_quote_snapshot('000001')
        print(f"  类型: Series, 字段数: {len(series)}")
        key_fields = ['股票代码','股票名称','最新价','涨跌幅','今开','最高','最低','成交量','成交额']
        sample = {k: series.get(k) for k in key_fields if k in series.index}
        print(f"  关键字段: {sample}")
        return len(series) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_base_info():
    """测试股票基本信息"""
    print("\n--- test_base_info: 平安银行公司基本信息 ---")
    try:
        series = ef.stock.get_base_info('000001')
        print(f"  类型: Series, 字段数: {len(series)}")
        print(f"  数据: {dict(series)}")
        return len(series) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_members():
    """测试板块成分股"""
    print("\n--- test_members: 半导体板块成分股 ---")
    try:
        df = ef.stock.get_members('半导体')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df.head(5).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_belong_board():
    """测试股票所属板块"""
    print("\n--- test_belong_board: 中芯国际所属板块 ---")
    try:
        df = ef.stock.get_belong_board('688981')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  数据: {df.to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_deal_detail():
    """测试股票每日成交明细"""
    print("\n--- test_deal_detail: 平安银行每日成交明细 ---")
    try:
        df = ef.stock.get_deal_detail('000001', '2026-04-29')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df.head(5).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_top10_holder():
    """测试前10大股东/流通股东"""
    print("\n--- test_top10_holder: 平安银行前10股东 ---")
    try:
        df = ef.stock.get_top10_stock_holder_info('000001', '2026-03-31')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df.head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_all_report_dates():
    """测试所有财报发布日期"""
    print("\n--- test_all_report_dates: 财报发布日期列表 ---")
    try:
        dates = ef.stock.get_all_report_dates()
        print(f"  报告期数: {len(dates)}, 最近5个: {dates[-5:]}")
        return len(dates) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_all_performance():
    """测试所有股票业绩快报"""
    print("\n--- test_all_performance: 全市场业绩快报 ---")
    try:
        dates = ef.stock.get_all_report_dates()
        last_date = dates[-1] if dates else '20260331'
        df = ef.stock.get_all_company_performance(last_date)
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df.head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_latest_holder_number():
    """测试最新股东户数"""
    print("\n--- test_latest_holder_number: 平安银行最新股东户数 ---")
    try:
        df = ef.stock.get_latest_holder_number('000001')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_latest_ipo():
    """测试最新新股列表"""
    print("\n--- test_latest_ipo: 最新新股列表 ---")
    try:
        df = ef.stock.get_latest_ipo_info()
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df.head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_getter():
    """测试通用getter接口"""
    print("\n--- test_getter: 通用getter接口 ---")
    try:
        df = ef.stock.getter('600519', '2026-04-01', '2026-05-03', 'daily')
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

if __name__ == "__main__":
    tests = [
        ("test_realtime_quote_industry", test_realtime_quote_industry),
        ("test_realtime_quote_concept", test_realtime_quote_concept),
        ("test_realtime_quote_sh", test_realtime_quote_sh),
        ("test_realtime_quote_sz", test_realtime_quote_sz),
        ("test_realtime_quote_kcb", test_realtime_quote_kcb),
        ("test_realtime_quote_hgt", test_realtime_quote_hgt),
        ("test_quote_history", test_quote_history),
        ("test_quote_history_minute", test_quote_history_minute),
        ("test_quote_snapshot", test_quote_snapshot),
        ("test_base_info", test_base_info),
        ("test_members", test_members),
        ("test_belong_board", test_belong_board),
        ("test_deal_detail", test_deal_detail),
        ("test_top10_holder", test_top10_holder),
        ("test_all_report_dates", test_all_report_dates),
        ("test_all_performance", test_all_performance),
        ("test_latest_holder_number", test_latest_holder_number),
        ("test_latest_ipo", test_latest_ipo),
        ("test_getter", test_getter),
    ]

    results = {}
    start_time = datetime.now()
    print(f"\n{'='*60}")
    print(f"efinance 数据源测试 - 开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    for name, fn in tests:
        try:
            results[name] = fn()
        except Exception as e:
            print(f"  [异常] {e}")
            results[name] = False

    end_time = datetime.now()
    print(f"\n{'='*60}")
    print("测试结果汇总:")
    for name, ok in results.items():
        print(f"  {'✅' if ok else '❌'} {name}")
    print(f"耗时: {(end_time - start_time).total_seconds():.1f}s")
    print(f"{'='*60}")
