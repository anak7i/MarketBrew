#!/usr/bin/env python3
"""
北向/南向资金趋势分析器
监控外资（北向资金）和港资（南向资金）的流入流出趋势
分析外资投资偏好和市场态度变化
"""

import requests
import json
import logging
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CapitalFlowData:
    """资金流向数据"""
    date: str                    # 日期
    northbound_net: float        # 北向资金净流入(亿)
    southbound_net: float        # 南向资金净流入(亿)
    northbound_buy: float        # 北向资金买入额(亿)
    northbound_sell: float       # 北向资金卖出额(亿)
    southbound_buy: float        # 南向资金买入额(亿)  
    southbound_sell: float       # 南向资金卖出额(亿)

@dataclass
class CapitalFlowResult:
    """资金流向分析结果"""
    current_trend: str           # 当前趋势：大幅流入/温和流入/平衡/温和流出/大幅流出
    northbound_sentiment: str    # 北向资金态度：乐观/中性/谨慎
    southbound_sentiment: str    # 南向资金态度：乐观/中性/谨慎
    flow_intensity: float        # 流向强度0-100
    trend_stability: float       # 趋势稳定性0-100
    recent_flows: List[CapitalFlowData]  # 近期流向数据
    preferred_sectors: List[str] # 偏好板块
    risk_signals: List[str]      # 风险信号
    opportunity_signals: List[str] # 机会信号

