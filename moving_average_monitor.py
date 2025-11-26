#!/usr/bin/env python3
"""
大盘突破/跌破关键均线监控器
监控主要指数的关键移动平均线(5日、10日、20日、60日、120日、250日线)
检测突破和跌破信号，提供技术面参考
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
class MASignal:
    """均线信号数据"""
    index_name: str          # 指数名称
    index_code: str          # 指数代码
    current_price: float     # 当前价位
    ma_period: int           # 均线周期
    ma_value: float          # 均线数值
    signal_type: str         # 信号类型：突破/跌破/接近
    distance_percent: float  # 距离百分比
    volume_confirm: bool     # 是否有成交量确认
    strength: str           # 信号强度：强/中/弱

@dataclass
class MAMonitorResult:
    """均线监控结果"""
    monitor_time: str               # 监控时间
    breakthrough_signals: List[MASignal]  # 突破信号
    breakdown_signals: List[MASignal]     # 跌破信号
    approach_signals: List[MASignal]      # 接近信号
    ma_support_levels: Dict[str, List[float]]  # 支撑位
    ma_resistance_levels: Dict[str, List[float]] # 阻力位
    trend_analysis: Dict[str, str]        # 趋势分析
    critical_alerts: List[str]            # 关键预警

class MovingAverageMonitor:
    """移动平均线监控器"""
    
    def __init__(self):
        self.market_index_url = "http://localhost:5008"
        
        # 关键均线周期
        self.ma_periods = [5, 10, 20, 60, 120, 250]
        
        # 监控的主要指数
        self.monitor_indices = {
            '000001': '上证指数',
            '399001': '深证成指', 
            '399006': '创业板指',
            '000300': '沪深300',
            '000905': '中证500'
        }
        
        # 信号阈值
        self.signal_thresholds = {
            'breakthrough_confirm': 0.5,   # 突破确认阈值0.5%
            'breakdown_confirm': -0.5,     # 跌破确认阈值-0.5%
            'approach_distance': 1.0,      # 接近距离阈值1%
            'strong_signal': 2.0,          # 强信号阈值2%
            'volume_ratio': 1.2            # 成交量放大确认比例
        }
        
        self.cache = {}
        self.cache_duration = 180  # 3分钟缓存
        
    def monitor_moving_averages(self) -> MAMonitorResult:
        """监控移动平均线"""
        try:
            logger.info("📈 开始监控大盘关键均线...")
            
            # 获取指数数据
            indices_data = self._get_indices_data()
            
            # 获取历史价格数据用于计算均线
            historical_data = self._get_historical_data()
            
            # 检测突破信号
            breakthrough_signals = self._detect_breakthrough_signals(indices_data, historical_data)
            
            # 检测跌破信号
            breakdown_signals = self._detect_breakdown_signals(indices_data, historical_data)
            
            # 检测接近信号
            approach_signals = self._detect_approach_signals(indices_data, historical_data)
            
            # 计算支撑阻力位
            support_levels, resistance_levels = self._calculate_support_resistance(historical_data)
            
            # 分析趋势
            trend_analysis = self._analyze_trends(indices_data, historical_data)
            
            # 生成关键预警
            critical_alerts = self._generate_critical_alerts(
                breakthrough_signals, breakdown_signals, trend_analysis
            )
            
            result = MAMonitorResult(
                monitor_time=datetime.now().isoformat(),
                breakthrough_signals=breakthrough_signals,
                breakdown_signals=breakdown_signals,
                approach_signals=approach_signals,
                ma_support_levels=support_levels,
                ma_resistance_levels=resistance_levels,
                trend_analysis=trend_analysis,
                critical_alerts=critical_alerts
            )
            
            logger.info(f"📈 均线监控完成: 突破{len(breakthrough_signals)}个, 跌破{len(breakdown_signals)}个")
            return result
            
        except Exception as e:
            logger.error(f"均线监控失败: {e}")
            return self._get_default_monitor_result()
    
    def _get_indices_data(self) -> Dict:
        """获取指数数据"""
        cache_key = "ma_indices_data"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            response = requests.get(f"{self.market_index_url}/api/main-indices", timeout=10)
            if response.status_code == 200:
                indices_data = response.json()
                
                # 缓存数据
                self.cache[cache_key] = indices_data
                self._set_cache_time(cache_key)
                
                return indices_data
            else:
                logger.warning("无法获取指数数据")
                return {}
                
        except Exception as e:
            logger.error(f"获取指数数据失败: {e}")
            return {}
    
    def _get_historical_data(self) -> Dict[str, List[float]]:
        """获取历史价格数据"""
        # 在真实环境中，这里应该调用历史数据API
        # 目前生成模拟数据用于演示
        
        cache_key = "ma_historical_data"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            historical_data = {}
            
            # 为每个指数生成模拟的历史价格数据
            for code, name in self.monitor_indices.items():
                # 模拟250天的历史价格数据
                base_price = 3000 if code == '000001' else 2000
                prices = []
                
                # 生成有趋势的价格序列
                for i in range(250, 0, -1):
                    # 添加随机波动
                    change = np.random.uniform(-0.03, 0.03)  # 日波动-3%到+3%
                    if i > 0:
                        # 基于前一天价格
                        if prices:
                            base_price = prices[-1] * (1 + change)
                        else:
                            base_price = base_price * (1 + change)
                    
                    prices.append(round(base_price, 2))
                
                # 翻转序列，使最新价格在前
                prices.reverse()
                historical_data[code] = prices
            
            # 缓存数据
            self.cache[cache_key] = historical_data
            self._set_cache_time(cache_key)
            
            return historical_data
            
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return {}
    
    def _calculate_moving_averages(self, prices: List[float]) -> Dict[int, float]:
        """计算移动平均线"""
        ma_values = {}
        
        for period in self.ma_periods:
            if len(prices) >= period:
                ma_value = np.mean(prices[:period])
                ma_values[period] = round(ma_value, 2)
        
        return ma_values
    
    def _detect_breakthrough_signals(self, indices_data: Dict, historical_data: Dict) -> List[MASignal]:
        """检测突破信号"""
        signals = []
        
        try:
            indices = indices_data.get('indices', {})
            
            for code, index_data in indices.items():
                if code not in historical_data:
                    continue
                
                name = index_data.get('name', self.monitor_indices.get(code, code))
                current_price = index_data.get('current_value', 0)
                
                if current_price <= 0:
                    continue
                
                # 计算移动平均线
                prices = historical_data[code]
                ma_values = self._calculate_moving_averages(prices)
                
                # 检测突破
                for period, ma_value in ma_values.items():
                    if ma_value > 0:
                        distance_percent = (current_price - ma_value) / ma_value * 100
                        
                        # 判断是否为突破
                        if distance_percent >= self.signal_thresholds['breakthrough_confirm']:
                            # 检查前一日是否在均线下方
                            yesterday_price = prices[1] if len(prices) > 1 else current_price
                            yesterday_distance = (yesterday_price - ma_value) / ma_value * 100
                            
                            if yesterday_distance <= 0:  # 前一日在均线下方
                                # 检测成交量确认
                                volume_confirm = self._check_volume_confirmation(index_data)
                                
                                # 判断信号强度
                                strength = self._determine_signal_strength(distance_percent, volume_confirm)
                                
                                signal = MASignal(
                                    index_name=name,
                                    index_code=code,
                                    current_price=current_price,
                                    ma_period=period,
                                    ma_value=ma_value,
                                    signal_type="突破",
                                    distance_percent=distance_percent,
                                    volume_confirm=volume_confirm,
                                    strength=strength
                                )
                                
                                signals.append(signal)
            
            # 按重要性排序（周期短的和距离大的优先）
            signals.sort(key=lambda x: (x.ma_period, -abs(x.distance_percent)))
            
        except Exception as e:
            logger.warning(f"检测突破信号失败: {e}")
        
        return signals
    
    def _detect_breakdown_signals(self, indices_data: Dict, historical_data: Dict) -> List[MASignal]:
        """检测跌破信号"""
        signals = []
        
        try:
            indices = indices_data.get('indices', {})
            
            for code, index_data in indices.items():
                if code not in historical_data:
                    continue
                
                name = index_data.get('name', self.monitor_indices.get(code, code))
                current_price = index_data.get('current_value', 0)
                
                if current_price <= 0:
                    continue
                
                # 计算移动平均线
                prices = historical_data[code]
                ma_values = self._calculate_moving_averages(prices)
                
                # 检测跌破
                for period, ma_value in ma_values.items():
                    if ma_value > 0:
                        distance_percent = (current_price - ma_value) / ma_value * 100
                        
                        # 判断是否为跌破
                        if distance_percent <= self.signal_thresholds['breakdown_confirm']:
                            # 检查前一日是否在均线上方
                            yesterday_price = prices[1] if len(prices) > 1 else current_price
                            yesterday_distance = (yesterday_price - ma_value) / ma_value * 100
                            
                            if yesterday_distance >= 0:  # 前一日在均线上方
                                # 检测成交量确认
                                volume_confirm = self._check_volume_confirmation(index_data)
                                
                                # 判断信号强度
                                strength = self._determine_signal_strength(abs(distance_percent), volume_confirm)
                                
                                signal = MASignal(
                                    index_name=name,
                                    index_code=code,
                                    current_price=current_price,
                                    ma_period=period,
                                    ma_value=ma_value,
                                    signal_type="跌破",
                                    distance_percent=distance_percent,
                                    volume_confirm=volume_confirm,
                                    strength=strength
                                )
                                
                                signals.append(signal)
            
            # 按重要性排序
            signals.sort(key=lambda x: (x.ma_period, -abs(x.distance_percent)))
            
        except Exception as e:
            logger.warning(f"检测跌破信号失败: {e}")
        
        return signals
    
    def _detect_approach_signals(self, indices_data: Dict, historical_data: Dict) -> List[MASignal]:
        """检测接近信号"""
        signals = []
        
        try:
            indices = indices_data.get('indices', {})
            
            for code, index_data in indices.items():
                if code not in historical_data:
                    continue
                
                name = index_data.get('name', self.monitor_indices.get(code, code))
                current_price = index_data.get('current_value', 0)
                
                if current_price <= 0:
                    continue
                
                # 计算移动平均线
                prices = historical_data[code]
                ma_values = self._calculate_moving_averages(prices)
                
                # 检测接近关键均线
                for period, ma_value in ma_values.items():
                    if ma_value > 0:
                        distance_percent = (current_price - ma_value) / ma_value * 100
                        
                        # 判断是否接近均线
                        if abs(distance_percent) <= self.signal_thresholds['approach_distance']:
                            signal = MASignal(
                                index_name=name,
                                index_code=code,
                                current_price=current_price,
                                ma_period=period,
                                ma_value=ma_value,
                                signal_type="接近",
                                distance_percent=distance_percent,
                                volume_confirm=False,
                                strength="中"
                            )
                            
                            signals.append(signal)
            
            # 过滤重复并排序
            unique_signals = {}
            for signal in signals:
                key = f"{signal.index_code}_{signal.ma_period}"
                if key not in unique_signals or abs(signal.distance_percent) < abs(unique_signals[key].distance_percent):
                    unique_signals[key] = signal
            
            return list(unique_signals.values())
            
        except Exception as e:
            logger.warning(f"检测接近信号失败: {e}")
        
        return signals
    
    def _check_volume_confirmation(self, index_data: Dict) -> bool:
        """检查成交量确认"""
        # 在真实环境中，这里需要比较当日成交量与历史平均成交量
        # 目前简化处理
        volume = index_data.get('volume', 0)
        turnover = index_data.get('turnover', 0)
        
        # 简单的成交量放大判断
        return volume > 0 or turnover > 0
    
    def _determine_signal_strength(self, distance_percent: float, volume_confirm: bool) -> str:
        """判断信号强度"""
        if distance_percent >= self.signal_thresholds['strong_signal'] and volume_confirm:
            return "强"
        elif distance_percent >= 1.0 or volume_confirm:
            return "中"
        else:
            return "弱"
    
    def _calculate_support_resistance(self, historical_data: Dict) -> Tuple[Dict[str, List[float]], Dict[str, List[float]]]:
        """计算支撑阻力位"""
        support_levels = {}
        resistance_levels = {}
        
        try:
            for code, prices in historical_data.items():
                if len(prices) < 60:
                    continue
                
                # 计算关键均线作为支撑阻力位
                ma_values = self._calculate_moving_averages(prices)
                current_price = prices[0]
                
                supports = []
                resistances = []
                
                for period, ma_value in ma_values.items():
                    if ma_value < current_price:
                        supports.append(ma_value)
                    else:
                        resistances.append(ma_value)
                
                # 排序并取最重要的几个
                supports.sort(reverse=True)  # 从高到低
                resistances.sort()          # 从低到高
                
                index_name = self.monitor_indices.get(code, code)
                support_levels[index_name] = supports[:3]    # 取最近的3个支撑位
                resistance_levels[index_name] = resistances[:3]  # 取最近的3个阻力位
        
        except Exception as e:
            logger.warning(f"计算支撑阻力失败: {e}")
        
        return support_levels, resistance_levels
    
    def _analyze_trends(self, indices_data: Dict, historical_data: Dict) -> Dict[str, str]:
        """分析趋势"""
        trends = {}
        
        try:
            indices = indices_data.get('indices', {})
            
            for code, index_data in indices.items():
                name = index_data.get('name', self.monitor_indices.get(code, code))
                current_price = index_data.get('current_value', 0)
                
                if code not in historical_data or current_price <= 0:
                    continue
                
                prices = historical_data[code]
                ma_values = self._calculate_moving_averages(prices)
                
                # 基于均线排列判断趋势
                if len(ma_values) >= 3:
                    ma_5 = ma_values.get(5, 0)
                    ma_20 = ma_values.get(20, 0)
                    ma_60 = ma_values.get(60, 0)
                    
                    if current_price > ma_5 > ma_20 > ma_60:
                        trend = "强势上涨"
                    elif current_price > ma_5 > ma_20:
                        trend = "震荡上涨"
                    elif current_price > ma_20:
                        trend = "弱势上涨"
                    elif current_price < ma_5 < ma_20 < ma_60:
                        trend = "强势下跌"
                    elif current_price < ma_5 < ma_20:
                        trend = "震荡下跌"
                    elif current_price < ma_20:
                        trend = "弱势下跌"
                    else:
                        trend = "横盘整理"
                    
                    trends[name] = trend
        
        except Exception as e:
            logger.warning(f"趋势分析失败: {e}")
        
        return trends
    
    def _generate_critical_alerts(self, breakthrough_signals: List[MASignal], 
                                breakdown_signals: List[MASignal], 
                                trends: Dict[str, str]) -> List[str]:
        """生成关键预警"""
        alerts = []
        
        # 重要突破预警
        for signal in breakthrough_signals:
            if signal.ma_period in [20, 60, 250] and signal.strength in ["强", "中"]:
                alerts.append(f"{signal.index_name}突破{signal.ma_period}日线，当前{signal.current_price:.2f}")
        
        # 重要跌破预警
        for signal in breakdown_signals:
            if signal.ma_period in [20, 60, 250] and signal.strength in ["强", "中"]:
                alerts.append(f"{signal.index_name}跌破{signal.ma_period}日线，当前{signal.current_price:.2f}")
        
        # 趋势变化预警
        for index_name, trend in trends.items():
            if trend in ["强势上涨", "强势下跌"]:
                alerts.append(f"{index_name}呈现{trend}趋势")
        
        return alerts[:5]  # 最多返回5个预警
    
    def _get_default_monitor_result(self) -> MAMonitorResult:
        """获取默认监控结果"""
        return MAMonitorResult(
            monitor_time=datetime.now().isoformat(),
            breakthrough_signals=[],
            breakdown_signals=[],
            approach_signals=[],
            ma_support_levels={},
            ma_resistance_levels={},
            trend_analysis={'数据异常': '无法分析'},
            critical_alerts=['数据获取异常']
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
    
    def generate_ma_monitor_report(self) -> str:
        """生成均线监控报告"""
        result = self.monitor_moving_averages()
        
        signal_icons = {
            '突破': '🚀',
            '跌破': '📉',
            '接近': '👀'
        }
        
        strength_icons = {
            '强': '🔥',
            '中': '⚡',
            '弱': '💫'
        }
        
        report = f"""
