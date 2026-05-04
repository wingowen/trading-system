"""
akshare 数据源测试脚本
测试所有可用的数据类型

数据源说明:
- akshare: A 股数据全能接口，东方财富/新浪/腾讯等多源聚合
- 官网: https://akshare.akfamily.xyz
- 安装: pip install akshare
- 数据: 行情/板块/资金流/龙虎榜/基本面等
- Token: 无需
"""
import akshare as ak
import pandas as pd
from datetime import datetime

def to_sample(df, n=3):
    if df is None or df.empty:
        return {}
    return {"rows": len(df), "columns": list(df.columns), "sample": df.tail(n).to_dict(orient='records')}

# ============================================================
# 测试函数
# ============================================================

def test_index_daily():
    """测试大盘指数日线数据"""
    print("\n--- test_index_daily: 上证指数日线 ---")
    try:
        df = ak.stock_zh_index_daily(symbol="sh000001")
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_index_spot():
    """测试主要指数实时行情"""
    print("\n--- test_index_spot: 主要指数实时行情 ---")
    try:
        df = ak.stock_zh_index_spot_em()
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df[['代码','名称','最新价','涨跌幅']].head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_stock_daily():
    """测试个股日线数据"""
    print("\n--- test_stock_daily: 平安银行日线 ---")
    try:
        df = ak.stock_zh_a_hist(symbol="000001", period="daily",
                                 start_date="20260401", end_date="20260503", adjust="qfq")
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        required = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '换手率']
        missing = [f for f in required if f not in df.columns]
        print(f"  必要字段缺失: {missing}" if missing else "  所有必要字段存在")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_stock_minute():
    """测试个股分钟数据"""
    print("\n--- test_stock_minute: 平安银行分钟数据 ---")
    try:
        df = ak.stock_zh_a_hist_min(symbol="000001", start_date="2026-05-03 09:30:00",
                                     end_date="2026-05-03 15:00:00", period="5")
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_industry_board():
    """测试行业板块数据"""
    print("\n--- test_industry_board: 行业板块 ---")
    try:
        df = ak.stock_board_industry_name_em()
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df.head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_concept_board():
    """测试概念板块数据"""
    print("\n--- test_concept_board: 概念板块 ---")
    try:
        df = ak.stock_board_concept_name_em()
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df.head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_board_cons():
    """测试板块成分股"""
    print("\n--- test_board_cons: 半导体板块成分股 ---")
    try:
        df = ak.stock_board_industry_cons_em(symbol="半导体")
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df.head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_board_hist():
    """测试板块历史行情"""
    print("\n--- test_board_hist: 半导体板块历史行情 ---")
    try:
        df = ak.stock_board_industry_hist_em(symbol="半导体", period="日k", start_date="20260401", end_date="20260503")
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_market_activity():
    """测试市场活跃度"""
    print("\n--- test_market_activity: 市场活跃度 ---")
    try:
        df = ak.stock_market_activity_legu()
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_margin_sse():
    """测试融资融券（上交所）"""
    print("\n--- test_margin_sse: 融资融券(上交所) ---")
    try:
        df = ak.stock_margin_sse()
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_individual_fund_flow():
    """测试个股资金流"""
    print("\n--- test_individual_fund_flow: 个股资金流 ---")
    try:
        df = ak.stock_individual_fund_flow(stock="000001", market="sh")
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_sector_fund_flow():
    """测试板块资金流"""
    print("\n--- test_sector_fund_flow: 行业板块资金流 ---")
    try:
        df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df.head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_lhb_detail():
    """测试每日龙虎榜"""
    print("\n--- test_lhb_detail: 每日龙虎榜 ---")
    try:
        df = ak.stock_lhb_detail_em()
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df.head(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_lhb_start():
    """测试龙虎榜机构交易明细"""
    print("\n--- test_lhb_start: 龙虎榜机构交易明细 ---")
    try:
        df = ak.stock_lhb_start_em()
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_stock_info():
    """测试股票基本信息"""
    print("\n--- test_stock_info: 股票基本信息 ---")
    try:
        df = ak.stock_info_a_code_name()
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df.head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_stock_spot():
    """测试A股实时行情全量"""
    print("\n--- test_stock_spot: A股实时行情快照 ---")
    try:
        df = ak.stock_zh_a_spot_em()
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df[['代码','名称','最新价','涨跌幅']].head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_limit_list():
    """测试涨跌停统计"""
    print("\n--- test_limit_list: 涨跌停统计 ---")
    try:
        df = ak.stock_em_zt_pool(date="20260430")
        print(f"  涨停数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df.head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_profit_predict():
    """测试业绩预告/快报"""
    print("\n--- test_profit_predict: 业绩预告 ---")
    try:
        df = ak.stock_profit_forecast(indicator="预盈", end_date="2026-05-03")
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  示例: {df.head(3).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

def test_history_dividend():
    """测试历史分红数据"""
    print("\n--- test_history_dividend: 历史分红 ---")
    try:
        df = ak.stock_history_dividend_detail(symbol="000001")
        print(f"  记录数: {len(df)}, 字段: {list(df.columns)}")
        print(f"  最新: {df.tail(2).to_dict(orient='records')}")
        return len(df) > 0
    except Exception as e:
        print(f"  失败: {e}")
        return False

if __name__ == "__main__":
    tests = [
        ("test_index_daily", test_index_daily),
        ("test_index_spot", test_index_spot),
        ("test_stock_daily", test_stock_daily),
        ("test_stock_minute", test_stock_minute),
        ("test_industry_board", test_industry_board),
        ("test_concept_board", test_concept_board),
        ("test_board_cons", test_board_cons),
        ("test_board_hist", test_board_hist),
        ("test_market_activity", test_market_activity),
        ("test_margin_sse", test_margin_sse),
        ("test_individual_fund_flow", test_individual_fund_flow),
        ("test_sector_fund_flow", test_sector_fund_flow),
        ("test_lhb_detail", test_lhb_detail),
        ("test_lhb_start", test_lhb_start),
        ("test_stock_info", test_stock_info),
        ("test_stock_spot", test_stock_spot),
        ("test_limit_list", test_limit_list),
        ("test_profit_predict", test_profit_predict),
        ("test_history_dividend", test_history_dividend),
    ]

    results = {}
    start_time = datetime.now()
    print(f"\n{'='*60}")
    print(f"akshare 数据源测试 - 开始: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
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
