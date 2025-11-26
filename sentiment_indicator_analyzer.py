#!/usr/bin/env python3
"""
市场情绪指标分析器
基于VIX、恐惧贪婪指数、成交量异动等指标判断市场是否处在极端情绪区域
识别恐慌抄底机会和亢奋减仓信号
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
class SentimentSignal:
    """情绪信号数据"""
    signal_type: str        # 信号类型：恐慌抄底/亢奋减仓/中性观望
    intensity: str          # 信号强度：极强/强/中/弱
    confidence: float       # 信号置信度 0-1
    trigger_factors: List[str]  # 触发因素
    suggested_action: str   # 建议操作
    risk_level: str        # 风险等级

@dataclass
class SentimentIndicatorResult:
    """情绪指标分析结果"""
    fear_greed_level: str         # 恐惧贪婪等级
    fear_greed_score: float       # 恐惧贪婪分数 0-100
    volatility_regime: str        # 波动率环境：低波/常波/高波/极高波
    volume_anomaly: str          # 成交量异常：萎缩/正常/放量/爆量
    sentiment_extremes: List[SentimentSignal]  # 极端情绪信号
    contrarian_signals: List[str]              # 反向信号
    momentum_signals: List[str]                # 趋势信号
    market_regime: str                         # 市场状态：牛市/熊市/震荡
    sentiment_score: float                     # 综合情绪分数 0-100

class SentimentIndicatorAnalyzer:
    """市场情绪指标分析器"""
    
    def __init__(self):
        # 连接数据服务
        self.sentiment_service_url = "http://localhost:5005"
        self.market_index_url = "http://localhost:5008"
        
        # 情绪极值阈值
        self.sentiment_thresholds = {
            'extreme_fear': 20,      # 极度恐慌
            'fear': 35,              # 恐慌
            'neutral': 65,           # 中性
            'greed': 80,             # 贪婪
            'extreme_greed': 95      # 极度贪婪
        }
        
        # 成交量异常阈值
        self.volume_thresholds = {
            'severe_shrink': 0.5,    # 严重萎缩
            'shrink': 0.8,           # 萎缩
            'normal': 1.2,           # 正常
            'surge': 2.0,            # 放量
            'explosive': 3.0         # 爆量
        }
        
        # 波动率阈值
        self.volatility_thresholds = {
            'low': 15,               # 低波动
            'normal': 25,            # 正常波动
            'high': 40,              # 高波动
            'extreme': 60            # 极高波动
        }
        
        self.cache = {}
        self.cache_duration = 180  # 3分钟缓存
        
    def analyze_sentiment_indicators(self) -> SentimentIndicatorResult:
        """分析市场情绪指标"""
        try:
            logger.info("🎭 开始分析市场情绪指标...")
            
            # 获取基础数据
            sentiment_data = self._get_sentiment_data()
            market_data = self._get_market_data()
            
            # 分析恐惧贪婪指数
            fear_greed_level, fear_greed_score = self._analyze_fear_greed(sentiment_data)
            
            # 分析波动率环境
            volatility_regime = self._analyze_volatility_regime(sentiment_data, market_data)
            
            # 分析成交量异常
            volume_anomaly = self._analyze_volume_anomaly(market_data)
            
            # 识别极端情绪信号
            sentiment_extremes = self._identify_sentiment_extremes(
                sentiment_data, market_data, fear_greed_score
            )
            
            # 生成反向信号
            contrarian_signals = self._generate_contrarian_signals(
                fear_greed_score, volatility_regime, volume_anomaly
            )
            
            # 生成趋势信号
            momentum_signals = self._generate_momentum_signals(
                sentiment_data, market_data
            )
            
            # 判断市场状态
            market_regime = self._determine_market_regime(sentiment_data, market_data)
            
            # 计算综合情绪分数
            sentiment_score = self._calculate_sentiment_score(
                fear_greed_score, volatility_regime, volume_anomaly, market_data
            )
            
            result = SentimentIndicatorResult(
                fear_greed_level=fear_greed_level,
                fear_greed_score=fear_greed_score,
                volatility_regime=volatility_regime,
                volume_anomaly=volume_anomaly,
                sentiment_extremes=sentiment_extremes,
                contrarian_signals=contrarian_signals,
                momentum_signals=momentum_signals,
                market_regime=market_regime,
                sentiment_score=sentiment_score
            )
            
            logger.info(f"🎭 情绪指标分析完成: {fear_greed_level}({fear_greed_score:.1f}) - {market_regime}")
            return result
            
        except Exception as e:
            logger.error(f"情绪指标分析失败: {e}")
            return self._get_default_sentiment_result()
    
    def _get_sentiment_data(self) -> Dict:
        """获取情绪数据"""
        cache_key = "sentiment_indicator_data"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            sentiment_data = {}
            
            # 获取恐惧贪婪指数
            response = requests.get(f"{self.sentiment_service_url}/api/fear-greed", timeout=10)
            if response.status_code == 200:
                fear_greed_data = response.json()
                sentiment_data['fear_greed'] = fear_greed_data
            
            # 获取市场情绪
            response = requests.get(f"{self.sentiment_service_url}/api/market-sentiment", timeout=10)
            if response.status_code == 200:
                market_sentiment = response.json()
                sentiment_data['market_sentiment'] = market_sentiment
            
            # 缓存数据
            self.cache[cache_key] = sentiment_data
            self._set_cache_time(cache_key)
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"获取情绪数据失败: {e}")
            return {}
    
    def _get_market_data(self) -> Dict:
        """获取市场数据"""
        cache_key = "sentiment_market_data"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            market_data = {}
            
            # 获取主要指数数据
            response = requests.get(f"{self.market_index_url}/api/main-indices", timeout=10)
            if response.status_code == 200:
                indices_data = response.json()
                market_data.update(indices_data)
            
            # 缓存数据
            self.cache[cache_key] = market_data
            self._set_cache_time(cache_key)
            
            return market_data
            
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return {}
    
    def _analyze_fear_greed(self, sentiment_data: Dict) -> Tuple[str, float]:
        """分析恐惧贪婪指数"""
        fear_greed = sentiment_data.get('fear_greed', {})
        score = fear_greed.get('index_value', 50)
        
        if score <= self.sentiment_thresholds['extreme_fear']:
            level = "极度恐慌"
        elif score <= self.sentiment_thresholds['fear']:
            level = "恐慌"
        elif score <= self.sentiment_thresholds['neutral']:
            level = "中性"
        elif score <= self.sentiment_thresholds['greed']:
            level = "贪婪"
        else:
            level = "极度贪婪"
        
        return level, score
    
    def _analyze_volatility_regime(self, sentiment_data: Dict, market_data: Dict) -> str:
        """分析波动率环境"""
        # 基于市场变化和情绪数据估算波动率
        indices = market_data.get('indices', {})
        
        if indices:
            # 计算主要指数的平均波动
            changes = [abs(index.get('change_percent', 0)) for index in indices.values()]
            avg_volatility = np.mean(changes) if changes else 0
            
            # 转换为年化波动率概念（简化）
            volatility_proxy = avg_volatility * 16  # 大致转换
            
            if volatility_proxy <= self.volatility_thresholds['low']:
                return "低波动环境"
            elif volatility_proxy <= self.volatility_thresholds['normal']:
                return "正常波动"
            elif volatility_proxy <= self.volatility_thresholds['high']:
                return "高波动环境"
            else:
                return "极高波动"
        
        return "无法确定"
    
    def _analyze_volume_anomaly(self, market_data: Dict) -> str:
        """分析成交量异常"""
        indices = market_data.get('indices', {})
        
        if indices:
            # 基于成交量数据分析（如果有的话）
            volumes = [index.get('volume', 0) for index in indices.values()]
            avg_volume = np.mean(volumes) if volumes else 0
            
            # 简化的成交量异常判断（需要历史基准数据）
            if avg_volume == 0:
                return "成交萎缩"
            elif avg_volume < 50:  # 假设的阈值
                return "量能不足"
            elif avg_volume > 200:  # 假设的阈值
                return "放量明显"
            else:
                return "成交正常"
        
        return "成交萎缩"  # 默认值
    
    def _identify_sentiment_extremes(self, sentiment_data: Dict, market_data: Dict, 
                                   fear_greed_score: float) -> List[SentimentSignal]:
        """识别极端情绪信号"""
        extremes = []
        
        # 极度恐慌信号
        if fear_greed_score <= self.sentiment_thresholds['extreme_fear']:
            signal = SentimentSignal(
                signal_type="恐慌抄底",
                intensity="极强",
                confidence=0.8,
                trigger_factors=["恐惧贪婪指数极低", "市场出现超卖"],
                suggested_action="分批抄底优质标的",
                risk_level="中等"
            )
            extremes.append(signal)
        
        # 极度贪婪信号
        elif fear_greed_score >= self.sentiment_thresholds['extreme_greed']:
            signal = SentimentSignal(
                signal_type="亢奋减仓",
                intensity="极强", 
                confidence=0.8,
                trigger_factors=["恐惧贪婪指数极高", "市场过度乐观"],
                suggested_action="逐步减仓控制风险",
                risk_level="高"
            )
            extremes.append(signal)
        
        # 恐慌信号
        elif fear_greed_score <= self.sentiment_thresholds['fear']:
            signal = SentimentSignal(
                signal_type="恐慌抄底",
                intensity="强",
                confidence=0.6,
                trigger_factors=["市场悲观情绪浓厚"],
                suggested_action="关注抄底机会",
                risk_level="中等"
            )
            extremes.append(signal)
        
        # 贪婪信号
        elif fear_greed_score >= self.sentiment_thresholds['greed']:
            signal = SentimentSignal(
                signal_type="亢奋减仓",
                intensity="中",
                confidence=0.5,
                trigger_factors=["市场乐观情绪高涨"],
                suggested_action="适度控制仓位",
                risk_level="中等"
            )
            extremes.append(signal)
        
        return extremes
    
    def _generate_contrarian_signals(self, fear_greed_score: float, 
                                   volatility_regime: str, volume_anomaly: str) -> List[str]:
        """生成反向投资信号"""
        signals = []
        
        # 恐慌时的反向信号
        if fear_greed_score <= 25:
            signals.append("市场极度悲观，反向投资机会出现")
            if "萎缩" in volume_anomaly:
                signals.append("恐慌性抛售接近尾声，关注反弹")
        
        # 贪婪时的反向信号  
        if fear_greed_score >= 75:
            signals.append("市场过度乐观，警惕反转风险")
            if "放量" in volume_anomaly:
                signals.append("追涨情绪高涨，注意获利了结")
        
        # 波动率信号
        if "极高波动" in volatility_regime:
            signals.append("波动率飙升，市场情绪极端化")
        
        return signals
    
    def _generate_momentum_signals(self, sentiment_data: Dict, market_data: Dict) -> List[str]:
        """生成趋势跟随信号"""
        signals = []
        
        indices = market_data.get('indices', {})
        if indices:
            # 分析市场趋势
            positive_changes = [idx for idx in indices.values() if idx.get('change_percent', 0) > 0]
            negative_changes = [idx for idx in indices.values() if idx.get('change_percent', 0) < 0]
            
            if len(positive_changes) > len(negative_changes):
                signals.append("主要指数普涨，趋势向上")
            elif len(negative_changes) > len(positive_changes):
                signals.append("主要指数普跌，趋势向下")
            else:
                signals.append("指数分化明显，震荡为主")
        
        return signals
    
    def _determine_market_regime(self, sentiment_data: Dict, market_data: Dict) -> str:
        """判断市场状态"""
        fear_greed = sentiment_data.get('fear_greed', {}).get('index_value', 50)
        
        indices = market_data.get('indices', {})
        if indices:
            avg_change = np.mean([idx.get('change_percent', 0) for idx in indices.values()])
            
            if avg_change > 1 and fear_greed > 60:
                return "牛市氛围"
            elif avg_change < -1 and fear_greed < 40:
                return "熊市氛围"  
            else:
                return "震荡市"
        
        return "震荡市"
    
    def _calculate_sentiment_score(self, fear_greed_score: float, volatility_regime: str,
                                 volume_anomaly: str, market_data: Dict) -> float:
        """计算综合情绪分数"""
        # 基础分数来自恐惧贪婪指数
        base_score = fear_greed_score
        
        # 波动率调整
        if "极高波动" in volatility_regime:
            base_score -= 10  # 高波动降低情绪分数
        elif "低波动" in volatility_regime:
            base_score += 5   # 低波动提升情绪分数
        
        # 成交量调整
        if "萎缩" in volume_anomaly:
            base_score -= 5   # 成交萎缩降低分数
        elif "放量" in volume_anomaly:
            base_score += 5   # 放量提升分数
        
        # 确保分数在0-100范围内
        return max(0, min(100, base_score))
    
    def _get_default_sentiment_result(self) -> SentimentIndicatorResult:
        """获取默认情绪指标结果"""
        return SentimentIndicatorResult(
            fear_greed_level="中性",
            fear_greed_score=50.0,
            volatility_regime="正常波动",
            volume_anomaly="成交正常",
            sentiment_extremes=[],
            contrarian_signals=["数据获取异常"],
            momentum_signals=["等待数据恢复"],
            market_regime="震荡市",
            sentiment_score=50.0
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
    
    def generate_sentiment_report(self) -> str:
        """生成情绪指标报告"""
        result = self.analyze_sentiment_indicators()
        
        report = f"""
