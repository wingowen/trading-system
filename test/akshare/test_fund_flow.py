"""
测试资金流数据获取功能
对应文档需求: money_flow - 资金流数据
"""
import akshare as ak

def test_individual_fund_flow():
    """测试个股资金流数据"""
    print("\n=== 测试个股资金流数据 ===")
    try:
        df = ak.stock_individual_fund_flow(stock="000001", market="sh")
        print(f"获取成功，共 {len(df)} 条记录")
        print(f"字段: {list(df.columns)}")
        print("\n前3条数据:")
        print(df.head(3).to_dict(orient='records'))
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False

def test_sector_fund_flow():
    """测试板块资金流数据"""
    print("\n=== 测试板块资金流数据 ===")
    try:
        df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流")
        print(f"获取成功，共 {len(df)} 条记录")
        print(f"字段: {list(df.columns)}")
        print("\n前3条数据:")
        print(df.head(3).to_dict(orient='records'))
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False

if __name__ == "__main__":
    test_individual_fund_flow()
    test_sector_fund_flow()