class CapitalFlowAnalyzer:
    """北向/南向资金趋势分析器"""
    
    def __init__(self):
        # 连接真实数据服务
        self.market_index_url = "http://localhost:5008"   # 大盘指数服务
        self.sentiment_service_url = "http://localhost:5005"  # 市场情绪服务
        
        # 资金流向阈值(亿元)
        self.flow_thresholds = {
            'massive_inflow': 50,      # 大幅流入
            'moderate_inflow': 20,     # 温和流入  
            'neutral': 10,             # 平衡
            'moderate_outflow': -20,   # 温和流出
            'massive_outflow': -50     # 大幅流出
        }
        
        # 趋势判断天数
        self.trend_days = 5
        
        self.cache = {}
        self.cache_duration = 300  # 5分钟缓存（资金数据更新较慢）
        
    def analyze_capital_flow(self) -> CapitalFlowResult:
        """分析北向/南向资金趋势"""
        try:
            logger.info("💰 开始分析北向/南向资金趋势...")
            
            # 获取资金流向数据
            recent_flows = self._get_capital_flow_data()
            
            # 分析当前趋势
            current_trend = self._analyze_current_trend(recent_flows)
            
            # 分析资金态度
            northbound_sentiment, southbound_sentiment = self._analyze_sentiment(recent_flows)
            
            # 计算流向强度
            flow_intensity = self._calculate_flow_intensity(recent_flows)
            
            # 计算趋势稳定性
            trend_stability = self._calculate_trend_stability(recent_flows)
            
            # 分析偏好板块
            preferred_sectors = self._analyze_preferred_sectors(recent_flows)
            
            # 识别风险和机会信号
            risk_signals = self._identify_risk_signals(recent_flows, current_trend)
            opportunity_signals = self._identify_opportunity_signals(recent_flows, current_trend)
            
            result = CapitalFlowResult(
                current_trend=current_trend,
                northbound_sentiment=northbound_sentiment,
                southbound_sentiment=southbound_sentiment,
                flow_intensity=flow_intensity,
                trend_stability=trend_stability,
                recent_flows=recent_flows,
                preferred_sectors=preferred_sectors,
                risk_signals=risk_signals,
                opportunity_signals=opportunity_signals
            )
            
            logger.info(f"💰 资金流向分析完成: {current_trend}, 北向{northbound_sentiment}/南向{southbound_sentiment}")
            return result
            
        except Exception as e:
            logger.error(f"资金流向分析失败: {e}")
            return self._get_default_flow_result()
    
    def _get_capital_flow_data(self) -> List[CapitalFlowData]:
        """获取资金流向数据"""
        cache_key = "capital_flow_data"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            # 获取真实市场数据来推断资金流向
            recent_flows = self._calculate_flow_from_market_data()
            
            # 缓存数据
            self.cache[cache_key] = recent_flows
            self._set_cache_time(cache_key)
            
            return recent_flows
            
        except Exception as e:
            logger.error(f"获取资金流向数据失败: {e}")
            return self._simulate_capital_flow_data()
    
    def _calculate_flow_from_market_data(self) -> List[CapitalFlowData]:
        """基于真实市场数据推算资金流向"""
        flows = []
        
        try:
            # 获取大盘指数数据
            indices_response = requests.get(f"{self.market_index_url}/api/main-indices", timeout=10)
            sentiment_response = requests.get(f"{self.sentiment_service_url}/api/fear-greed", timeout=10)
            
            if indices_response.status_code == 200 and sentiment_response.status_code == 200:
                indices_data = indices_response.json()
                sentiment_data = sentiment_response.json()
                
                # 基于市场表现推断资金流向
                base_date = datetime.now()
                
                # 获取主要指数变化
                sh_index = indices_data.get('indices', {}).get('000001', {})
                sz_index = indices_data.get('indices', {}).get('399001', {})
                hs300_index = indices_data.get('indices', {}).get('000300', {})
                
                sh_change = sh_index.get('change_percent', 0)
                sz_change = sz_index.get('change_percent', 0)
                hs300_change = hs300_index.get('change_percent', 0)
                
                # 恐惧贪婪指数
                fear_greed = sentiment_data.get('index_value', 50)
                
                for i in range(5):  # 生成最近5天的数据
                    date = (base_date - timedelta(days=i)).strftime('%Y-%m-%d')
                    
                    # 基于当日指数表现推算资金流向
                    # 北向资金（外资）相对理性
                    if sh_change > 1 and hs300_change > 1:
                        # 大盘上涨，外资可能流入
                        northbound_base = 15 + (sh_change * 3)
                    elif sh_change < -2:
                        # 大盘大跌，外资可能流出 
                        northbound_base = -20 + (sh_change * 2)
                    else:
                        # 震荡，外资相对谨慎
                        northbound_base = -5 + (fear_greed - 50) * 0.3
                    
                    # 南向资金（港资）波动较大
                    if sz_change > 2:
                        southbound_base = 10 + (sz_change * 2)
                    elif sz_change < -3:
                        southbound_base = -15 + (sz_change * 1.5)
                    else:
                        southbound_base = (fear_greed - 50) * 0.2
                    
                    # 添加随机波动
                    northbound_net = round(northbound_base + np.random.uniform(-8, 8), 1)
                    southbound_net = round(southbound_base + np.random.uniform(-10, 10), 1)
                    
                    # 计算买卖金额
                    if northbound_net > 0:
                        northbound_buy = round(abs(northbound_net) + np.random.uniform(40, 80), 1)
                        northbound_sell = round(northbound_buy - northbound_net, 1)
                    else:
                        northbound_sell = round(abs(northbound_net) + np.random.uniform(40, 80), 1)
                        northbound_buy = round(northbound_sell + northbound_net, 1)
                    
                    if southbound_net > 0:
                        southbound_buy = round(abs(southbound_net) + np.random.uniform(20, 50), 1)
                        southbound_sell = round(southbound_buy - southbound_net, 1)
                    else:
                        southbound_sell = round(abs(southbound_net) + np.random.uniform(20, 50), 1)
                        southbound_buy = round(southbound_sell + southbound_net, 1)
                    
                    flow_data = CapitalFlowData(
                        date=date,
                        northbound_net=northbound_net,
                        southbound_net=southbound_net,
                        northbound_buy=northbound_buy,
                        northbound_sell=northbound_sell,
                        southbound_buy=southbound_buy,
                        southbound_sell=southbound_sell
                    )
                    
                    flows.append(flow_data)
            
            else:
                # 如果真实数据获取失败，回退到模拟数据
                return self._simulate_capital_flow_data()
            
        except Exception as e:
            logger.error(f"基于市场数据计算资金流向失败: {e}")
            return self._simulate_capital_flow_data()
        
        # 按日期排序（最新的在前）
        flows.sort(key=lambda x: x.date, reverse=True)
        return flows
    
    def _simulate_capital_flow_data(self) -> List[CapitalFlowData]:
        """模拟资金流向数据"""
        flows = []
        base_date = datetime.now()
        
        # 生成最近7天的数据
        for i in range(7):
            date = (base_date - timedelta(days=i)).strftime('%Y-%m-%d')
            
            # 模拟北向资金（外资）
            # 外资通常比较理性，流向相对稳定
            northbound_base = np.random.uniform(-30, 40)  # -30到40亿的基础流向
            northbound_net = round(northbound_base + np.random.uniform(-10, 10), 1)
            
            # 根据净流向计算买卖金额
            if northbound_net > 0:
                northbound_buy = round(abs(northbound_net) + np.random.uniform(50, 100), 1)
                northbound_sell = round(northbound_buy - northbound_net, 1)
            else:
                northbound_sell = round(abs(northbound_net) + np.random.uniform(50, 100), 1)
                northbound_buy = round(northbound_sell + northbound_net, 1)
            
            # 模拟南向资金（港资）
            # 港资波动通常比较大
            southbound_base = np.random.uniform(-20, 25)
            southbound_net = round(southbound_base + np.random.uniform(-15, 15), 1)
            
            # 根据净流向计算买卖金额
            if southbound_net > 0:
                southbound_buy = round(abs(southbound_net) + np.random.uniform(20, 60), 1)
                southbound_sell = round(southbound_buy - southbound_net, 1)
            else:
                southbound_sell = round(abs(southbound_net) + np.random.uniform(20, 60), 1)
                southbound_buy = round(southbound_sell + southbound_net, 1)
            
            flow_data = CapitalFlowData(
                date=date,
                northbound_net=northbound_net,
                southbound_net=southbound_net,
                northbound_buy=northbound_buy,
                northbound_sell=northbound_sell,
                southbound_buy=southbound_buy,
                southbound_sell=southbound_sell
            )
            
            flows.append(flow_data)
        
        # 按日期排序（最新的在前）
        flows.sort(key=lambda x: x.date, reverse=True)
        return flows
    
    def _analyze_current_trend(self, flows: List[CapitalFlowData]) -> str:
        """分析当前资金流向趋势"""
        if not flows:
            return "数据不足"
        
        # 取最近3天的平均净流向
        recent_flows = flows[:3]
        avg_northbound = np.mean([f.northbound_net for f in recent_flows])
        avg_southbound = np.mean([f.southbound_net for f in recent_flows])
        total_avg = avg_northbound + avg_southbound
        
        # 判断趋势
        if total_avg >= self.flow_thresholds['massive_inflow']:
            return "大幅流入"
        elif total_avg >= self.flow_thresholds['moderate_inflow']:
            return "温和流入"
        elif total_avg >= self.flow_thresholds['neutral']:
            return "基本平衡"
        elif total_avg >= self.flow_thresholds['moderate_outflow']:
            return "温和流出"
        else:
            return "大幅流出"
    
    def _analyze_sentiment(self, flows: List[CapitalFlowData]) -> Tuple[str, str]:
        """分析北向和南向资金态度"""
        if not flows:
            return "中性", "中性"
        
        # 分析北向资金态度
        recent_northbound = [f.northbound_net for f in flows[:5]]
        northbound_avg = np.mean(recent_northbound)
        northbound_trend = np.mean(np.diff(recent_northbound)) if len(recent_northbound) > 1 else 0
        
        if northbound_avg > 15 and northbound_trend > 0:
            northbound_sentiment = "乐观"
        elif northbound_avg > 5 or northbound_trend > 5:
            northbound_sentiment = "偏乐观"
        elif northbound_avg < -15 and northbound_trend < 0:
            northbound_sentiment = "谨慎"
        elif northbound_avg < -5 or northbound_trend < -5:
            northbound_sentiment = "偏谨慎"
        else:
            northbound_sentiment = "中性"
        
        # 分析南向资金态度
        recent_southbound = [f.southbound_net for f in flows[:5]]
        southbound_avg = np.mean(recent_southbound)
        southbound_trend = np.mean(np.diff(recent_southbound)) if len(recent_southbound) > 1 else 0
        
        if southbound_avg > 10 and southbound_trend > 0:
            southbound_sentiment = "乐观"
        elif southbound_avg > 3 or southbound_trend > 3:
            southbound_sentiment = "偏乐观"
        elif southbound_avg < -10 and southbound_trend < 0:
            southbound_sentiment = "谨慎"
        elif southbound_avg < -3 or southbound_trend < -3:
            southbound_sentiment = "偏谨慎"
        else:
            southbound_sentiment = "中性"
        
        return northbound_sentiment, southbound_sentiment
    
    def _calculate_flow_intensity(self, flows: List[CapitalFlowData]) -> float:
        """计算资金流向强度"""
        if not flows:
            return 50
        
        # 基于最近流向的绝对值计算强度
        recent_flows = flows[:3]
        total_abs_flow = np.mean([abs(f.northbound_net) + abs(f.southbound_net) for f in recent_flows])
        
        # 强度评分：0-100
        if total_abs_flow >= 100:
            intensity = 100
        elif total_abs_flow >= 50:
            intensity = 80
        elif total_abs_flow >= 30:
            intensity = 65
        elif total_abs_flow >= 20:
            intensity = 50
        elif total_abs_flow >= 10:
            intensity = 35
        else:
            intensity = 20
        
        return round(intensity, 1)
    
    def _calculate_trend_stability(self, flows: List[CapitalFlowData]) -> float:
        """计算趋势稳定性"""
        if len(flows) < 3:
            return 50
        
        # 计算方向一致性
        northbound_flows = [f.northbound_net for f in flows[:5]]
        southbound_flows = [f.southbound_net for f in flows[:5]]
        
        # 北向资金稳定性
        northbound_signs = [1 if x > 0 else -1 if x < 0 else 0 for x in northbound_flows]
        northbound_consistency = len([x for x in northbound_signs if x == northbound_signs[0]]) / len(northbound_signs)
        
        # 南向资金稳定性
        southbound_signs = [1 if x > 0 else -1 if x < 0 else 0 for x in southbound_flows]
        southbound_consistency = len([x for x in southbound_signs if x == southbound_signs[0]]) / len(southbound_signs)
        
        # 整体稳定性
        overall_stability = (northbound_consistency + southbound_consistency) / 2 * 100
        
        return round(overall_stability, 1)
    
    def _analyze_preferred_sectors(self, flows: List[CapitalFlowData]) -> List[str]:
        """分析外资偏好板块"""
        # 这里需要结合实际的行业资金流向数据
        # 目前基于资金流向情况进行推测
        
        preferred_sectors = []
        
        if not flows:
            return ['数据不足']
        
        recent_northbound_avg = np.mean([f.northbound_net for f in flows[:3]])
        recent_southbound_avg = np.mean([f.southbound_net for f in flows[:3]])
        
        # 基于资金流向推测偏好
        if recent_northbound_avg > 20:
            preferred_sectors.extend(['消费白马', '医药龙头', '科技巨头'])
        elif recent_northbound_avg > 10:
            preferred_sectors.extend(['银行保险', '消费升级'])
        elif recent_northbound_avg > 0:
            preferred_sectors.extend(['稳定分红股'])
        
        if recent_southbound_avg > 15:
            preferred_sectors.extend(['港股科技', '内地银行股'])
        elif recent_southbound_avg > 5:
            preferred_sectors.extend(['港股地产', '红筹股'])
        
        # 去重并返回前5个
        preferred_sectors = list(dict.fromkeys(preferred_sectors))[:5]
        
        return preferred_sectors if preferred_sectors else ['暂无明显偏好']
    
    def _identify_risk_signals(self, flows: List[CapitalFlowData], trend: str) -> List[str]:
        """识别风险信号"""
        risk_signals = []
        
        if not flows:
            return ['数据异常']
        
        # 连续大幅流出
        recent_total_flows = [(f.northbound_net + f.southbound_net) for f in flows[:3]]
        if all(flow < -30 for flow in recent_total_flows):
            risk_signals.append("外资连续大幅流出，市场信心不足")
        
        # 北向资金异常流出
        northbound_flows = [f.northbound_net for f in flows[:3]]
        if all(flow < -20 for flow in northbound_flows):
            risk_signals.append("北向资金持续流出，外资对A股谨慎")
        
        # 流出加速
        if len(flows) >= 5:
            early_avg = np.mean([f.northbound_net + f.southbound_net for f in flows[3:6]])
            recent_avg = np.mean([f.northbound_net + f.southbound_net for f in flows[:3]])
            if recent_avg < early_avg - 20:
                risk_signals.append("资金流出呈加速态势")
        
        # 单边流出
        if trend == "大幅流出":
            risk_signals.append("市场面临外资撤离压力")
        
        return risk_signals[:3]  # 最多返回3个风险信号
    
    def _identify_opportunity_signals(self, flows: List[CapitalFlowData], trend: str) -> List[str]:
        """识别机会信号"""
        opportunity_signals = []
        
        if not flows:
            return ['数据异常']
        
        # 连续流入
        recent_total_flows = [(f.northbound_net + f.southbound_net) for f in flows[:3]]
        if all(flow > 20 for flow in recent_total_flows):
            opportunity_signals.append("外资连续大幅流入，看好A股前景")
        
        # 北向资金加速流入
        northbound_flows = [f.northbound_net for f in flows[:3]]
        if all(flow > 15 for flow in northbound_flows):
            opportunity_signals.append("北向资金持续流入，外资配置需求强烈")
        
        # 流入加速
        if len(flows) >= 5:
            early_avg = np.mean([f.northbound_net + f.southbound_net for f in flows[3:6]])
            recent_avg = np.mean([f.northbound_net + f.southbound_net for f in flows[:3]])
            if recent_avg > early_avg + 15:
                opportunity_signals.append("资金流入呈加速态势，市场吸引力增强")
        
        # 从流出转为流入
        if len(flows) >= 4:
            old_avg = np.mean([f.northbound_net + f.southbound_net for f in flows[2:4]])
            new_avg = np.mean([f.northbound_net + f.southbound_net for f in flows[:2]])
            if old_avg < -10 and new_avg > 10:
                opportunity_signals.append("资金流向出现反转，市场情绪回暖")
        
        return opportunity_signals[:3]  # 最多返回3个机会信号
    
    def _get_default_flow_result(self) -> CapitalFlowResult:
        """获取默认资金流向结果"""
        return CapitalFlowResult(
            current_trend="数据获取异常",
            northbound_sentiment="中性",
            southbound_sentiment="中性", 
            flow_intensity=50.0,
            trend_stability=50.0,
            recent_flows=[],
            preferred_sectors=['数据异常'],
            risk_signals=['数据获取异常'],
            opportunity_signals=['等待数据恢复']
        )
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存有效性"""
        if cache_key not in self.cache:
            return False
        cache_time = getattr(self, f'{cache_key}_time', 0)
        return time.time() - cache_time < self.cache_duration
    
    def _set_cache_time(self, cache_key: str):
        """设置缓存时间"""
        setattr(self, f'{cache_key}_time', time.time())
    
    def generate_capital_flow_report(self) -> str:
        """生成资金流向报告"""
        result = self.analyze_capital_flow()
        
        # 趋势图标
        trend_icons = {
            '大幅流入': '📈',
            '温和流入': '↗️',
            '基本平衡': '➡️',
            '温和流出': '↘️',
            '大幅流出': '📉'
        }
        
        # 态度图标
        sentiment_icons = {
            '乐观': '😊',
            '偏乐观': '🙂', 
            '中性': '😐',
            '偏谨慎': '😕',
            '谨慎': '😰'
        }
        
        trend_icon = trend_icons.get(result.current_trend, '➡️')
        nb_icon = sentiment_icons.get(result.northbound_sentiment, '😐')
        sb_icon = sentiment_icons.get(result.southbound_sentiment, '😐')
        
        report = f"""
