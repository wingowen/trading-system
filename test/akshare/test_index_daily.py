"""
测试大盘指数数据获取功能
对应文档需求: index_daily - 大盘指数日线
"""
import akshare as ak

def test_index_daily():
    """测试大盘指数日线数据"""
    print("\n=== 测试大盘指数日线数据 ===")
    try:
        # 上证指数
        df = ak.stock_zh_index_daily(symbol="sh000001")
        print(f"获取成功，共 {len(df)} 条记录")
        print(f"字段: {list(df.columns)}")
        print("\n前3条数据:")
        print(df.head(3).to_dict(orient='records'))
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False

def test_index_spot():
    """测试主要指数实时行情"""
    print("\n=== 测试主要指数实时行情 ===")
    try:
        df = ak.stock_zh_index_spot_em()
        print(f"获取成功，共 {len(df)} 条记录")
        print(f"字段: {list(df.columns)}")
        print("\n前3条数据:")
        print(df.head(3).to_dict(orient='records'))
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False

if __name__ == "__main__":
    test_index_daily()
    test_index_spot()
