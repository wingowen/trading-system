"""
测试新增的 skill 功能
"""
import akshare as ak

def test_index_data_fetcher():
    """测试 index-data-fetcher skill"""
    print("\n=== 测试 index-data-fetcher ===")
    try:
        # 测试获取上证指数日线数据
        df = ak.stock_zh_index_daily(symbol="sh000001")
        print(f"上证指数日线数据获取成功，共 {len(df)} 条记录")
        print(f"字段: {list(df.columns)}")
        print("\n最近3条数据:")
        print(df.tail(3).to_dict(orient='records'))
        
        # 测试获取主要指数实时行情
        df_spot = ak.stock_zh_index_spot_em()
        print(f"\n主要指数实时行情获取成功，共 {len(df_spot)} 条记录")
        print(f"字段: {list(df_spot.columns)}")
        
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False

def test_market_sentiment_fetcher():
    """测试 market-sentiment-fetcher skill"""
    print("\n=== 测试 market-sentiment-fetcher ===")
    try:
        # 测试获取市场活跃度数据
        df = ak.stock_market_activity_legu()
        print(f"市场活跃度数据获取成功，共 {len(df)} 条记录")
        print(f"字段: {list(df.columns)}")
        print("\n最近数据:")
        print(df.tail(3).to_dict(orient='records'))
        
        # 测试获取融资融券数据
        df_margin = ak.stock_margin_sse()
        print(f"\n融资融券数据获取成功，共 {len(df_margin)} 条记录")
        print(f"字段: {list(df_margin.columns)}")
        
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False

if __name__ == "__main__":
    results = {}
    results["index-data-fetcher"] = test_index_data_fetcher()
    results["market-sentiment-fetcher"] = test_market_sentiment_fetcher()
    
    print("\n\n=== 新增 Skill 测试结果汇总 ===")
    for name, success in results.items():
        status = "成功" if success else "失败"
        print(f"{name}: {status}")