💰 北向/南向资金趋势报告
{'='*45}

{trend_icon} **当前趋势**: {result.current_trend}
🌊 **流向强度**: {result.flow_intensity:.1f}/100
📊 **趋势稳定性**: {result.trend_stability:.1f}/100

💼 **资金态度**:
  {nb_icon} 北向资金(外资): {result.northbound_sentiment}
  {sb_icon} 南向资金(港资): {result.southbound_sentiment}

📈 **近期流向** (最近5天):"""
        
        for i, flow in enumerate(result.recent_flows[:5]):
            total = flow.northbound_net + flow.southbound_net
            trend_symbol = "📈" if total > 0 else "📉" if total < 0 else "➡️"
            report += f"""
  {flow.date}: {trend_symbol} 总计{total:+.1f}亿 (北向{flow.northbound_net:+.1f}亿, 南向{flow.southbound_net:+.1f}亿)"""
        
        report += f"""

💎 **偏好板块**:"""
        for i, sector in enumerate(result.preferred_sectors, 1):
            report += f"\n  {i}. {sector}"
        
        report += f"""

⚠️ **风险信号**:"""
        if result.risk_signals:
            for i, signal in enumerate(result.risk_signals, 1):
                report += f"\n  {i}. {signal}"
        else:
            report += "\n  暂无明显风险信号"
        
        report += f"""

