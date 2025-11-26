#!/usr/bin/env python3
"""
市场情绪反转信号分析器
基于量能变化和波动率特征识别情绪反转时机
主要识别：
1. 恐慌性抛售的尾声（量能萎缩 + 低价高波动）
2. 亢奋情绪的顶部（量能爆发 + 高价低波动）
3. 情绪修复的开始（波动率回落 + 量价配合）
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
class VolumeSignal:
    """量能信号"""
    signal_type: str        # 放量/缩量/爆量/地量
    volume_ratio: float     # 量比
    price_volume_sync: str  # 量价配合情况
    trend_confirmation: bool # 趋势确认

@dataclass
class VolatilitySignal:
    """波动率信号"""
    vix_level: str          # 波动率水平：低/正常/高/极高
    vix_trend: str          # 波动率趋势：上升/下降/震荡
    fear_peak: bool         # 是否恐慌峰值
    complacency_valley: bool # 是否自满谷底

@dataclass
class ReversalSignal:
    """反转信号"""
    signal_type: str        # 见底/见顶/修复/分化
    reversal_phase: str     # 反转阶段：初期/中期/尾期
    confidence: float       # 信号置信度
    time_window: str        # 时间窗口：短期/中期/长期
    trigger_factors: List[str] # 触发因素
    suggested_strategy: str # 建议策略

@dataclass
class SentimentReversalResult:
    """情绪反转分析结果"""
    volume_signal: VolumeSignal      # 量能信号
    volatility_signal: VolatilitySignal # 波动率信号  
    reversal_signals: List[ReversalSignal] # 反转信号列表
    market_phase: str                # 市场阶段：底部构建/顶部形成/趋势延续/震荡整理
    sentiment_momentum: str          # 情绪动量：转强/转弱/维持/分化
    risk_reward_ratio: float         # 风险收益比
    position_advice: str             # 仓位建议

class SentimentReversalAnalyzer:
    """情绪反转信号分析器"""
    
    def __init__(self):
        # 连接数据服务
        self.sentiment_service_url = "http://localhost:5005"
        self.market_index_url = "http://localhost:5008"
        
        # 量能阈值
        self.volume_thresholds = {
            'ground_volume': 0.3,     # 地量
            'shrink_volume': 0.7,     # 缩量
            'normal_volume': 1.3,     # 正常
            'surge_volume': 2.0,      # 放量
            'explosive_volume': 3.5   # 爆量
        }
        
        # 波动率阈值（基于VIX概念）
        self.volatility_thresholds = {
            'low_vix': 12,           # 低波动率（自满）
            'normal_vix': 20,        # 正常波动率
            'high_vix': 30,          # 高波动率（紧张）
            'extreme_vix': 50        # 极高波动率（恐慌）
        }
        
        # 反转信号置信度阈值
        self.confidence_thresholds = {
            'strong': 0.8,           # 强信号
            'medium': 0.6,           # 中等信号
            'weak': 0.4              # 弱信号
        }
        
        self.cache = {}
        self.cache_duration = 240  # 4分钟缓存
        
    def analyze_sentiment_reversal(self) -> SentimentReversalResult:
        """分析情绪反转信号"""
        try:
            logger.info("🔄 开始分析情绪反转信号...")
            
            # 获取数据
            market_data = self._get_market_data()
            sentiment_data = self._get_sentiment_data()
            volume_data = self._analyze_volume_patterns(market_data)
            
            # 分析量能信号
            volume_signal = self._analyze_volume_signal(volume_data, market_data)
            
            # 分析波动率信号
            volatility_signal = self._analyze_volatility_signal(sentiment_data, market_data)
            
            # 识别反转信号
            reversal_signals = self._identify_reversal_signals(
                volume_signal, volatility_signal, market_data, sentiment_data
            )
            
            # 判断市场阶段
            market_phase = self._determine_market_phase(
                volume_signal, volatility_signal, market_data
            )
            
            # 分析情绪动量
            sentiment_momentum = self._analyze_sentiment_momentum(
                volume_signal, volatility_signal, sentiment_data
            )
            
            # 计算风险收益比
            risk_reward_ratio = self._calculate_risk_reward_ratio(
                reversal_signals, market_phase
            )
            
            # 生成仓位建议
            position_advice = self._generate_position_advice(
                reversal_signals, market_phase, risk_reward_ratio
            )
            
            result = SentimentReversalResult(
                volume_signal=volume_signal,
                volatility_signal=volatility_signal,
                reversal_signals=reversal_signals,
                market_phase=market_phase,
                sentiment_momentum=sentiment_momentum,
                risk_reward_ratio=risk_reward_ratio,
                position_advice=position_advice
            )
            
            logger.info(f"🔄 情绪反转分析完成: {market_phase} - {len(reversal_signals)}个反转信号")
            return result
            
        except Exception as e:
            logger.error(f"情绪反转分析失败: {e}")
            return self._get_default_reversal_result()
    
    def _get_market_data(self) -> Dict:
        """获取市场数据"""
        cache_key = "reversal_market_data"
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
    
    def _get_sentiment_data(self) -> Dict:
        """获取情绪数据"""
        cache_key = "reversal_sentiment_data"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            sentiment_data = {}
            
            # 获取恐惧贪婪指数
            response = requests.get(f"{self.sentiment_service_url}/api/fear-greed", timeout=10)
            if response.status_code == 200:
                fear_greed_data = response.json()
                sentiment_data['fear_greed'] = fear_greed_data
            
            # 缓存数据
            self.cache[cache_key] = sentiment_data
            self._set_cache_time(cache_key)
            
            return sentiment_data
            
        except Exception as e:
            logger.error(f"获取情绪数据失败: {e}")
            return {}
    
    def _analyze_volume_patterns(self, market_data: Dict) -> Dict:
        """分析成交量模式"""
        volume_data = {'total_volume': 0, 'avg_volume': 0, 'volume_trend': 'unknown'}
        
        indices = market_data.get('indices', {})
        if indices:
            volumes = []
            for index_data in indices.values():
                volume = index_data.get('volume', 0)
                if volume > 0:
                    volumes.append(volume)
            
            if volumes:
                volume_data['total_volume'] = sum(volumes)
                volume_data['avg_volume'] = np.mean(volumes)
                
                # 简化的成交量趋势判断
                # 在实际应用中，这里应该使用历史数据进行对比
                if volume_data['avg_volume'] > 100:  # 假设阈值
                    volume_data['volume_trend'] = 'increasing'
                elif volume_data['avg_volume'] < 50:
                    volume_data['volume_trend'] = 'decreasing'
                else:
                    volume_data['volume_trend'] = 'stable'
        
        return volume_data
    
    def _analyze_volume_signal(self, volume_data: Dict, market_data: Dict) -> VolumeSignal:
        """分析量能信号"""
        avg_volume = volume_data.get('avg_volume', 0)
        volume_trend = volume_data.get('volume_trend', 'unknown')
        
        # 量比计算（简化版本，实际需要历史基准）
        baseline_volume = 75  # 假设的基准量
        volume_ratio = avg_volume / baseline_volume if baseline_volume > 0 else 1.0
        
        # 判断量能类型
        if volume_ratio <= self.volume_thresholds['ground_volume']:
            signal_type = "地量"
        elif volume_ratio <= self.volume_thresholds['shrink_volume']:
            signal_type = "缩量"
        elif volume_ratio <= self.volume_thresholds['normal_volume']:
            signal_type = "正常量"
        elif volume_ratio <= self.volume_thresholds['surge_volume']:
            signal_type = "放量"
        else:
            signal_type = "爆量"
        
        # 分析量价配合
        indices = market_data.get('indices', {})
        if indices:
            price_changes = [idx.get('change_percent', 0) for idx in indices.values()]
            avg_change = np.mean(price_changes)
            
            if avg_change > 1 and signal_type in ["放量", "爆量"]:
                price_volume_sync = "量价齐升"
            elif avg_change < -1 and signal_type in ["放量", "爆量"]:
                price_volume_sync = "放量下跌"
            elif avg_change > 0 and signal_type in ["缩量", "地量"]:
                price_volume_sync = "缩量上涨"
            elif avg_change < 0 and signal_type in ["缩量", "地量"]:
                price_volume_sync = "缩量下跌"
            else:
                price_volume_sync = "量价背离"
        else:
            price_volume_sync = "无法判断"
        
        # 趋势确认
        trend_confirmation = (
            (price_volume_sync in ["量价齐升", "缩量上涨"]) or
            (signal_type in ["放量", "爆量"] and volume_trend == "increasing")
        )
        
        return VolumeSignal(
            signal_type=signal_type,
            volume_ratio=volume_ratio,
            price_volume_sync=price_volume_sync,
            trend_confirmation=trend_confirmation
        )
    
    def _analyze_volatility_signal(self, sentiment_data: Dict, market_data: Dict) -> VolatilitySignal:
        """分析波动率信号"""
        # 基于恐惧贪婪指数和市场变化估算VIX水平
        fear_greed = sentiment_data.get('fear_greed', {}).get('index_value', 50)
        
        # 计算市场波动（简化版VIX）
        indices = market_data.get('indices', {})
        if indices:
            changes = [abs(idx.get('change_percent', 0)) for idx in indices.values()]
            market_volatility = np.mean(changes) * 15  # 粗略转换为VIX概念
        else:
            market_volatility = 20
        
        # 结合恐惧贪婪指数调整波动率
        if fear_greed < 25:  # 恐慌时波动率通常较高
            adjusted_vix = market_volatility * 1.5
        elif fear_greed > 75:  # 贪婪时波动率通常较低
            adjusted_vix = market_volatility * 0.8
        else:
            adjusted_vix = market_volatility
        
        # 判断VIX水平
        if adjusted_vix <= self.volatility_thresholds['low_vix']:
            vix_level = "低波动率"
        elif adjusted_vix <= self.volatility_thresholds['normal_vix']:
            vix_level = "正常波动率"
        elif adjusted_vix <= self.volatility_thresholds['high_vix']:
            vix_level = "高波动率"
        else:
            vix_level = "极高波动率"
        
        # 判断波动率趋势（简化）
        if fear_greed < 30 and adjusted_vix > 25:
            vix_trend = "急速上升"
        elif fear_greed > 70 and adjusted_vix < 15:
            vix_trend = "持续下降"
        else:
            vix_trend = "震荡"
        
        # 识别恐慌峰值和自满谷底
        fear_peak = (fear_greed < 20 and adjusted_vix > 35)
        complacency_valley = (fear_greed > 80 and adjusted_vix < 12)
        
        return VolatilitySignal(
            vix_level=vix_level,
            vix_trend=vix_trend,
            fear_peak=fear_peak,
            complacency_valley=complacency_valley
        )
    
    def _identify_reversal_signals(self, volume_signal: VolumeSignal, 
                                  volatility_signal: VolatilitySignal,
                                  market_data: Dict, sentiment_data: Dict) -> List[ReversalSignal]:
        """识别反转信号"""
        signals = []
        
        fear_greed = sentiment_data.get('fear_greed', {}).get('index_value', 50)
        
        # 恐慌见底信号
        if (volatility_signal.fear_peak and 
            volume_signal.signal_type in ["地量", "缩量"] and
            fear_greed < 25):
            signal = ReversalSignal(
                signal_type="恐慌见底",
                reversal_phase="初期",
                confidence=0.7,
                time_window="短期",
                trigger_factors=["恐慌情绪达到极值", "量能萎缩至地量", "波动率处于高位"],
                suggested_strategy="分批建仓，等待确认"
            )
            signals.append(signal)
        
        # 亢奋见顶信号
        if (volatility_signal.complacency_valley and 
            volume_signal.signal_type in ["爆量"] and
            fear_greed > 75):
            signal = ReversalSignal(
                signal_type="亢奋见顶",
                reversal_phase="中期",
                confidence=0.6,
                time_window="中期",
                trigger_factors=["贪婪情绪过度", "成交量爆发", "波动率过低"],
                suggested_strategy="逐步减仓，控制风险"
            )
            signals.append(signal)
        
        # 情绪修复信号
        if (volume_signal.price_volume_sync == "量价齐升" and
            volatility_signal.vix_trend == "持续下降" and
            30 < fear_greed < 70):
            signal = ReversalSignal(
                signal_type="情绪修复",
                reversal_phase="中期", 
                confidence=0.5,
                time_window="中期",
                trigger_factors=["量价配合良好", "波动率回落", "情绪趋于平衡"],
                suggested_strategy="适度参与，观察延续性"
            )
            signals.append(signal)
        
        # 量能背离信号
        if volume_signal.price_volume_sync == "量价背离":
            indices = market_data.get('indices', {})
            if indices:
                avg_change = np.mean([idx.get('change_percent', 0) for idx in indices.values()])
                if avg_change > 2:  # 上涨但量能不足
                    signal = ReversalSignal(
                        signal_type="量价背离",
                        reversal_phase="尾期",
                        confidence=0.4,
                        time_window="短期",
                        trigger_factors=["价格上涨但成交量萎缩", "追涨意愿不强"],
                        suggested_strategy="谨慎观望，准备获利了结"
                    )
                    signals.append(signal)
        
        return signals
    
    def _determine_market_phase(self, volume_signal: VolumeSignal, 
                               volatility_signal: VolatilitySignal,
                               market_data: Dict) -> str:
        """判断市场阶段"""
        if volatility_signal.fear_peak:
            return "底部构建期"
        elif volatility_signal.complacency_valley:
            return "顶部形成期"
        elif volume_signal.trend_confirmation:
            return "趋势延续期"
        else:
            return "震荡整理期"
    
    def _analyze_sentiment_momentum(self, volume_signal: VolumeSignal,
                                   volatility_signal: VolatilitySignal, 
                                   sentiment_data: Dict) -> str:
        """分析情绪动量"""
        fear_greed = sentiment_data.get('fear_greed', {}).get('index_value', 50)
        
        if (volume_signal.signal_type in ["放量", "爆量"] and 
            volatility_signal.vix_trend == "持续下降" and 
            fear_greed > 50):
            return "情绪转强"
        elif (volume_signal.signal_type in ["地量", "缩量"] and
              volatility_signal.vix_trend == "急速上升" and
              fear_greed < 50):
            return "情绪转弱"
        elif volume_signal.price_volume_sync == "量价背离":
            return "情绪分化"
        else:
            return "情绪维持"
    
    def _calculate_risk_reward_ratio(self, reversal_signals: List[ReversalSignal],
                                    market_phase: str) -> float:
        """计算风险收益比"""
        base_ratio = 1.0
        
        # 基于反转信号调整
        for signal in reversal_signals:
            if signal.signal_type == "恐慌见底" and signal.confidence > 0.6:
                base_ratio += 0.5  # 见底信号提高收益潜力
            elif signal.signal_type == "亢奋见顶" and signal.confidence > 0.6:
                base_ratio -= 0.5  # 见顶信号增加风险
        
        # 基于市场阶段调整
        if market_phase == "底部构建期":
            base_ratio += 0.3
        elif market_phase == "顶部形成期":
            base_ratio -= 0.3
        
        return max(0.2, min(3.0, base_ratio))
    
    def _generate_position_advice(self, reversal_signals: List[ReversalSignal],
                                 market_phase: str, risk_reward_ratio: float) -> str:
        """生成仓位建议"""
        if risk_reward_ratio > 1.5:
            return "适度加仓，风险可控"
        elif risk_reward_ratio > 1.0:
            return "保持仓位，观察变化"
        elif risk_reward_ratio > 0.7:
            return "适度减仓，控制风险"
        else:
            return "大幅减仓，等待机会"
    
    def _get_default_reversal_result(self) -> SentimentReversalResult:
        """获取默认反转分析结果"""
        return SentimentReversalResult(
            volume_signal=VolumeSignal("正常量", 1.0, "无法判断", False),
            volatility_signal=VolatilitySignal("正常波动率", "震荡", False, False),
            reversal_signals=[],
            market_phase="震荡整理期",
            sentiment_momentum="情绪维持",
            risk_reward_ratio=1.0,
            position_advice="保持仓位，观察变化"
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
    
    def generate_reversal_report(self) -> str:
        """生成情绪反转分析报告"""
        result = self.analyze_sentiment_reversal()
        
        report = f"""
