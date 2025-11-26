#!/usr/bin/env python3
"""
调试AI决策系统的数据流 - 验证传给模型的信息
"""

import requests
from unified_decision_engine import UnifiedDecisionEngine

def test_single_stock_analysis(symbol="000977"):
    """测试单只股票的完整分析流程"""
    
    print(f"\n=== 调试 {symbol} 的分析流程 ===\n")
    
    # 1. 获取实时价格数据
    try:
        response = requests.post(
            "http://localhost:5002/api/stocks",
            json={"symbols": [symbol]},
            timeout=5
        )
        if response.status_code == 200:
            real_time_data = response.json()[symbol]
            print("1. 实时价格数据:")
            print(f"   价格: ¥{real_time_data['current_price']}")
            print(f"   变化: {real_time_data['change_percent']:+.2f}%")
            print(f"   成交量: {real_time_data['volume']:,}手")
        else:
            print("1. 实时价格服务不可用")
            return
    except Exception as e:
        print(f"1. 获取实时数据失败: {e}")
        return
    
    # 2. 初始化决策引擎并分析
    engine = UnifiedDecisionEngine()
    
    # 获取历史数据用于平均成交量计算
    import os, json
    data_file = os.path.join(engine.data_dir, f'daily_prices_{symbol}.json')
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            stock_data = json.load(f)
        
        time_series = stock_data.get('Time Series (Daily)', {})
        recent_dates = sorted(time_series.keys(), reverse=True)[:5]
        
        # 计算平均成交量
        avg_volume = sum([int(time_series[date].get('5. volume', 0)) for date in recent_dates[:3]]) // 3
        
        print(f"\n2. 历史数据 (用于计算平均值):")
        print(f"   最近3日平均成交量: {avg_volume:,}手")
        print(f"   成交量比值: {real_time_data['volume'] / avg_volume:.1f}x")
        
        # 构建prompt
        stock_name = engine.get_stock_name(symbol)
        prompt = engine.build_decision_prompt(
            symbol, 
            stock_name, 
            time_series[recent_dates[0]], 
            recent_dates, 
            time_series,
            real_time_data['current_price'],
            real_time_data['change_percent'], 
            real_time_data['volume']
        )
        
        print(f"\n3. 传给AI模型的完整prompt:")
        print("="*60)
        print(prompt)
        print("="*60)
        
        print(f"\n4. 关键信息总结:")
        print(f"   - 股票: {symbol} ({stock_name})")
        print(f"   - 当前价格: ¥{real_time_data['current_price']:.2f} ({real_time_data['change_percent']:+.1f}%)")
        print(f"   - 当前成交量: {real_time_data['volume']:,}手")
        print(f"   - 平均成交量: {avg_volume:,}手")
        print(f"   - 成交量比率: {real_time_data['volume'] / avg_volume * 100:.1f}%")
        
    except Exception as e:
        print(f"2. 获取历史数据失败: {e}")

if __name__ == "__main__":
    test_single_stock_analysis("000977")  # 浪潮信息
    print("\n" + "="*60)
    test_single_stock_analysis("000001")  # 平安银行