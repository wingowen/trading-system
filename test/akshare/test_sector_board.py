"""
测试板块数据获取功能
对应文档需求: sector_daily - 板块日线数据
"""
import akshare as ak

def test_industry_board():
    """测试行业板块数据"""
    print("\n=== 测试行业板块数据 ===")
    try:
        df = ak.stock_board_industry_name_em()
        print(f"获取成功，共 {len(df)} 条记录")
        print(f"字段: {list(df.columns)}")
        print("\n前3条数据:")
        print(df.head(3).to_dict(orient='records'))
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False

def test_concept_board():
    """测试概念板块数据"""
    print("\n=== 测试概念板块数据 ===")
    try:
        df = ak.stock_board_concept_name_em()
        print(f"获取成功，共 {len(df)} 条记录")
        print(f"字段: {list(df.columns)}")
        print("\n前3条数据:")
        print(df.head(3).to_dict(orient='records'))
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False

def test_board_cons():
    """测试板块成分股数据"""
    print("\n=== 测试板块成分股数据 ===")
    try:
        df = ak.stock_board_industry_cons_em(symbol="半导体")
        print(f"获取成功，共 {len(df)} 条记录")
        print(f"字段: {list(df.columns)}")
        print("\n前3条数据:")
        print(df.head(3).to_dict(orient='records'))
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False

if __name__ == "__main__":
    test_industry_board()
    test_concept_board()
    test_board_cons()