🎭 市场情绪指标分析报告
{'='*50}

⏰ **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

😨 **恐惧贪婪指数**: {result.fear_greed_score:.1f}/100 ({result.fear_greed_level})

📊 **市场环境**:
  • 波动率状态: {result.volatility_regime}
  • 成交量状态: {result.volume_anomaly}
  • 市场状态: {result.market_regime}
  • 综合情绪: {result.sentiment_score:.1f}/100

🚨 **极端情绪信号** ({len(result.sentiment_extremes)}个):"""
        
        if result.sentiment_extremes:
            for i, signal in enumerate(result.sentiment_extremes, 1):
                report += f"""
  {i}. [{signal.signal_type}] 强度:{signal.intensity} 置信度:{signal.confidence:.1%}
     • 建议: {signal.suggested_action}
     • 风险: {signal.risk_level}
     • 原因: {', '.join(signal.trigger_factors)}"""
        else:
            report += "\n  暂无极端情绪信号"
        
        report += f"\n\n🔄 **反向投资信号**:"
        if result.contrarian_signals:
            for i, signal in enumerate(result.contrarian_signals, 1):
                report += f"\n  {i}. {signal}"
        else:
            report += "\n  暂无明显反向信号"
        
        report += f"\n\n📈 **趋势信号**:"
        if result.momentum_signals:
            for i, signal in enumerate(result.momentum_signals, 1):
                report += f"\n  {i}. {signal}"
        else:
            report += "\n  暂无明显趋势信号"
        
        report += f"""

💡 **投资建议**:"""
        
        if result.fear_greed_score <= 25:
            report += """
  • 市场处于恐慌区域，考虑分批抄底
  • 关注优质标的的超跌机会
  • 控制风险，分散投资"""
        elif result.fear_greed_score >= 75:
            report += """
  • 市场处于贪婪区域，注意获利了结
  • 减少追高行为，控制仓位
  • 关注反转风险信号"""
        else:
            report += """
  • 市场情绪相对平衡
  • 以基本面选股为主
  • 保持适度仓位，等待明确信号"""
        
        return report

def main():
    """主函数 - 演示情绪指标分析功能"""
    print("🎭 MarketBrew 市场情绪指标分析系统")
    print("=" * 60)
    
    analyzer = SentimentIndicatorAnalyzer()
    
    # 分析情绪指标
    print("🔍 正在分析市场情绪指标...")
    result = analyzer.analyze_sentiment_indicators()
    
    # 生成报告
    report = analyzer.generate_sentiment_report()
    print(report)
    
    print(f"\n🔧 技术详情:")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"情绪极端信号: {len(result.sentiment_extremes)}个")
    print(f"数据来源: 真实市场数据 + 情绪服务")

if __name__ == "__main__":
    main()