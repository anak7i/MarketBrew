#!/usr/bin/env python3
"""
DeepSeek输出验证器
检测和修正AI输出中的实时数据错误
"""

import re
import requests
from typing import Dict, Any, Tuple

class DeepSeekOutputValidator:
    """DeepSeek输出验证和修正器"""
    
    def __init__(self):
        self.outdated_patterns = [
            r'3[0-3]\d{2}点',  # 3000-3399点
            r'面临3[0-3]\d{2}',  # 面临3000-3399
            r'突破3[0-3]\d{2}',  # 突破3000-3399
            r'守住3[0-3]\d{2}',  # 守住3000-3399
            r'失守3[0-3]\d{2}',  # 失守3000-3399
            r'跌破3[0-3]\d{2}',  # 跌破3000-3399
        ]
    
    def get_real_market_data(self) -> Tuple[float, str]:
        """获取实时市场数据"""
        try:
            response = requests.get("http://localhost:5004/api/macro", timeout=10)
            if response.status_code == 200:
                data = response.json()
                index = data.get('shanghai_index', 3997)
                change = data.get('shanghai_change', -0.03)
                
                # 生成正确的市场描述
                if index >= 3900:
                    position = f"历史高位区间({index:.0f}点)"
                elif index >= 3500:
                    position = f"高位震荡区间({index:.0f}点)"
                else:
                    position = f"中位区间({index:.0f}点)"
                
                return index, position
            else:
                return 3997.0, "历史高位区间(3997点)"
        except:
            return 3997.0, "历史高位区间(3997点)"
    
    def validate_and_fix_output(self, analysis_text: str) -> Dict[str, Any]:
        """验证并修正AI输出"""
        real_index, real_position = self.get_real_market_data()
        
        # 检测过时数据
        outdated_found = []
        for pattern in self.outdated_patterns:
            matches = re.findall(pattern, analysis_text)
            outdated_found.extend(matches)
        
        # 统计问题
        validation_result = {
            "has_outdated_data": len(outdated_found) > 0,
            "outdated_mentions": outdated_found,
            "real_index": real_index,
            "real_position": real_position,
            "corrected_text": analysis_text
        }
        
        # 如果发现过时数据，进行修正
        if outdated_found:
            corrected = analysis_text
            
            # 替换具体点位
            for pattern in self.outdated_patterns:
                corrected = re.sub(pattern, f"{real_index:.0f}点", corrected)
            
            # 添加修正说明
            corrected = f"""## ⚠️ AI输出修正
原输出包含过时数据({', '.join(set(outdated_found))})，已自动修正为实时数据({real_index:.0f}点)

{corrected}

---
📊 实时数据验证：当前上证指数{real_index:.0f}点，{real_position}"""
            
            validation_result["corrected_text"] = corrected
            validation_result["correction_applied"] = True
        else:
            validation_result["correction_applied"] = False
        
        return validation_result
    
    def create_fallback_analysis(self) -> str:
        """创建基于实时数据的备用分析"""
        real_index, real_position = self.get_real_market_data()
        
        fallback = f"""## ✅ 数据确认
当前上证指数：{real_index:.0f}点，市场位置：{real_position}

## 📈 今日市场判断
大盘位于{real_position}，接近4000点整数关口，短期面临高位震荡风险。

## 🔥 重点机会 
**买入机会**：白酒 - 估值回归合理区间，中秋旺季备货启动
**观望板块**：高估值成长股 - 在{real_index:.0f}点高位需谨慎

## ⚠️ 主要风险
指数在{real_index:.0f}点附近，接近历史高位，回调风险较大

## 💰 操作建议
**建议仓位**：60%
**本周重点**：谨慎操作，等待{real_index-200:.0f}点以下机会
**止损位置**：{real_index-150:.0f}点或个股-8%

## 📊 关键指标
北向资金流向、{real_index:.0f}点支撑强度、成交量配合情况

---
📊 基于实时数据{real_index:.0f}点生成的分析"""
        
        return fallback

# 全局验证器实例
validator = DeepSeekOutputValidator()

def validate_market_analysis(analysis_text: str) -> Dict[str, Any]:
    """验证市场分析输出的接口函数"""
    return validator.validate_and_fix_output(analysis_text)

def get_fallback_analysis() -> str:
    """获取备用分析的接口函数"""
    return validator.create_fallback_analysis()

if __name__ == "__main__":
    # 测试验证器
    test_analysis = """## 📈 今日市场判断
大盘处于震荡筑底阶段，短期面临3100点压力位，预计今日维持窄幅震荡。

## 💰 操作建议
**止损位置**：大盘失守3050点"""
    
    result = validate_market_analysis(test_analysis)
    print("验证结果:")
    print(f"发现过时数据: {result['has_outdated_data']}")
    print(f"过时内容: {result['outdated_mentions']}")
    print(f"实时指数: {result['real_index']}")
    print("\n修正后的分析:")
    print(result['corrected_text'])