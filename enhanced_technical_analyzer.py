#!/usr/bin/env python3
"""
增强版技术分析器
实现更精确的技术分析逻辑：
1. 指数 > MA20 & MA30
2. MA20、MA30均向上（5日斜率 > 0）
3. 指数连续2-3天收盘在均线之上，或突破当天放量，或回踩不破
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TechnicalSignal:
    """技术信号结果"""
    signal_type: str          # 信号类型：强势突破/温和突破/震荡/弱势
    signal_strength: float    # 信号强度 0-100
    above_ma: bool           # 是否在均线之上
    ma_trend_up: bool        # 均线是否向上
    consecutive_days: int    # 连续突破天数
    volume_breakout: bool    # 是否放量突破
    pullback_hold: bool      # 回踩是否守住
    details: Dict            # 详细数据

@dataclass
class MarketData:
    """市场数据"""
    prices: pd.Series        # 收盘价序列
    volumes: pd.Series       # 成交量序列
    ma20: pd.Series         # MA20序列
    ma30: pd.Series         # MA30序列
    dates: pd.DatetimeIndex # 日期索引

class EnhancedTechnicalAnalyzer:
    """增强版技术分析器"""
    
    def __init__(self):
        self.symbol = "000300.SS"  # 沪深300
        self.lookback_days = 80    # 回看天数
        
    def get_market_data(self) -> Optional[MarketData]:
        """获取市场数据"""
        try:
            logger.info("📊 获取沪深300历史数据...")
            
            # 获取数据
            ticker = yf.Ticker(self.symbol)
            hist = ticker.history(period=f"{self.lookback_days}d")
            
            if hist.empty:
                logger.error("无法获取历史数据")
                return None
            
            # 计算移动平均线
            hist['MA20'] = hist['Close'].rolling(window=20).mean()
            hist['MA30'] = hist['Close'].rolling(window=30).mean()
            
            # 创建MarketData对象
            data = MarketData(
                prices=hist['Close'],
                volumes=hist['Volume'],
                ma20=hist['MA20'],
                ma30=hist['MA30'],
                dates=hist.index
            )
            
            logger.info(f"✅ 获取到{len(hist)}天数据")
            return data
            
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return None
    
    def calculate_ma_slope(self, ma_series: pd.Series, days: int = 5) -> float:
        """计算均线斜率（最近N天的平均斜率）"""
        try:
            if len(ma_series) < days + 1:
                return 0.0
            
            # 取最近days天的数据
            recent_ma = ma_series.tail(days + 1)
            
            # 计算每日斜率并取平均
            slopes = []
            for i in range(1, len(recent_ma)):
                slope = (recent_ma.iloc[i] - recent_ma.iloc[i-1]) / recent_ma.iloc[i-1] * 100
                slopes.append(slope)
            
            return np.mean(slopes) if slopes else 0.0
            
        except Exception as e:
            logger.warning(f"计算均线斜率失败: {e}")
            return 0.0
    
    def check_above_ma_condition(self, data: MarketData) -> Tuple[bool, Dict]:
        """检查指数是否在MA20和MA30之上"""
        try:
            latest_price = data.prices.iloc[-1]
            latest_ma20 = data.ma20.iloc[-1]
            latest_ma30 = data.ma30.iloc[-1]
            
            above_ma20 = latest_price > latest_ma20
            above_ma30 = latest_price > latest_ma30
            above_both = above_ma20 and above_ma30
            
            details = {
                'price': latest_price,
                'ma20': latest_ma20,
                'ma30': latest_ma30,
                'above_ma20': above_ma20,
                'above_ma30': above_ma30,
                'distance_ma20_pct': ((latest_price - latest_ma20) / latest_ma20 * 100),
                'distance_ma30_pct': ((latest_price - latest_ma30) / latest_ma30 * 100)
            }
            
            return above_both, details
            
        except Exception as e:
            logger.error(f"检查均线位置失败: {e}")
            return False, {}
    
    def check_ma_trend_up(self, data: MarketData) -> Tuple[bool, Dict]:
        """检查MA20和MA30是否向上（5日斜率 > 0）"""
        try:
            ma20_slope = self.calculate_ma_slope(data.ma20, days=5)
            ma30_slope = self.calculate_ma_slope(data.ma30, days=5)
            
            ma20_up = ma20_slope > 0
            ma30_up = ma30_slope > 0
            both_up = ma20_up and ma30_up
            
            details = {
                'ma20_slope_5d': ma20_slope,
                'ma30_slope_5d': ma30_slope,
                'ma20_trend_up': ma20_up,
                'ma30_trend_up': ma30_up,
                'slope_threshold': 0.0
            }
            
            return both_up, details
            
        except Exception as e:
            logger.error(f"检查均线趋势失败: {e}")
            return False, {}
    
    def check_consecutive_days_above_ma(self, data: MarketData, min_days: int = 2) -> Tuple[int, Dict]:
        """检查连续在均线之上的天数"""
        try:
            consecutive_days = 0
            breakout_date = None
            
            # 从最新日期往前检查
            for i in range(len(data.prices) - 1, -1, -1):
                if pd.isna(data.ma20.iloc[i]) or pd.isna(data.ma30.iloc[i]):
                    break
                
                price = data.prices.iloc[i]
                ma20 = data.ma20.iloc[i]
                ma30 = data.ma30.iloc[i]
                
                if price > ma20 and price > ma30:
                    consecutive_days += 1
                    breakout_date = data.dates[i]
                else:
                    break
            
            details = {
                'consecutive_days': consecutive_days,
                'breakout_date': breakout_date.strftime('%Y-%m-%d') if breakout_date else None,
                'meets_minimum': consecutive_days >= min_days,
                'required_days': min_days
            }
            
            return consecutive_days, details
            
        except Exception as e:
            logger.error(f"检查连续突破天数失败: {e}")
            return 0, {}
    
    def check_volume_breakout(self, data: MarketData, lookback_days: int = 20) -> Tuple[bool, Dict]:
        """检查是否放量突破"""
        try:
            if len(data.volumes) < lookback_days + 5:
                return False, {'error': '数据不足'}
            
            # 获取最近几天的成交量
            recent_volumes = data.volumes.tail(5)  # 最近5天
            avg_volume_before = data.volumes.tail(lookback_days + 5).head(lookback_days).mean()  # 之前20天平均
            
            # 检查最近几天是否有明显放量
            max_recent_volume = recent_volumes.max()
            volume_ratio = max_recent_volume / avg_volume_before if avg_volume_before > 0 else 1
            
            # 放量标准：成交量超过前期平均的1.5倍
            is_volume_breakout = volume_ratio >= 1.5
            
            details = {
                'max_recent_volume': int(max_recent_volume),
                'avg_volume_before': int(avg_volume_before),
                'volume_ratio': volume_ratio,
                'volume_threshold': 1.5,
                'is_volume_breakout': is_volume_breakout
            }
            
            return is_volume_breakout, details
            
        except Exception as e:
            logger.error(f"检查放量突破失败: {e}")
            return False, {}
    
    def check_pullback_hold(self, data: MarketData, lookback_days: int = 10) -> Tuple[bool, Dict]:
        """检查回踩不破（近期低点未跌破关键均线）"""
        try:
            if len(data.prices) < lookback_days:
                return False, {'error': '数据不足'}
            
            # 获取最近10天的数据
            recent_data = data.tail(lookback_days) if hasattr(data, 'tail') else None
            if recent_data is None:
                recent_prices = data.prices.tail(lookback_days)
                recent_ma20 = data.ma20.tail(lookback_days)
                recent_ma30 = data.ma30.tail(lookback_days)
            else:
                recent_prices = recent_data.prices
                recent_ma20 = recent_data.ma20
                recent_ma30 = recent_data.ma30
            
            # 找到最近的最低点
            min_price_idx = recent_prices.idxmin()
            min_price = recent_prices.loc[min_price_idx]
            
            # 获取最低点当天的均线值
            ma20_at_min = recent_ma20.loc[min_price_idx] if min_price_idx in recent_ma20.index else recent_ma20.iloc[-1]
            ma30_at_min = recent_ma30.loc[min_price_idx] if min_price_idx in recent_ma30.index else recent_ma30.iloc[-1]
            
            # 判断最低点是否守住均线（这里用较宽松的标准，允许短暂跌破但收盘要守住）
            hold_ma20 = min_price >= ma20_at_min * 0.99  # 允许1%的误差
            hold_ma30 = min_price >= ma30_at_min * 0.99
            pullback_hold = hold_ma20 and hold_ma30
            
            details = {
                'min_price_date': min_price_idx.strftime('%Y-%m-%d'),
                'min_price': min_price,
                'ma20_at_min': ma20_at_min,
                'ma30_at_min': ma30_at_min,
                'hold_ma20': hold_ma20,
                'hold_ma30': hold_ma30,
                'pullback_hold': pullback_hold
            }
            
            return pullback_hold, details
            
        except Exception as e:
            logger.error(f"检查回踩不破失败: {e}")
            return False, {}
    
    def analyze_technical_signal(self) -> TechnicalSignal:
        """综合技术分析"""
        try:
            # 获取数据
            data = self.get_market_data()
            if data is None:
                return self._get_default_signal()
            
            # 1. 检查是否在均线之上
            above_ma, above_ma_details = self.check_above_ma_condition(data)
            
            # 2. 检查均线是否向上
            ma_trend_up, ma_trend_details = self.check_ma_trend_up(data)
            
            # 3. 检查连续突破天数
            consecutive_days, consecutive_details = self.check_consecutive_days_above_ma(data)
            
            # 4. 检查放量突破
            volume_breakout, volume_details = self.check_volume_breakout(data)
            
            # 5. 检查回踩不破
            pullback_hold, pullback_details = self.check_pullback_hold(data)
            
            # 综合判断信号类型和强度
            signal_type, signal_strength = self._determine_signal_type(
                above_ma, ma_trend_up, consecutive_days, volume_breakout, pullback_hold
            )
            
            # 汇总详细数据
            details = {
                'above_ma': above_ma_details,
                'ma_trend': ma_trend_details,
                'consecutive': consecutive_details,
                'volume': volume_details,
                'pullback': pullback_details,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return TechnicalSignal(
                signal_type=signal_type,
                signal_strength=signal_strength,
                above_ma=above_ma,
                ma_trend_up=ma_trend_up,
                consecutive_days=consecutive_days,
                volume_breakout=volume_breakout,
                pullback_hold=pullback_hold,
                details=details
            )
            
        except Exception as e:
            logger.error(f"技术分析失败: {e}")
            return self._get_default_signal()
    
    def _determine_signal_type(self, above_ma: bool, ma_trend_up: bool, 
                              consecutive_days: int, volume_breakout: bool, 
                              pullback_hold: bool) -> Tuple[str, float]:
        """确定信号类型和强度"""
        
        # 基础分数
        score = 0
        
        # 核心条件评分
        if above_ma:
            score += 30  # 在均线之上是最基本条件
        
        if ma_trend_up:
            score += 25  # 均线向上是重要趋势信号
        
        # 确认条件评分
        if consecutive_days >= 3:
            score += 20  # 连续3天以上突破
        elif consecutive_days >= 2:
            score += 15  # 连续2天突破
        elif consecutive_days >= 1:
            score += 10  # 至少1天突破
        
        if volume_breakout:
            score += 15  # 放量突破确认
        
        if pullback_hold:
            score += 10  # 回踩不破确认
        
        # 确定信号类型
        if score >= 80 and above_ma and ma_trend_up:
            return "强势突破", score
        elif score >= 60 and above_ma:
            return "温和突破", score
        elif score >= 40:
            return "震荡突破", score
        elif above_ma:
            return "弱势突破", score
        else:
            return "震荡整理", score
    
    def _get_default_signal(self) -> TechnicalSignal:
        """获取默认信号"""
        return TechnicalSignal(
            signal_type="数据异常",
            signal_strength=0,
            above_ma=False,
            ma_trend_up=False,
            consecutive_days=0,
            volume_breakout=False,
            pullback_hold=False,
            details={}
        )
    
    def generate_analysis_report(self) -> str:
        """生成分析报告"""
        signal = self.analyze_technical_signal()
        
        report = f"""
