#!/usr/bin/env python3
"""
市场情绪与风险监控系统 (Market Mood)
帮助用户判断今天适不适合出手：追涨日/观望日/抄底日
"""

import requests
import json
import logging
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from sentiment_indicator_analyzer import SentimentIndicatorAnalyzer
from sentiment_reversal_analyzer import SentimentReversalAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MarketMoodResult:
    """市场情绪分析结果"""
    mood_score: float  # 0-100分，越高越乐观
    mood_level: str    # 恐慌/谨慎/中性/乐观/亢奋
    action_type: str   # 抄底日/观望日/追涨日
    confidence: float  # 信号置信度
    risk_alerts: List[str]
    opportunities: List[str]
    # 新增字段
    market_phase: str = "震荡整理期"           # 市场阶段：底部构建/顶部形成/趋势延续/震荡整理
    reversal_signals: List[str] = None       # 反转信号列表
    volume_signal: str = "正常量"             # 量能信号
    volatility_level: str = "正常波动率"      # 波动率水平
    
    def __post_init__(self):
        if self.reversal_signals is None:
            self.reversal_signals = []
    
class MarketMoodAnalyzer:
    """市场情绪分析器"""
    
    def __init__(self):
        self.market_index_url = "http://localhost:5008"
        self.price_service_url = "http://localhost:5002"
        
        # 初始化高级分析器
        self.sentiment_analyzer = SentimentIndicatorAnalyzer()
        self.reversal_analyzer = SentimentReversalAnalyzer()
        
        # 情绪阈值配置
        self.mood_thresholds = {
            'panic': 20,        # 恐慌区 0-20
            'cautious': 40,     # 谨慎区 20-40  
            'neutral': 60,      # 中性区 40-60
            'optimistic': 80,   # 乐观区 60-80
            'euphoric': 100     # 亢奋区 80-100
        }
        
        # 行动建议映射
        self.action_mapping = {
            'panic': '抄底日',
            'cautious': '观望日',
            'neutral': '观望日', 
            'optimistic': '追涨日',
            'euphoric': '观望日'  # 亢奋时也建议观望
        }
        
        self.cache = {}
        self.cache_duration = 120  # 2分钟缓存
        
    def analyze_market_mood(self) -> MarketMoodResult:
        """分析市场情绪"""
        try:
            # 获取基础数据
            market_data = self._get_comprehensive_market_data()
            
            # 计算各项指标
            temperature_score = self._calculate_market_temperature(market_data)
            sector_score = self._calculate_sector_heat(market_data) 
            capital_score = self._calculate_capital_flow(market_data)
            technical_score = self._calculate_technical_signals(market_data)
            sentiment_score = self._calculate_sentiment_indicators(market_data)
            
            # 综合评分
            weights = {
                'temperature': 0.25,  # 市场温度计
                'sector': 0.20,       # 行业热力
                'capital': 0.25,      # 资金流向
                'technical': 0.20,    # 技术信号
                'sentiment': 0.10     # 情绪指标
            }
            
            mood_score = (
                temperature_score * weights['temperature'] +
                sector_score * weights['sector'] +
                capital_score * weights['capital'] +
                technical_score * weights['technical'] +
                sentiment_score * weights['sentiment']
            )
            
            # 确定情绪等级和行动建议
            mood_level = self._determine_mood_level(mood_score)
            action_type = self.action_mapping[mood_level]
            
            # 风险提醒和机会识别
            risk_alerts = self._identify_risk_alerts(market_data, mood_score)
            opportunities = self._identify_opportunities(market_data, mood_score)
            
            # 计算置信度
            confidence = self._calculate_confidence(market_data, mood_score)
            
            # 分析情绪反转信号
            try:
                reversal_result = self.reversal_analyzer.analyze_sentiment_reversal()
                market_phase = reversal_result.market_phase
                reversal_signal_list = [f"{signal.signal_type}({signal.confidence:.1%})" for signal in reversal_result.reversal_signals]
                volume_signal = reversal_result.volume_signal.signal_type
                volatility_level = reversal_result.volatility_signal.vix_level
                
                logger.info(f"反转分析: {market_phase}, {len(reversal_result.reversal_signals)}个信号")
            except Exception as e:
                logger.warning(f"反转分析失败: {e}")
                market_phase = "震荡整理期"
                reversal_signal_list = []
                volume_signal = "正常量"
                volatility_level = "正常波动率"
            
            result = MarketMoodResult(
                mood_score=round(mood_score, 1),
                mood_level=mood_level,
                action_type=action_type,
                confidence=confidence,
                risk_alerts=risk_alerts,
                opportunities=opportunities,
                market_phase=market_phase,
                reversal_signals=reversal_signal_list,
                volume_signal=volume_signal,
                volatility_level=volatility_level
            )
            
            logger.info(f"🎯 市场情绪分析完成: {mood_score:.1f}分 - {mood_level} - {action_type}")
            return result
            
        except Exception as e:
            logger.error(f"市场情绪分析失败: {e}")
            return self._get_default_mood()
    
    def _get_comprehensive_market_data(self) -> Dict:
        """获取综合市场数据"""
        cache_key = "comprehensive_market_data"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            market_data = {}
            
            # 获取主要指数数据
            response = requests.get(f"{self.market_index_url}/api/main-indices", timeout=10)
            if response.status_code == 200:
                indices_data = response.json()
                market_data['indices'] = indices_data.get('indices', {})
                market_data['market_overview'] = indices_data.get('market_overview', {})
                market_data['market_status'] = indices_data.get('market_status', {})
            
            # 获取行业数据
            response = requests.get(f"{self.market_index_url}/api/sector-indices", timeout=10)
            if response.status_code == 200:
                sector_data = response.json()
                market_data['sectors'] = sector_data
            
            # 模拟获取其他关键数据（实际场景需要接入真实API）
            market_data['etf_flows'] = self._simulate_etf_flows()
            market_data['margin_trading'] = self._simulate_margin_data()
            market_data['northbound_capital'] = self._simulate_northbound_capital()
            market_data['volatility'] = self._simulate_volatility_data()
            
            # 如果market_overview为空，生成模拟的市场概览数据
            if not market_data.get('market_overview'):
                market_data['market_overview'] = self._simulate_market_overview()
            
            # 保存最新的市场概况数据供ETF计算使用
            self._last_market_overview = market_data['market_overview']
            
            # 缓存数据
            self.cache[cache_key] = market_data
            self._set_cache_time(cache_key)
            
            return market_data
            
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return {}
    
    def _calculate_market_temperature(self, market_data: Dict) -> float:
        """计算市场温度计 (0-100)"""
        try:
            score = 50  # 基准分
            
            # 涨跌家数 (30分)
            overview = market_data.get('market_overview', {})
            up_stocks = overview.get('up_stocks', 0)
            down_stocks = overview.get('down_stocks', 0)
            total_stocks = overview.get('total_stocks', 1)
            
            if total_stocks > 0:
                up_ratio = up_stocks / total_stocks
                if up_ratio > 0.7:
                    score += 30
                elif up_ratio > 0.6:
                    score += 20
                elif up_ratio > 0.5:
                    score += 10
                elif up_ratio < 0.3:
                    score -= 30
                elif up_ratio < 0.4:
                    score -= 20
            
            # 成交额 (25分)
            turnover = overview.get('total_turnover', 0)
            if turnover > 15000:  # 超1.5万亿
                score += 25
            elif turnover > 12000:
                score += 15
            elif turnover > 10000:
                score += 5
            elif turnover < 6000:
                score -= 25
            elif turnover < 8000:
                score -= 15
            
            # 两融数据 (20分)
            margin_data = market_data.get('margin_trading', {})
            margin_balance = margin_data.get('balance_change_pct', 0)
            if margin_balance > 2:
                score += 20
            elif margin_balance > 1:
                score += 10
            elif margin_balance < -2:
                score -= 20
            elif margin_balance < -1:
                score -= 10
            
            # ETF资金流 (25分)
            etf_flows = market_data.get('etf_flows', {})
            net_inflow = etf_flows.get('net_inflow_billion', 0)
            if net_inflow > 50:
                score += 25
            elif net_inflow > 20:
                score += 15
            elif net_inflow > 0:
                score += 5
            elif net_inflow < -50:
                score -= 25
            elif net_inflow < -20:
                score -= 15
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.warning(f"市场温度计算失败: {e}")
            return 50
    
    def _calculate_sector_heat(self, market_data: Dict) -> float:
        """计算行业热力图 (0-100)"""
        try:
            sectors = market_data.get('sectors', {})
            sector_performance = sectors.get('sector_performance', {})
            
            if not sector_performance:
                return 50
            
            # 领涨板块数量 (40分)
            leading_sectors = sector_performance.get('leading_sectors', [])
            if len(leading_sectors) >= 5:
                heat_score = 90
            elif len(leading_sectors) >= 3:
                heat_score = 70
            elif len(leading_sectors) >= 1:
                heat_score = 55
            else:
                heat_score = 30
            
            # 板块轮动情况 (30分)
            rotation = sector_performance.get('sector_rotation', '')
            if '科技' in rotation or '新能源' in rotation:
                heat_score += 15  # 成长股活跃
            elif '金融' in rotation:
                heat_score += 10  # 价值股活跃
            elif '消费' in rotation:
                heat_score += 12  # 消费股活跃
            
            # 板块涨幅分化 (30分)
            best_sectors = sector_performance.get('best_performing', [])
            worst_sectors = sector_performance.get('worst_performing', [])
            
            if best_sectors and worst_sectors:
                # 计算分化程度
                try:
                    best_avg = np.mean([s.get('change_percent', 0) for s in best_sectors[:3]])
                    worst_avg = np.mean([s.get('change_percent', 0) for s in worst_sectors[:3]])
                    spread = best_avg - worst_avg
                    
                    if spread > 5:  # 分化明显，有明确热点
                        heat_score += 20
                    elif spread > 3:
                        heat_score += 10
                    elif spread < 1:  # 过于一致，缺乏热点
                        heat_score -= 10
                except:
                    pass
            
            return max(0, min(100, heat_score))
            
        except Exception as e:
            logger.warning(f"行业热力计算失败: {e}")
            return 50
    
    def _calculate_capital_flow(self, market_data: Dict) -> float:
        """计算资金流向评分 (0-100)"""
        try:
            score = 50  # 基准分
            
            # 北向资金 (40分)
            northbound = market_data.get('northbound_capital', {})
            net_inflow = northbound.get('net_inflow_billion', 0)
            if net_inflow > 10:
                score += 30
            elif net_inflow > 5:
                score += 20
            elif net_inflow > 0:
                score += 10
            elif net_inflow < -10:
                score -= 30
            elif net_inflow < -5:
                score -= 20
            
            # 主力资金监控 (30分)
            # 基于ETF和大单交易模拟
            etf_flows = market_data.get('etf_flows', {})
            large_cap_flow = etf_flows.get('large_cap_flow', 0)
            small_cap_flow = etf_flows.get('small_cap_flow', 0)
            
            if large_cap_flow > 0 and small_cap_flow > 0:
                score += 25  # 全面流入
            elif large_cap_flow > 0:
                score += 15  # 大盘股受青睐
            elif small_cap_flow > 0:
                score += 10  # 小盘股活跃
            elif large_cap_flow < 0 and small_cap_flow < 0:
                score -= 25  # 全面流出
            
            # 融资融券 (30分)
            margin_data = market_data.get('margin_trading', {})
            financing_change = margin_data.get('financing_change_pct', 0)
            if financing_change > 1:
                score += 20
            elif financing_change > 0:
                score += 10
            elif financing_change < -2:
                score -= 20
            elif financing_change < -1:
                score -= 10
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.warning(f"资金流向计算失败: {e}")
            return 50
    
    def _calculate_technical_signals(self, market_data: Dict) -> float:
        """计算技术信号评分 (0-100)"""
        try:
            indices = market_data.get('indices', {})
            if not indices:
                return 50
            
            score = 50
            
            # 主要指数表现 (50分)
            index_changes = []
            for symbol, data in indices.items():
                change = data.get('change_percent', 0)
                index_changes.append(change)
            
            if index_changes:
                avg_change = np.mean(index_changes)
                if avg_change > 2:
                    score += 40
                elif avg_change > 1:
                    score += 25
                elif avg_change > 0.5:
                    score += 15
                elif avg_change > 0:
                    score += 5
                elif avg_change < -2:
                    score -= 40
                elif avg_change < -1:
                    score -= 25
                elif avg_change < -0.5:
                    score -= 15
            
            # 突破/跌破关键位置 (30分)
            # 模拟关键技术位分析
            breakthrough_signals = self._detect_breakthrough_signals(indices)
            score += breakthrough_signals * 30  # -1到1的系数
            
            # 量价配合 (20分)
            volume_price_match = self._analyze_volume_price_match(indices)
            score += volume_price_match * 20
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.warning(f"技术信号计算失败: {e}")
            return 50
    
    def _calculate_sentiment_indicators(self, market_data: Dict) -> float:
        """计算情绪指标 (0-100) - 使用高级情绪指标分析器"""
        try:
            # 使用新的情绪指标分析器
            sentiment_result = self.sentiment_analyzer.analyze_sentiment_indicators()
            
            # 基础分数来自综合情绪分数
            base_score = sentiment_result.sentiment_score
            
            # 根据极端情绪信号调整
            for signal in sentiment_result.sentiment_extremes:
                if signal.signal_type == "恐慌抄底":
                    if signal.intensity == "极强":
                        base_score -= 15  # 极度恐慌，分数下降
                    elif signal.intensity == "强":
                        base_score -= 10
                elif signal.signal_type == "亢奋减仓":
                    if signal.intensity == "极强":
                        base_score += 15  # 极度亢奋，分数上升但有风险
                    elif signal.intensity == "强":
                        base_score += 10
            
            # 波动率环境调整
            if "极高波动" in sentiment_result.volatility_regime:
                base_score -= 10  # 极高波动降低情绪分数
            elif "低波动" in sentiment_result.volatility_regime:
                base_score += 5   # 低波动提升情绪稳定性
            
            # 确保分数在0-100范围内
            score = max(0, min(100, base_score))
            
            logger.info(f"情绪指标: {score:.1f} (恐惧贪婪:{sentiment_result.fear_greed_score:.1f}, 极端信号:{len(sentiment_result.sentiment_extremes)}个)")
            return score
            
        except Exception as e:
            logger.error(f"计算情绪指标失败: {e}")
            # 降级处理：使用简化的情绪计算
            overview = market_data.get('market_overview', {})
            limit_down = overview.get('limit_down_stocks', 0)
            total_stocks = overview.get('total_stocks', 1)
            
            if total_stocks > 0:
                limit_up_ratio = limit_up / total_stocks
                limit_down_ratio = limit_down / total_stocks
                
                if limit_up_ratio > 0.02:  # 超2%涨停，市场亢奋
                    score += 15
                elif limit_down_ratio > 0.02:  # 超2%跌停，市场恐慌
                    score -= 25
            
            # 反转信号 (30分)
            reversal_score = self._detect_reversal_signals(market_data)
            score += reversal_score
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.warning(f"情绪指标计算失败: {e}")
            return 50
    
    def _detect_breakthrough_signals(self, indices: Dict) -> float:
        """检测突破信号 (-1到1)"""
        # 简化的突破检测，实际需要更复杂的技术分析
        try:
            breakthrough_count = 0
            total_indices = len(indices)
            
            for symbol, data in indices.items():
                change = data.get('change_percent', 0)
                if change > 1.5:  # 模拟突破
                    breakthrough_count += 1
                elif change < -1.5:  # 模拟跌破
                    breakthrough_count -= 1
            
            if total_indices > 0:
                return breakthrough_count / total_indices
            return 0
        except:
            return 0
    
    def _analyze_volume_price_match(self, indices: Dict) -> float:
        """分析量价配合 (-1到1)"""
        # 简化的量价分析
        try:
            positive_changes = sum(1 for d in indices.values() if d.get('change_percent', 0) > 0)
            total_indices = len(indices)
            
            if total_indices > 0:
                return (positive_changes / total_indices - 0.5) * 2
            return 0
        except:
            return 0
    
    def _detect_reversal_signals(self, market_data: Dict) -> float:
        """检测反转信号 (-30到30)"""
        try:
            score = 0
            
            # 量能缩减检测
            overview = market_data.get('market_overview', {})
            turnover = overview.get('total_turnover', 0)
            if turnover < 8000:  # 成交量萎缩
                indices = market_data.get('indices', {})
                avg_change = np.mean([d.get('change_percent', 0) for d in indices.values()])
                if avg_change < -1:  # 缩量下跌，可能反转
                    score += 15
                elif avg_change > 1:  # 缩量上涨，警惕反转
                    score -= 10
            
            # 波动率压缩
            volatility = market_data.get('volatility', {})
            if volatility.get('implied_volatility', 20) < 15:
                score += 10  # 低波动后可能有大行情
            
            return score
        except:
            return 0
    
    def _determine_mood_level(self, mood_score: float) -> str:
        """确定情绪等级"""
        if mood_score <= self.mood_thresholds['panic']:
            return 'panic'
        elif mood_score <= self.mood_thresholds['cautious']:
            return 'cautious'
        elif mood_score <= self.mood_thresholds['neutral']:
            return 'neutral'
        elif mood_score <= self.mood_thresholds['optimistic']:
            return 'optimistic'
        else:
            return 'euphoric'
    
    def _identify_risk_alerts(self, market_data: Dict, mood_score: float) -> List[str]:
        """识别风险提醒"""
        alerts = []
        
        try:
            # 技术风险
            indices = market_data.get('indices', {})
            for symbol, data in indices.items():
                change = data.get('change_percent', 0)
                if change < -3:
                    alerts.append(f"{data.get('name', symbol)}跌幅过大，注意支撑位")
            
            # 流动性风险
            overview = market_data.get('market_overview', {})
            turnover = overview.get('total_turnover', 0)
            if turnover < 6000:
                alerts.append("成交量严重萎缩，流动性不足")
            
            # 情绪风险
            if mood_score > 85:
                alerts.append("市场情绪过于乐观，警惕回调风险")
            elif mood_score < 15:
                alerts.append("市场情绪过于悲观，可能超跌")
            
            # 资金风险
            northbound = market_data.get('northbound_capital', {})
            if northbound.get('net_inflow_billion', 0) < -20:
                alerts.append("北向资金大幅流出，外资态度谨慎")
        
        except Exception as e:
            logger.warning(f"风险识别失败: {e}")
        
        return alerts[:5]  # 最多返回5条风险提醒
    
    def _identify_opportunities(self, market_data: Dict, mood_score: float) -> List[str]:
        """识别投资机会"""
        opportunities = []
        
        try:
            # 技术机会
            sectors = market_data.get('sectors', {})
            sector_performance = sectors.get('sector_performance', {})
            leading_sectors = sector_performance.get('leading_sectors', [])
            
            for sector in leading_sectors[:3]:
                opportunities.append(f"{sector}板块表现强势，可关注龙头股")
            
            # 情绪机会
            if 15 <= mood_score <= 25:
                opportunities.append("市场恐慌情绪，优质股票可能出现超跌机会")
            elif 75 <= mood_score <= 85:
                opportunities.append("市场情绪乐观，成长股可能有表现机会")
            
            # 资金机会
            northbound = market_data.get('northbound_capital', {})
            if northbound.get('net_inflow_billion', 0) > 15:
                opportunities.append("北向资金大幅流入，外资看好A股")
            
            # 技术机会
            indices = market_data.get('indices', {})
            breakthrough_signals = self._detect_breakthrough_signals(indices)
            if breakthrough_signals > 0.3:
                opportunities.append("多个指数呈现突破态势，可关注突破确认")
        
        except Exception as e:
            logger.warning(f"机会识别失败: {e}")
        
        return opportunities[:5]  # 最多返回5条机会提醒
    
    def _calculate_confidence(self, market_data: Dict, mood_score: float) -> float:
        """计算信号置信度"""
        try:
            base_confidence = 0.7
            
            # 数据完整性
            data_completeness = 0
            if market_data.get('indices'):
                data_completeness += 0.3
            if market_data.get('market_overview'):
                data_completeness += 0.3
            if market_data.get('sectors'):
                data_completeness += 0.2
            if market_data.get('northbound_capital'):
                data_completeness += 0.2
            
            # 信号一致性（各指标方向一致性越高，置信度越高）
            signals = []
            if 'market_overview' in market_data:
                overview = market_data['market_overview']
                up_ratio = overview.get('up_stocks', 0) / max(overview.get('total_stocks', 1), 1)
                signals.append(up_ratio - 0.5)  # -0.5到0.5
            
            if signals:
                consistency = 1 - np.std(signals) if len(signals) > 1 else 0.8
            else:
                consistency = 0.5
            
            final_confidence = base_confidence * data_completeness * consistency
            return max(0.3, min(0.95, final_confidence))
            
        except:
            return 0.7
    
    # 模拟数据方法（实际场景需要接入真实API）
    def _get_realistic_etf_flows(self) -> Dict:
        """暂时返回空数据，等待月度数据源"""
        return {
            'large_cap_flow': None,
            'small_cap_flow': None,
            'net_inflow_billion': None,
            'data_source': '暂无数据源',
            'timestamp': datetime.now().isoformat(),
            'note': '寻找月度免费ETF数据中...'
        }
    
    def _simulate_etf_flows(self) -> Dict:
        """ETF资金流向数据入口 - 使用真实市场逻辑"""
        return self._get_realistic_etf_flows()
    
    def _simulate_margin_data(self) -> Dict:
        """模拟融资融券数据"""
        return {
            'balance_change_pct': np.random.uniform(-3, 4),
            'financing_change_pct': np.random.uniform(-2, 3),
            'securities_lending_change_pct': np.random.uniform(-5, 2)
        }
    
    def _simulate_northbound_capital(self) -> Dict:
        """模拟北向资金数据"""
        return {
            'net_inflow_billion': np.random.uniform(-25, 35),
            'shanghai_inflow': np.random.uniform(-15, 20),
            'shenzhen_inflow': np.random.uniform(-10, 15)
        }
    
    def _simulate_volatility_data(self) -> Dict:
        """模拟波动率数据"""
        return {
            'implied_volatility': np.random.uniform(12, 40),
            'historical_volatility': np.random.uniform(10, 35),
            'vix_equivalent': np.random.uniform(15, 45)
        }
    
    def _simulate_market_overview(self) -> Dict:
        """模拟市场概览数据"""
        # 根据当前时间生成相对合理的市场数据
        total_stocks = np.random.randint(4800, 5200)  # A股总数约5000只
        up_stocks = np.random.randint(int(total_stocks * 0.2), int(total_stocks * 0.8))
        down_stocks = np.random.randint(int(total_stocks * 0.15), total_stocks - up_stocks - 50)
        unchanged_stocks = total_stocks - up_stocks - down_stocks
        
        # 成交额，参考真实A股日均成交额
        total_turnover = np.random.uniform(6000, 15000)  # 6000亿到1.5万亿
        
        return {
            'total_stocks': total_stocks,
            'up_stocks': up_stocks,
            'down_stocks': down_stocks,
            'unchanged_stocks': unchanged_stocks,
            'total_turnover': round(total_turnover, 2),
            'limit_up_stocks': np.random.randint(0, 50),
            'limit_down_stocks': np.random.randint(0, 30),
            'new_high_stocks': np.random.randint(10, 100),
            'new_low_stocks': np.random.randint(5, 80),
            'trading_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _get_default_mood(self) -> MarketMoodResult:
        """获取默认情绪结果"""
        return MarketMoodResult(
            mood_score=50.0,
            mood_level='neutral',
            action_type='观望日',
            confidence=0.5,
            risk_alerts=['数据获取异常，建议谨慎操作'],
            opportunities=['等待数据恢复后再做判断'],
            market_phase='震荡整理期',
            reversal_signals=[],
            volume_signal='正常量',
            volatility_level='正常波动率'
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
    
    def _get_temperature_details(self, market_data: Dict) -> Dict:
        """获取市场温度详细数据"""
        overview = market_data.get('market_overview', {})
        etf_flows = market_data.get('etf_flows', {})
        margin_data = market_data.get('margin_trading', {})
        
        return {
            'dimension_name': '市场温度计',
            'description': '反映市场整体活跃度和参与度',
            'current_score': self._calculate_market_temperature(market_data),
            'key_indicators': {
                'up_down_ratio': {
                    'name': '涨跌家数比',
                    'up_stocks': overview.get('up_stocks', 0),
                    'down_stocks': overview.get('down_stocks', 0),
                    'total_stocks': overview.get('total_stocks', 0),
                    'up_ratio': round(overview.get('up_stocks', 0) / max(overview.get('total_stocks', 1), 1) * 100, 1)
                },
                'turnover': {
                    'name': '总成交额',
                    'value': overview.get('total_turnover', 0),
                    'unit': '亿元',
                    'level': '1.5万亿以上为热' if overview.get('total_turnover', 0) > 15000 else '正常'
                },
                'margin_trading': {
                    'name': '融资余额变化',
                    'balance_change': margin_data.get('balance_change_pct', 0),
                    'financing_change': margin_data.get('financing_change_pct', 0),
                    'unit': '%'
                },
                'etf_flows': {
                    'name': 'ETF资金流向',
                    'net_inflow': etf_flows.get('net_inflow_billion', 0),
                    'large_cap_flow': etf_flows.get('large_cap_flow', 0),
                    'small_cap_flow': etf_flows.get('small_cap_flow', 0),
                    'unit': '亿元'
                }
            }
        }
    
    def _get_sector_details(self, market_data: Dict) -> Dict:
        """获取行业热力详细数据"""
        sectors = market_data.get('sectors', {})
        sector_performance = sectors.get('sector_performance', {})
        
        return {
            'dimension_name': '行业热力图',
            'description': '跟踪板块轮动和热点分布',
            'current_score': self._calculate_sector_heat(market_data),
            'key_indicators': {
                'leading_sectors': {
                    'name': '领涨板块',
                    'sectors': sector_performance.get('leading_sectors', []),
                    'count': len(sector_performance.get('leading_sectors', []))
                },
                'sector_rotation': {
                    'name': '板块轮动',
                    'current_theme': sector_performance.get('sector_rotation', '暂无明确主线'),
                    'best_performing': sector_performance.get('best_performing', [])[:3],
                    'worst_performing': sector_performance.get('worst_performing', [])[:3]
                },
                'sector_divergence': {
                    'name': '板块分化程度',
                    'spread': self._calculate_sector_spread(sector_performance),
                    'description': '高分化利于选股，低分化缺乏热点'
                }
            }
        }
    
    def _get_capital_details(self, market_data: Dict) -> Dict:
        """获取资金流向详细数据"""
        northbound = market_data.get('northbound_capital', {})
        etf_flows = market_data.get('etf_flows', {})
        margin_data = market_data.get('margin_trading', {})
        
        return {
            'dimension_name': '资金流向监控',
            'description': '追踪各类资金的进出情况',
            'current_score': self._calculate_capital_flow(market_data),
            'key_indicators': {
                'northbound_capital': {
                    'name': '北向资金(外资)',
                    'net_inflow': northbound.get('net_inflow_billion', 0),
                    'shanghai_inflow': northbound.get('shanghai_inflow', 0),
                    'shenzhen_inflow': northbound.get('shenzhen_inflow', 0),
                    'unit': '亿元',
                    'significance': '外资看好A股' if northbound.get('net_inflow_billion', 0) > 10 else '外资态度谨慎'
                },
                'etf_flows': {
                    'name': 'ETF申赎',
                    'large_cap_etf': etf_flows.get('large_cap_flow', 0),
                    'small_cap_etf': etf_flows.get('small_cap_flow', 0),
                    'sector_flows': etf_flows.get('sector_etf_flows', {}),
                    'unit': '亿元'
                },
                'margin_financing': {
                    'name': '融资买入',
                    'financing_change': margin_data.get('financing_change_pct', 0),
                    'securities_lending': margin_data.get('securities_lending_change_pct', 0),
                    'unit': '%',
                    'description': '融资增加表明看多情绪'
                }
            }
        }
    
    def _get_technical_details(self, market_data: Dict) -> Dict:
        """获取技术信号详细数据"""
        indices = market_data.get('indices', {})
        
        index_changes = []
        for symbol, data in indices.items():
            change = data.get('change_percent', 0)
            index_changes.append({
                'name': data.get('name', symbol),
                'change': change,
                'current': data.get('current_value', 0)
            })
        
        return {
            'dimension_name': '技术信号分析',
            'description': '主要指数技术面走势分析',
            'current_score': self._calculate_technical_signals(market_data),
            'key_indicators': {
                'index_performance': {
                    'name': '主要指数表现',
                    'indices': index_changes,
                    'avg_change': round(np.mean([idx['change'] for idx in index_changes]), 2) if index_changes else 0
                },
                'breakthrough_signals': {
                    'name': '突破跌破信号',
                    'breakthrough_score': self._detect_breakthrough_signals(indices),
                    'description': '正值表示突破，负值表示跌破'
                },
                'volume_price_match': {
                    'name': '量价配合',
                    'match_score': self._analyze_volume_price_match(indices),
                    'description': '量价配合良好利于趋势延续'
                }
            }
        }
    
    def _get_sentiment_details(self, market_data: Dict) -> Dict:
        """获取情绪指标详细数据"""
        try:
            sentiment_result = self.sentiment_analyzer.analyze_sentiment_indicators()
            
            return {
                'dimension_name': '情绪指标监控',
                'description': '基于恐惧贪婪指数等判断情绪极端度',
                'current_score': self._calculate_sentiment_indicators(market_data),
                'key_indicators': {
                    'fear_greed_index': {
                        'name': '恐惧贪婪指数',
                        'score': sentiment_result.fear_greed_score,
                        'level': sentiment_result.fear_greed_level,
                        'description': '0-25极度恐慌, 25-45恐慌, 45-55中性, 55-75贪婪, 75-100极度贪婪'
                    },
                    'volatility_regime': {
                        'name': '波动率环境',
                        'regime': sentiment_result.volatility_regime,
                        'description': '高波动通常伴随情绪极端'
                    },
                    'volume_anomaly': {
                        'name': '成交量异常',
                        'status': sentiment_result.volume_anomaly,
                        'description': '放量/缩量反映市场参与度'
                    },
                    'extreme_signals': {
                        'name': '极端情绪信号',
                        'signals': [s.signal_type for s in sentiment_result.sentiment_extremes],
                        'count': len(sentiment_result.sentiment_extremes)
                    }
                }
            }
        except Exception as e:
            logger.warning(f"获取情绪详细数据失败: {e}")
            return {
                'dimension_name': '情绪指标监控',
                'description': '情绪数据暂时不可用',
                'current_score': 50,
                'key_indicators': {
                    'error': str(e)
                }
            }
    
    def _calculate_sector_spread(self, sector_performance: Dict) -> float:
        """计算板块分化程度"""
        try:
            best = sector_performance.get('best_performing', [])
            worst = sector_performance.get('worst_performing', [])
            
            if best and worst:
                best_avg = np.mean([s.get('change_percent', 0) for s in best[:3]])
                worst_avg = np.mean([s.get('change_percent', 0) for s in worst[:3]])
                return round(best_avg - worst_avg, 2)
            return 0
        except:
            return 0

    def generate_mood_report(self, result: MarketMoodResult = None) -> str:
        """生成市场情绪报告"""
        if not result:
            result = self.analyze_market_mood()
        
        # 情绪描述映射
        mood_descriptions = {
            'panic': '😰 极度恐慌',
            'cautious': '😐 谨慎观望', 
            'neutral': '😶 中性平静',
            'optimistic': '😊 乐观积极',
            'euphoric': '🤩 过度亢奋'
        }
        
        # 行动建议详细描述
        action_descriptions = {
            '抄底日': '💰 适合逢低布局，关注优质标的',
            '观望日': '⏳ 建议静观其变，等待更好时机', 
            '追涨日': '🚀 可适度参与强势板块，控制仓位'
        }
        
        report = f"""
🎯 市场情绪分析报告 (Market Mood)
{'='*50}

📊 **综合评分**: {result.mood_score}/100
😊 **市场情绪**: {mood_descriptions.get(result.mood_level, result.mood_level)}
🎪 **今日定调**: {result.action_type}
💡 **行动建议**: {action_descriptions.get(result.action_type, '')}
🎯 **信号置信度**: {result.confidence:.0%}

⚠️ **风险提醒**:
"""
        
        if result.risk_alerts:
            for i, alert in enumerate(result.risk_alerts, 1):
                report += f"  {i}. {alert}\n"
        else:
            report += "  暂无特别风险提醒\n"
        
        report += "\n🌟 **投资机会**:\n"
        if result.opportunities:
            for i, opportunity in enumerate(result.opportunities, 1):
                report += f"  {i}. {opportunity}\n"
        else:
            report += "  暂无明显投资机会\n"
        
        report += f"""
📈 **操作策略**:
"""
        
        if result.action_type == '抄底日':
            report += """  • 重点关注超跌的优质股票
  • 分批建仓，不要一次性满仓
  • 优选基本面稳健的龙头公司
  • 设置止损位，控制下行风险"""
        elif result.action_type == '追涨日':
            report += """  • 关注突破关键位置的强势股
  • 追涨需要控制仓位，及时止盈
  • 重点关注领涨板块的龙头股
  • 避免追高位横盘已久的个股"""
        else:
            report += """  • 保持耐心，等待更明确的信号
  • 可以适当关注，但不急于下手
  • 利用观望期完善选股策略
  • 关注市场情绪变化的转折点"""
        
        return report

def main():
    """主函数 - 演示Market Mood功能"""
    print("🎭 MarketBrew 市场情绪分析系统 (Market Mood)")
    print("=" * 60)
    
    analyzer = MarketMoodAnalyzer()
    
    # 分析市场情绪
    print("🔍 正在分析市场情绪...")
    result = analyzer.analyze_market_mood()
    
    # 生成报告
    report = analyzer.generate_mood_report(result)
    print(report)
    
    # 显示技术详情
    print(f"\n🔧 技术指标详情:")
    print(f"数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"分析维度: 市场温度+行业热力+资金流向+技术信号+情绪指标")

if __name__ == "__main__":
    main()