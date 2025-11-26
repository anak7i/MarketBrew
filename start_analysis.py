#!/usr/bin/env python3
"""
直接启动100只股票分析
"""

from batch_ai_analyzer import BatchAIAnalyzer
import sys

def main():
    print("🚀 启动100只股票AI分析...")
    print("=" * 50)
    
    analyzer = BatchAIAnalyzer()
    
    try:
        results = analyzer.analyze_batch(100)
        print("\n✅ 分析完成!")
        
        # 统计买入卖出信号
        buy_count = 0
        sell_count = 0
        
        for symbol, data in results.items():
            if 'error' in data:
                continue
            analysis = data.get('analysis', '').lower()
            if '买入' in analysis:
                buy_count += 1
            elif '卖出' in analysis:
                sell_count += 1
        
        print(f"🎯 发现交易信号: {buy_count}个买入, {sell_count}个卖出")
        
    except KeyboardInterrupt:
        print("\n⏸️ 分析被用户中断")
    except Exception as e:
        print(f"\n❌ 分析出错: {e}")

if __name__ == "__main__":
    main()