🔍 沪深300增强技术分析报告
{'='*50}

📊 **综合信号**: {signal.signal_type} (强度: {signal.signal_strength:.1f}/100)

✅ **核心条件检查**:
  • 价格 > MA20 & MA30: {'✅ 是' if signal.above_ma else '❌ 否'}
  • MA20、MA30向上: {'✅ 是' if signal.ma_trend_up else '❌ 否'}

🔍 **确认条件检查**:
  • 连续突破天数: {signal.consecutive_days}天
  • 放量突破: {'✅ 是' if signal.volume_breakout else '❌ 否'}
  • 回踩不破: {'✅ 是' if signal.pullback_hold else '❌ 否'}
"""
        
        # 详细数据
        if signal.details:
            above_ma = signal.details.get('above_ma', {})
            ma_trend = signal.details.get('ma_trend', {})
            consecutive = signal.details.get('consecutive', {})
            volume = signal.details.get('volume', {})
            
            report += f"""
📈 **详细数据**:
  • 最新价格: {above_ma.get('price', 0):.2f}
  • MA20: {above_ma.get('ma20', 0):.2f} (距离: {above_ma.get('distance_ma20_pct', 0):.2f}%)
  • MA30: {above_ma.get('ma30', 0):.2f} (距离: {above_ma.get('distance_ma30_pct', 0):.2f}%)
  • MA20斜率: {ma_trend.get('ma20_slope_5d', 0):.3f}%
  • MA30斜率: {ma_trend.get('ma30_slope_5d', 0):.3f}%
  • 突破开始日期: {consecutive.get('breakout_date', 'N/A')}
  • 放量倍数: {volume.get('volume_ratio', 0):.2f}倍
