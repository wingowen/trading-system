"""
测试市场情绪数据获取功能
对应文档需求: index_sentiment - 市场情绪数据
"""
import akshare as ak

def test_market_activity():
    """测试市场活跃度数据"""
    print("\n=== 测试市场活跃度数据 ===")
    try:
        df = ak.stock_market_activity_legu()
        print(f"获取成功，共 {len(df)} 条记录")
        print(f"字段: {list(df.columns)}")
        print("\n最近3条数据:")
        print(df.tail(3).to_dict(orient='records'))
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False

def test_market_rzrq():
    """测试融资融券数据"""
    print("\n=== 测试融资融券数据 ===")
    try:
        df = ak.stock_margin_sse()
        print(f"获取成功，共 {len(df)} 条记录")
        print(f"字段: {list(df.columns)}")
        print("\n最近3条数据:")
        print(df.tail(3).to_dict(orient='records'))
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False

if __name__ == "__main__":
    test_market_activity()
    test_market_rzrq()
