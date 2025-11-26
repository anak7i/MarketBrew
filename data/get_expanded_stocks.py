#!/usr/bin/env python3
"""
扩展股票池数据获取脚本
支持多个指数的股票数据获取
"""

import akshare as ak
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time

def get_index_stocks(index_code: str, index_name: str):
    """获取指数成分股列表"""
    try:
        print(f"正在获取{index_name}成分股...")
        stocks = ak.index_stock_cons(symbol=index_code)
        print(f"✅ {index_name}: {len(stocks)}只股票")
        # 获取股票代码列，尝试不同的列名
        if '品种代码' in stocks.columns:
            return stocks['品种代码'].tolist()
        elif '代码' in stocks.columns:
            return stocks['代码'].tolist()
        elif 'code' in stocks.columns:
            return stocks['code'].tolist()
        else:
            print(f"可用列名: {stocks.columns.tolist()}")
            return stocks.iloc[:, 0].tolist()  # 使用第一列
    except Exception as e:
        print(f"❌ 获取{index_name}失败: {e}")
        return []

def get_all_stock_pools():
    """获取所有可选股票池"""
    stock_pools = {}
    
    # 沪深300
    stock_pools['hs300'] = get_index_stocks("000300", "沪深300")
    
    # 中证500  
    stock_pools['zz500'] = get_index_stocks("000905", "中证500")
    
    # 创业板指
    stock_pools['cyb'] = get_index_stocks("399006", "创业板指")
    
    # 科创50
    stock_pools['kc50'] = get_index_stocks("000688", "科创50")
    
    return stock_pools

def create_combined_pool(pools: dict, selection: dict):
    """创建组合股票池"""
    combined = []
    
    for pool_name, count in selection.items():
        if pool_name in pools:
            pool_stocks = pools[pool_name][:count]
            combined.extend(pool_stocks)
            print(f"添加 {pool_name}: {len(pool_stocks)}只")
    
    # 去重
    unique_stocks = list(set(combined))
    print(f"去重后总计: {len(unique_stocks)}只股票")
    
    return unique_stocks

def save_stock_pool_config(stocks: list, name: str):
    """保存股票池配置"""
    config = {
        "name": name,
        "update_time": datetime.now().isoformat(),
        "total_count": len(stocks),
        "stocks": stocks
    }
    
    filename = f"stock_pool_{name}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 股票池配置已保存: {filename}")

if __name__ == "__main__":
    print("🚀 开始获取扩展股票池...")
    
    # 获取所有指数成分股
    all_pools = get_all_stock_pools()
    
    # 方案一：平衡型 (推荐)
    balanced_selection = {
        'hs300': 300,  # 沪深300全部
        'cyb': 100,    # 创业板指全部  
        'kc50': 50     # 科创50全部
    }
    balanced_stocks = create_combined_pool(all_pools, balanced_selection)
    save_stock_pool_config(balanced_stocks, "balanced")
    
    # 方案二：全市场型
    full_market_selection = {
        'hs300': 300,  # 沪深300
        'zz500': 500,  # 中证500
        'kc50': 50     # 科创50
    }
    full_market_stocks = create_combined_pool(all_pools, full_market_selection)
    save_stock_pool_config(full_market_stocks, "full_market")
    
    # 方案三：高成长型
    growth_selection = {
        'zz500': 500,  # 中证500
        'cyb': 100,    # 创业板指
        'kc50': 50     # 科创50
    }
    growth_stocks = create_combined_pool(all_pools, growth_selection)
    save_stock_pool_config(growth_stocks, "growth")
    
    print("🎉 所有股票池配置生成完成！")
    print("\n📊 可选方案:")
    print(f"1. 平衡型: {len(balanced_stocks)}只股票")
    print(f"2. 全市场型: {len(full_market_stocks)}只股票") 
    print(f"3. 高成长型: {len(growth_stocks)}只股票")