📈 大盘关键均线监控报告
{'='*50}

⏰ **监控时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🚀 **突破信号** ({len(result.breakthrough_signals)}个):"""
        
        if result.breakthrough_signals:
            for signal in result.breakthrough_signals[:5]:
                icon = strength_icons.get(signal.strength, '💫')
                volume_status = "放量" if signal.volume_confirm else "缩量"
                report += f"""
  {icon} {signal.index_name} 突破 {signal.ma_period}日线
     • 当前价位: {signal.current_price:.2f}
     • 均线位置: {signal.ma_value:.2f} ({signal.distance_percent:+.2f}%)
     • 信号强度: {signal.strength} | {volume_status}确认"""
        else:
            report += "\n  暂无突破信号"
        
        report += f"\n\n📉 **跌破信号** ({len(result.breakdown_signals)}个):"
        
        if result.breakdown_signals:
            for signal in result.breakdown_signals[:5]:
                icon = strength_icons.get(signal.strength, '💫')
                volume_status = "放量" if signal.volume_confirm else "缩量"
                report += f"""
  {icon} {signal.index_name} 跌破 {signal.ma_period}日线
     • 当前价位: {signal.current_price:.2f}
     • 均线位置: {signal.ma_value:.2f} ({signal.distance_percent:+.2f}%)
     • 信号强度: {signal.strength} | {volume_status}确认"""
        else:
            report += "\n  暂无跌破信号"
        
        report += f"\n\n👀 **接近关键位** ({len(result.approach_signals)}个):"
        
        if result.approach_signals:
            for signal in result.approach_signals[:3]:
                direction = "上方" if signal.distance_percent > 0 else "下方"
                report += f"""
  👀 {signal.index_name} 接近 {signal.ma_period}日线
     • 当前在均线{direction} {abs(signal.distance_percent):.2f}%"""
        else:
            report += "\n  暂无接近信号"
        
        report += f"\n\n📊 **趋势分析**:"
        if result.trend_analysis:
            for index_name, trend in result.trend_analysis.items():
                if trend != '无法分析':
                    report += f"\n  📈 {index_name}: {trend}"
        else:
            report += "\n  暂无趋势数据"
        
        report += f"\n\n🚨 **关键预警**:"
        if result.critical_alerts:
            for i, alert in enumerate(result.critical_alerts, 1):
                report += f"\n  {i}. ⚠️ {alert}"
        else:
            report += "\n  暂无关键预警"
        
        report += f"""

💡 **操作建议**:
  • 关注重要均线的突破和跌破信号
  • 结合成交量确认信号有效性
  • 20日线、60日线、250日线为关键参考
  • 均线多头排列时可积极操作
  • 均线空头排列时保持谨慎
"""
        
        return report

def main():
    """主函数 - 演示均线监控功能"""
    print("📈 MarketBrew 移动平均线监控系统")
    print("=" * 60)
    
    monitor = MovingAverageMonitor()
    
    # 监控均线
    print("🔍 正在监控大盘关键均线...")
    result = monitor.monitor_moving_averages()
    
    # 生成报告
    report = monitor.generate_ma_monitor_report()
    print(report)
    
    print(f"\n🔧 技术详情:")
    print(f"监控指数: {len(monitor.monitor_indices)}个")
    print(f"监控均线: {', '.join([f'{p}日' for p in monitor.ma_periods])}")

if __name__ == "__main__":
    main()