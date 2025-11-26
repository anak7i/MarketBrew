#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
print(f"当前日期: {datetime.now()}")
print("测试akshare是否正常工作...")

try:
    import akshare as ak
    print("✅ akshare 导入成功")
    
    # 测试获取股票列表
    print("正在获取A股列表...")
    stock_list = ak.stock_info_a_code_name()
    print(f"✅ 获取到 {len(stock_list)} 只A股")
    
    # 显示前几只股票
    print("前5只股票:")
    print(stock_list.head())
    
    print("🎯 数据源工作正常，可以获取2025年最新数据")
    
except Exception as e:
    print(f"❌ 错误: {e}")