🔄 市场情绪反转信号分析
{'='*50}

⏰ **分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 **量能分析**:
  • 量能状态: {result.volume_signal.signal_type} (量比: {result.volume_signal.volume_ratio:.2f})
  • 量价关系: {result.volume_signal.price_volume_sync}
  • 趋势确认: {'是' if result.volume_signal.trend_confirmation else '否'}

🌊 **波动率分析**:
  • 波动水平: {result.volatility_signal.vix_level}
  • 波动趋势: {result.volatility_signal.vix_trend}
  • 恐慌峰值: {'是' if result.volatility_signal.fear_peak else '否'}
  • 自满谷底: {'是' if result.volatility_signal.complacency_valley else '否'}

🔄 **反转信号** ({len(result.reversal_signals)}个):"""
        
        if result.reversal_signals:
            for i, signal in enumerate(result.reversal_signals, 1):
                report += f"""
  {i}. [{signal.signal_type}] 置信度: {signal.confidence:.1%}
     • 阶段: {signal.reversal_phase} | 时间窗口: {signal.time_window}
     • 建议: {signal.suggested_strategy}
     • 依据: {', '.join(signal.trigger_factors)}"""
        else:
            report += "\n  暂无明确反转信号"
        
        report += f"""

🎯 **市场判断**:
  • 市场阶段: {result.market_phase}
  • 情绪动量: {result.sentiment_momentum}
  • 风险收益比: {result.risk_reward_ratio:.2f}

