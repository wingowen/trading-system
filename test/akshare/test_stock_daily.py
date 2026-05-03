"""
测试个股日线数据获取功能
对应文档需求: stock_daily - 个股日线数据
"""
import akshare as ak
import json
from datetime import datetime

def test_stock_daily():
    """测试获取个股日线数据"""
    print("\n=== 测试个股日线数据 ===")
    try:
        # 获取平安银行日线数据
        df = ak.stock_zh_a_hist(
            symbol="000001", 
            period="daily", 
            start_date="20260401", 
            end_date="20260503", 
            adjust="qfq"
        )
        
        print(f"获取成功，共 {len(df)} 条记录")
        print(f"字段: {list(df.columns)}")
        print("\n前3条数据:")
        print(df.head(3).to_dict(orient='records'))
        
        # 验证必要字段
        required_fields = ['日期', '开盘', '收盘', '最高', '最低', '成交量', '成交额', '换手率']
        actual_fields = list(df.columns)
        missing = [f for f in required_fields if f not in actual_fields]
        if missing:
            print(f"\n警告: 缺少字段 {missing}")
        else:
            print("\n所有必要字段都存在")
            
        return True
    except Exception as e:
        print(f"失败: {e}")
        return False

if __name__ == "__main__":
    test_stock_daily()