"""
        
        # 交易建议
        report += f"""
💡 **交易建议**:"""
        
        if signal.signal_type == "强势突破":
            report += """
  • 🟢 强势买入信号，可积极布局
  • 🎯 建议满仓或加仓操作
  • ⚠️ 设置止损位在MA20下方2%"""
        elif signal.signal_type == "温和突破":
            report += """
  • 🟡 温和买入信号，可适度布局
  • 🎯 建议半仓或逐步加仓
  • ⚠️ 设置止损位在MA30下方"""
        elif "突破" in signal.signal_type:
            report += """
  • 🟡 观察信号，可小仓位试探
  • 🎯 等待更多确认信号
  • ⚠️ 严格止损，控制风险"""
        else:
            report += """
  • 🔴 暂无明确方向，建议观望
  • 🎯 等待突破信号出现
  • ⚠️ 保持现金，控制仓位"""
        
        return report

def main():
    """主函数"""
    print("🔍 沪深300增强技术分析系统")
    print("="*50)
    
    analyzer = EnhancedTechnicalAnalyzer()
    
    # 进行技术分析
    print("📊 正在进行技术分析...")
    signal = analyzer.analyze_technical_signal()
    
    # 生成报告
    report = analyzer.generate_analysis_report()
    print(report)

if __name__ == "__main__":
    main()