💼 **仓位建议**: {result.position_advice}

💡 **操作策略**:"""
        
        if "底部构建" in result.market_phase:
            report += """
  • 关注恐慌情绪见底信号
  • 分批建仓，不要急于抄底
  • 等待量价配合确认反转"""
        elif "顶部形成" in result.market_phase:
            report += """
  • 警惕亢奋情绪见顶风险
  • 适度获利了结，控制仓位
  • 关注量价背离信号"""
        elif "趋势延续" in result.market_phase:
            report += """
  • 顺势而为，保持仓位
  • 关注趋势疲态信号
  • 做好获利保护准备"""
        else:
            report += """
  • 保持观望，等待方向明朗
  • 控制风险，适度参与
  • 关注突破或跌破信号"""
        
        return report

def main():
    """主函数 - 演示情绪反转分析功能"""
    print("🔄 MarketBrew 情绪反转信号分析系统")
    print("=" * 60)
    
    analyzer = SentimentReversalAnalyzer()
    
    # 分析情绪反转
    print("🔍 正在分析情绪反转信号...")
    result = analyzer.analyze_sentiment_reversal()
    
    # 生成报告
    report = analyzer.generate_reversal_report()
    print(report)
    
    print(f"\n🔧 技术详情:")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"反转信号: {len(result.reversal_signals)}个")
    print(f"市场阶段: {result.market_phase}")
    print(f"风险收益比: {result.risk_reward_ratio:.2f}")

if __name__ == "__main__":
    main()