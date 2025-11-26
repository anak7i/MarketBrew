#!/usr/bin/env python3
"""
测试输出验证器集成
模拟完整的市场分析流程包含验证
"""

import requests
import json
from output_validator import validate_market_analysis, get_fallback_analysis

def test_validation_integration():
    """测试验证器集成"""
    print("🧪 测试输出验证器集成")
    print("=" * 50)
    
    # 模拟AI输出（包含过时数据）
    mock_ai_output = """## 📈 今日市场判断
大盘处于震荡筑底阶段，短期面临3100点压力位，预计维持区间震荡。

## 💰 操作建议
**止损位置**：大盘失守3050点"""
    
    print("🤖 模拟AI原始输出:")
    print(mock_ai_output)
    
    # 进行验证
    validation_result = validate_market_analysis(mock_ai_output)
    
    print(f"\n🔍 验证结果:")
    print(f"   发现过时数据: {validation_result['has_outdated_data']}")
    print(f"   过时内容: {validation_result['outdated_mentions']}")
    print(f"   实时指数: {validation_result['real_index']:.0f}点")
    print(f"   应用修正: {validation_result.get('correction_applied', False)}")
    
    # 判断是否使用备用分析
    if validation_result["has_outdated_data"] and len(validation_result["outdated_mentions"]) > 2:
        print(f"\n⚠️  发现多个过时数据，使用备用分析")
        final_analysis = get_fallback_analysis()
        used_fallback = True
    else:
        print(f"\n✅ 使用修正后的AI输出")
        final_analysis = validation_result["corrected_text"]
        used_fallback = False
    
    print(f"\n📝 最终输出:")
    print("-" * 50)
    print(final_analysis)
    print("-" * 50)
    
    # 构建完整响应
    response = {
        "success": True,
        "market_analysis": final_analysis,
        "validation_info": {
            "had_outdated_data": validation_result["has_outdated_data"],
            "outdated_mentions": validation_result["outdated_mentions"],
            "real_index": validation_result["real_index"],
            "used_fallback": used_fallback,
            "correction_applied": validation_result.get("correction_applied", False)
        }
    }
    
    print(f"\n📊 验证信息:")
    validation_info = response["validation_info"]
    for key, value in validation_info.items():
        print(f"   {key}: {value}")
    
    return response

def test_direct_api_call():
    """测试直接API调用"""
    print(f"\n\n🌐 测试直接API调用:")
    print("=" * 50)
    
    try:
        response = requests.post(
            "http://localhost:5001/api/langchain/market-analysis",
            json={"stocks": [{"symbol": "600519", "name": "贵州茅台"}], "market_status": "trading"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API调用成功")
            
            # 检查是否包含验证信息
            if "validation_info" in data:
                print("✅ 包含验证信息")
                print(f"   过时数据: {data['validation_info'].get('had_outdated_data', 'N/A')}")
                print(f"   实时指数: {data['validation_info'].get('real_index', 'N/A')}")
                print(f"   使用备用: {data['validation_info'].get('used_fallback', 'N/A')}")
            else:
                print("❌ 缺少验证信息")
            
            # 检查输出是否包含过时数据
            analysis = data.get("market_analysis", "")
            if "3100点" in analysis or "3050点" in analysis:
                print("❌ 输出仍包含过时数据")
            else:
                print("✅ 输出没有过时数据")
        else:
            print(f"❌ API调用失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ API调用异常: {e}")

if __name__ == "__main__":
    # 测试验证器本身
    test_validation_integration()
    
    # 测试实际API
    test_direct_api_call()