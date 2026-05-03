"""
测试龙虎榜数据获取功能
对应文档需求: top_list - 龙虎榜数据
"""
import akshare as ak
from datetime import datetime

def test_lhb_detail():
    """测试每日龙虎榜数据"""
    print("\n=== 测试每日龙虎榜数据 ===")
    try:
        # 获取最近一个交易日的数据
        df = ak.stock_lhb_detail_em()
        print(f"获取成功，共 {len(df)} 条记录")
        print(f"字段: {list(df.columns)}")
        print("\n前3条数据:")
        print(df.head(3).to_dict(orient='records'))
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False

def test_lhb_stock_stat():
    """测试个股龙虎榜统计"""
    print("\n=== 测试个股龙虎榜统计 ===")
    try:
        df = ak.stock_lhb_stock_stat_em(symbol="近一月")
        print(f"获取成功，共 {len(df)} 条记录")
        print(f"字段: {list(df.columns)}")
        print("\n前3条数据:")
        print(df.head(3).to_dict(orient='records'))
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False

if __name__ == "__main__":
    test_lhb_detail()
    test_lhb_stock_stat()