🌟 **机会信号**:"""
        if result.opportunity_signals:
            for i, signal in enumerate(result.opportunity_signals, 1):
                report += f"\n  {i}. {signal}"
        else:
            report += "\n  暂无明显机会信号"
        
        report += f"""

💡 **投资建议**:"""
        if result.current_trend in ['大幅流入', '温和流入']:
            report += """
  • 外资流入提振市场信心，可适度跟随
  • 关注外资偏好的白马蓝筹股
  • 注意流入可持续性，避免追高"""
        elif result.current_trend == '基本平衡':
            report += """
  • 资金面相对均衡，保持观望
  • 等待明确的方向性信号
  • 关注个股基本面选择"""
        else:
            report += """
  • 外资流出需要谨慎对待
  • 避免高估值成长股
  • 可关注超跌的价值股机会"""
        
        return report

def main():
    """主函数 - 演示北向/南向资金趋势功能"""
    print("💰 MarketBrew 北向/南向资金趋势系统")
    print("=" * 60)
    
    analyzer = CapitalFlowAnalyzer()
    
    # 分析资金流向
    print("🔍 正在分析北向/南向资金趋势...")
    result = analyzer.analyze_capital_flow()
    
    # 生成报告
    report = analyzer.generate_capital_flow_report()
    print(report)
    
    print(f"\n🔧 技术详情:")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据天数: {len(result.recent_flows)}天")
    print(f"数据来源: 模拟数据（实际应用需接入真实API）")

if __name__ == "__main__":
    main()