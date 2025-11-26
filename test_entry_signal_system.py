#!/usr/bin/env python3
"""
进场信号系统测试脚本
测试完整的进场信号分析流程
"""

import requests
import json
from daily_entry_signal_analyzer import DailyEntrySignalAnalyzer
from entry_signal_backtest import EntrySignalBacktester

def test_signal_analyzer():
    """测试信号分析器"""
    print("🧪 测试信号分析器...")
    
    analyzer = DailyEntrySignalAnalyzer()
    result = analyzer.analyze_daily_entry_signal()
    
    print(f"✅ 综合得分: {result['overall_score']}")
    print(f"📊 各维度得分:")
    for dimension, score in result['dimension_scores'].items():
        print(f"  - {dimension}: {score:.1f}")
    print(f"💡 建议: {result['recommendation']['action']}")
    print(f"📝 理由: {result['recommendation']['reason']}")
    
    return result

def test_api_service():
    """测试API服务"""
    print("\n🌐 测试API服务...")
    
    try:
        # 测试健康检查
        response = requests.get('http://localhost:5009/health', timeout=5)
        if response.status_code == 200:
            print("✅ 健康检查通过")
        else:
            print("❌ 健康检查失败")
            return False
        
        # 测试进场信号接口
        response = requests.get('http://localhost:5009/api/entry-signal', timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print("✅ 进场信号接口正常")
                print(f"📊 得分: {data['data']['overall_score']}")
                return True
            else:
                print(f"❌ API返回错误: {data.get('error')}")
                return False
        else:
            print(f"❌ API请求失败: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到API服务 (端口5009)")
        print("💡 请先运行: python3 entry_signal_service.py")
        return False
    except Exception as e:
        print(f"❌ API测试异常: {e}")
        return False

def test_backtest_system():
    """测试回测系统"""
    print("\n🔬 测试回测系统...")
    
    try:
        backtester = EntrySignalBacktester()
        
        # 测试模拟回测
        results = backtester.simulate_historical_backtest(10)
        if 'error' not in results:
            print("✅ 回测系统正常")
            print(f"📈 模拟准确率: {results['accuracy_stats']['overall_accuracy']:.1%}")
            print(f"💰 模拟收益: {results['performance_metrics']['total_return']:.1%}")
            return True
        else:
            print(f"❌ 回测失败: {results['error']}")
            return False
            
    except Exception as e:
        print(f"❌ 回测系统异常: {e}")
        return False

def test_dependencies():
    """测试依赖服务"""
    print("\n🔍 测试依赖服务...")
    
    services = [
        ('市场指数服务', 'http://localhost:5008/health'),
        ('价格服务', 'http://localhost:5002/health')
    ]
    
    all_ok = True
    for name, url in services:
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"✅ {name} 运行正常")
            else:
                print(f"❌ {name} 状态异常: {response.status_code}")
                all_ok = False
        except:
            print(f"❌ {name} 连接失败")
            print(f"💡 请检查服务是否启动: {url}")
            all_ok = False
    
    return all_ok

def main():
    """主测试函数"""
    print("🎯 MarketBrew 进场信号系统完整性测试")
    print("=" * 50)
    
    test_results = []
    
    # 测试依赖服务
    deps_ok = test_dependencies()
    test_results.append(("依赖服务", deps_ok))
    
    # 测试信号分析器
    try:
        signal_result = test_signal_analyzer()
        test_results.append(("信号分析器", True))
    except Exception as e:
        print(f"❌ 信号分析器测试失败: {e}")
        test_results.append(("信号分析器", False))
    
    # 测试API服务
    api_ok = test_api_service()
    test_results.append(("API服务", api_ok))
    
    # 测试回测系统
    backtest_ok = test_backtest_system()
    test_results.append(("回测系统", backtest_ok))
    
    # 汇总结果
    print("\n📋 测试结果汇总:")
    print("=" * 30)
    
    all_passed = True
    for test_name, passed in test_results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name:12}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 30)
    if all_passed:
        print("🎉 所有测试通过! 进场信号系统运行正常")
        print("\n📖 使用指南:")
        print("1. 启动服务: python3 entry_signal_service.py")
        print("2. 访问界面: 打开 ai_decision_center.html")
        print("3. 查看信号: 顶部进场信号面板")
        print("4. 测试回测: python3 entry_signal_backtest.py")
    else:
        print("⚠️ 部分测试失败，请检查相关服务")
        print("\n🔧 故障排除:")
        print("1. 确保所有依赖服务已启动")
        print("2. 检查端口占用 (5002, 5008, 5009)")
        print("3. 验证网络连接")
        print("4. 查看日志文件排查错误")

if __name__ == "__main__":
    main()