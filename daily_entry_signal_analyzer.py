#!/usr/bin/env python3
"""
当日进场信号分析器
基于多维度市场数据判断当天是否适合进场交易
"""

import requests
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DailyEntrySignalAnalyzer:
    """当日进场信号分析器"""
    
    def __init__(self):
        self.market_index_url = "http://localhost:5008"
        self.price_service_url = "http://localhost:5002"
        
        # 评分权重配置
        self.weights = {
            'market_sentiment': 0.30,   # 市场情绪权重
            'capital_flow': 0.25,       # 资金流向权重
            'technical_pattern': 0.20,  # 技术形态权重
            'volatility_risk': 0.15,    # 波动率风险权重
            'stock_quality': 0.10       # 个股质量权重
        }
        
        # 一票否决条件
        self.veto_conditions = {
            'extreme_panic': {'limit_down_ratio': 0.05},  # 跌停股超过5%
            'volume_drought': {'turnover_ratio': 0.3},    # 成交量萎缩70%
            'index_crash': {'major_index_drop': -3.0}     # 主要指数跌超3%
        }
        
        self.cache = {}
        self.cache_duration = 60  # 1分钟缓存
        
    def analyze_daily_entry_signal(self) -> Dict[str, Any]:
        """分析当日进场信号"""
        try:
            # 获取市场数据
            market_data = self._get_market_data()
            if not market_data:
                return self._get_default_result("数据获取失败")
            
            # 计算各维度得分
            scores = {}
            scores['market_sentiment'] = self._calculate_market_sentiment_score(market_data)
            scores['capital_flow'] = self._calculate_capital_flow_score(market_data)
            scores['technical_pattern'] = self._calculate_technical_pattern_score(market_data)
            scores['volatility_risk'] = self._calculate_volatility_risk_score(market_data)
            scores['stock_quality'] = self._calculate_stock_quality_score(market_data)
            
            # 检查一票否决条件
            veto_check = self._check_veto_conditions(market_data)
            
            # 计算综合得分
            weighted_score = sum(scores[key] * self.weights[key] for key in scores)
            
            # 生成最终建议
            recommendation = self._generate_recommendation(weighted_score, veto_check, scores)
            
            result = {
                'timestamp': datetime.now().isoformat(),
                'overall_score': round(weighted_score, 1),
                'dimension_scores': scores,
                'veto_check': veto_check,
                'recommendation': recommendation,
                'market_summary': self._generate_market_summary(market_data),
                'confidence_level': self._calculate_confidence_level(scores, market_data)
            }
            
            logger.info(f"📊 进场信号分析完成: 综合得分{weighted_score:.1f}, 建议: {recommendation['action']}")
            return result
            
        except Exception as e:
            logger.error(f"进场信号分析失败: {e}")
            return self._get_default_result(f"分析异常: {str(e)}")
    
    def _get_market_data(self) -> Optional[Dict]:
        """获取市场数据"""
        cache_key = "market_data"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            # 获取主要指数数据
            response = requests.get(f"{self.market_index_url}/api/main-indices", timeout=10)
            if response.status_code == 200:
                indices_data = response.json()
            else:
                logger.warning("无法获取主要指数数据")
                indices_data = {}
            
            # 获取行业数据
            response = requests.get(f"{self.market_index_url}/api/sector-indices", timeout=10)
            if response.status_code == 200:
                sector_data = response.json()
            else:
                logger.warning("无法获取行业数据")
                sector_data = {}
            
            # 整合数据
            market_data = {
                'indices': indices_data.get('indices', {}),
                'market_overview': indices_data.get('market_overview', {}),
                'market_status': indices_data.get('market_status', {}),
                'sector_data': sector_data,
                'timestamp': datetime.now().isoformat()
            }
            
            # 缓存数据
            self.cache[cache_key] = market_data
            self._set_cache_time(cache_key)
            
            return market_data
            
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return None
    
    def _calculate_market_sentiment_score(self, market_data: Dict) -> float:
        """计算市场情绪得分 (0-100)"""
        try:
            overview = market_data.get('market_overview', {})
            
            # 检查是否有真实涨跌数据
            up_stocks = overview.get('up_stocks', 0)
            down_stocks = overview.get('down_stocks', 0)
            total_stocks = overview.get('total_stocks', 0)
            
            if total_stocks == 0 or up_stocks == 0:
                logger.warning("🚫 无法获取真实涨跌数据，使用指数数据计算情绪")
                return self._calculate_sentiment_from_indices(market_data)
            
            # 基础指标
            limit_up = overview.get('limit_up_stocks', 0)
            limit_down = overview.get('limit_down_stocks', 0)
            
            # 涨跌比例得分 (40分)
            up_ratio = up_stocks / total_stocks if total_stocks > 0 else 0
            if up_ratio > 0.7:
                ratio_score = 40
            elif up_ratio > 0.6:
                ratio_score = 35
            elif up_ratio > 0.5:
                ratio_score = 25
            elif up_ratio > 0.4:
                ratio_score = 15
            else:
                ratio_score = 0
            
            # 涨跌停比例得分 (30分)
            limit_ratio = (limit_up - limit_down) / total_stocks if total_stocks > 0 else 0
            if limit_ratio > 0.02:
                limit_score = 30
            elif limit_ratio > 0.01:
                limit_score = 20
            elif limit_ratio > 0:
                limit_score = 10
            elif limit_ratio > -0.01:
                limit_score = 5
            else:
                limit_score = 0
            
            # 市场情绪得分 (30分)
            sentiment = overview.get('market_sentiment', '震荡')
            if sentiment == '强势':
                sentiment_score = 30
            elif sentiment == '震荡':
                sentiment_score = 15
            else:
                sentiment_score = 0
            
            total_score = ratio_score + limit_score + sentiment_score
            return min(total_score, 100)
            
        except Exception as e:
            logger.warning(f"市场情绪计算失败: {e}")
            return 50  # 默认中性得分
    
    def _calculate_sentiment_from_indices(self, market_data: Dict) -> float:
        """基于指数数据计算市场情绪得分"""
        try:
            indices = market_data.get('indices', {})
            if not indices:
                return 50
            
            # 计算主要指数平均涨跌幅
            changes = []
            for symbol, data in indices.items():
                change = data.get('change_percent', 0)
                changes.append(change)
            
            if not changes:
                return 50
                
            avg_change = sum(changes) / len(changes)
            
            # 基于指数表现评分
            if avg_change > 2:
                return 85  # 强势
            elif avg_change > 1:
                return 70  # 较好
            elif avg_change > 0.5:
                return 60  # 偏好
            elif avg_change > 0:
                return 55  # 微涨
            elif avg_change > -0.5:
                return 45  # 微跌
            elif avg_change > -1:
                return 30  # 偏弱
            elif avg_change > -2:
                return 20  # 较弱
            else:
                return 10  # 大跌
                
        except Exception as e:
            logger.warning(f"指数情绪计算失败: {e}")
            return 50
    
    def _calculate_capital_flow_score(self, market_data: Dict) -> float:
        """计算资金流向得分 (0-100)"""
        try:
            overview = market_data.get('market_overview', {})
            
            # 成交量得分 (50分)
            turnover = overview.get('total_turnover', 0)
            if turnover > 12000:  # 超过1.2万亿
                volume_score = 50
            elif turnover > 10000:
                volume_score = 40
            elif turnover > 8000:
                volume_score = 30
            elif turnover > 6000:
                volume_score = 20
            else:
                volume_score = 10
            
            # 换手率得分 (30分)
            turnover_rate = overview.get('turnover_rate', 0)
            if turnover_rate > 2.0:
                rate_score = 30
            elif turnover_rate > 1.5:
                rate_score = 25
            elif turnover_rate > 1.0:
                rate_score = 20
            elif turnover_rate > 0.8:
                rate_score = 15
            else:
                rate_score = 5
            
            # 资金情绪得分 (20分)
            up_down_ratio = overview.get('up_down_ratio', 0.5)
            if up_down_ratio > 2.0:
                flow_score = 20
            elif up_down_ratio > 1.5:
                flow_score = 15
            elif up_down_ratio > 1.0:
                flow_score = 10
            else:
                flow_score = 5
            
            total_score = volume_score + rate_score + flow_score
            return min(total_score, 100)
            
        except Exception as e:
            logger.warning(f"资金流向计算失败: {e}")
            return 50
    
    def _calculate_technical_pattern_score(self, market_data: Dict) -> float:
        """计算技术形态得分 (0-100)"""
        try:
            indices = market_data.get('indices', {})
            market_status = market_data.get('market_status', {})
            
            # 主要指数技术得分 (60分)
            index_scores = []
            for symbol, data in indices.items():
                change_pct = data.get('change_percent', 0)
                if change_pct > 2.0:
                    index_scores.append(20)
                elif change_pct > 1.0:
                    index_scores.append(15)
                elif change_pct > 0.5:
                    index_scores.append(10)
                elif change_pct > -0.5:
                    index_scores.append(5)
                else:
                    index_scores.append(0)
            
            avg_index_score = np.mean(index_scores) if index_scores else 5
            
            # 市场趋势得分 (40分)
            trend = market_status.get('trend', 'sideways')
            if trend == 'bullish':
                trend_score = 40
            elif trend == 'mild_bullish':
                trend_score = 30
            elif trend == 'sideways':
                trend_score = 20
            elif trend == 'mild_bearish':
                trend_score = 10
            else:
                trend_score = 0
            
            total_score = avg_index_score * 3 + trend_score  # 60分 + 40分
            return min(total_score, 100)
            
        except Exception as e:
            logger.warning(f"技术形态计算失败: {e}")
            return 50
    
    def _calculate_volatility_risk_score(self, market_data: Dict) -> float:
        """计算波动率风险得分 (0-100, 越低风险越大)"""
        try:
            overview = market_data.get('market_overview', {})
            indices = market_data.get('indices', {})
            
            # 涨跌停风险 (40分)
            total_stocks = overview.get('total_stocks', 1)
            limit_down = overview.get('limit_down_stocks', 0)
            limit_up = overview.get('limit_up_stocks', 0)
            
            limit_down_ratio = limit_down / total_stocks if total_stocks > 0 else 0
            if limit_down_ratio > 0.03:  # 跌停超3%
                risk_score = 0
            elif limit_down_ratio > 0.02:
                risk_score = 10
            elif limit_down_ratio > 0.01:
                risk_score = 20
            else:
                risk_score = 40
            
            # 指数波动风险 (30分)
            max_drop = 0
            for symbol, data in indices.items():
                change_pct = data.get('change_percent', 0)
                if change_pct < max_drop:
                    max_drop = change_pct
            
            if max_drop < -4:
                volatility_score = 0
            elif max_drop < -3:
                volatility_score = 10
            elif max_drop < -2:
                volatility_score = 20
            else:
                volatility_score = 30
            
            # 市场恐慌指标 (30分)
            sentiment = overview.get('market_sentiment', '震荡')
            if sentiment == '弱势':
                panic_score = 0
            elif sentiment == '震荡':
                panic_score = 15
            else:
                panic_score = 30
            
            total_score = risk_score + volatility_score + panic_score
            return min(total_score, 100)
            
        except Exception as e:
            logger.warning(f"风险评估计算失败: {e}")
            return 50
    
    def _calculate_stock_quality_score(self, market_data: Dict) -> float:
        """计算个股质量得分 (0-100)"""
        try:
            overview = market_data.get('market_overview', {})
            sector_data = market_data.get('sector_data', {})
            
            # 强势股比例 (50分)
            up_stocks = overview.get('up_stocks', 0)
            total_stocks = overview.get('total_stocks', 1)
            strong_ratio = up_stocks / total_stocks if total_stocks > 0 else 0
            
            if strong_ratio > 0.6:
                quality_score = 50
            elif strong_ratio > 0.5:
                quality_score = 40
            elif strong_ratio > 0.4:
                quality_score = 30
            else:
                quality_score = 15
            
            # 板块活跃度 (30分)
            sector_performance = sector_data.get('sector_performance', {})
            leading_sectors = len(sector_performance.get('leading_sectors', []))
            if leading_sectors >= 3:
                sector_score = 30
            elif leading_sectors >= 2:
                sector_score = 20
            elif leading_sectors >= 1:
                sector_score = 10
            else:
                sector_score = 5
            
            # 涨停板质量 (20分)
            limit_up = overview.get('limit_up_stocks', 0)
            if limit_up > 50:
                limit_score = 20
            elif limit_up > 30:
                limit_score = 15
            elif limit_up > 15:
                limit_score = 10
            else:
                limit_score = 5
            
            total_score = quality_score + sector_score + limit_score
            return min(total_score, 100)
            
        except Exception as e:
            logger.warning(f"个股质量计算失败: {e}")
            return 50
    
    def _check_veto_conditions(self, market_data: Dict) -> Dict[str, Any]:
        """检查一票否决条件"""
        veto_triggered = False
        veto_reasons = []
        
        try:
            overview = market_data.get('market_overview', {})
            indices = market_data.get('indices', {})
            
            # 检查极端恐慌
            total_stocks = overview.get('total_stocks', 1)
            limit_down = overview.get('limit_down_stocks', 0)
            limit_down_ratio = limit_down / total_stocks if total_stocks > 0 else 0
            
            if limit_down_ratio > self.veto_conditions['extreme_panic']['limit_down_ratio']:
                veto_triggered = True
                veto_reasons.append(f"跌停股比例过高: {limit_down_ratio:.2%}")
            
            # 检查成交量萎缩 (仅在有真实数据时检查)
            turnover = overview.get('total_turnover', 0)
            if overview and turnover > 0 and turnover < 5000:  # 低于5000亿
                veto_triggered = True
                veto_reasons.append(f"成交量严重萎缩: {turnover}亿")
            
            # 检查主要指数暴跌
            for symbol, data in indices.items():
                change_pct = data.get('change_percent', 0)
                if change_pct < self.veto_conditions['index_crash']['major_index_drop']:
                    veto_triggered = True
                    veto_reasons.append(f"{data.get('name', symbol)}跌幅过大: {change_pct:.2f}%")
                    break
            
        except Exception as e:
            logger.warning(f"一票否决检查失败: {e}")
        
        return {
            'triggered': veto_triggered,
            'reasons': veto_reasons
        }
    
    def _generate_recommendation(self, score: float, veto_check: Dict, scores: Dict) -> Dict[str, Any]:
        """生成投资建议"""
        
        # 一票否决优先
        if veto_check['triggered']:
            return {
                'action': '强烈观望',
                'reason': f"系统性风险: {'; '.join(veto_check['reasons'])}",
                'position_size': 0,
                'confidence': 0.9
            }
        
        # 综合得分判断
        if score >= 75:
            return {
                'action': '积极进场',
                'reason': f'多项指标优秀(得分{score:.1f}), 市场情绪积极, 建议积极布局',
                'position_size': 0.8,
                'confidence': 0.85
            }
        elif score >= 60:
            return {
                'action': '谨慎进场',
                'reason': f'指标良好(得分{score:.1f}), 可适量参与, 注意风险控制',
                'position_size': 0.5,
                'confidence': 0.7
            }
        elif score >= 40:
            return {
                'action': '轻仓试探',
                'reason': f'指标一般(得分{score:.1f}), 可小仓位试探, 严控风险',
                'position_size': 0.2,
                'confidence': 0.5
            }
        else:
            return {
                'action': '建议观望',
                'reason': f'指标偏弱(得分{score:.1f}), 建议观望等待更好机会',
                'position_size': 0,
                'confidence': 0.8
            }
    
    def _generate_market_summary(self, market_data: Dict) -> str:
        """生成市场摘要"""
        try:
            overview = market_data.get('market_overview', {})
            market_status = market_data.get('market_status', {})
            
            up_stocks = overview.get('up_stocks', 0)
            down_stocks = overview.get('down_stocks', 0)
            turnover = overview.get('total_turnover', 0)
            sentiment = overview.get('market_sentiment', '震荡')
            description = market_status.get('description', '市场震荡整理')
            
            return f"📊 市场概况: {description} | " \
                   f"涨跌分布: {up_stocks}涨{down_stocks}跌 | " \
                   f"成交量: {turnover:.0f}亿 | " \
                   f"整体情绪: {sentiment}"
        except:
            return "市场数据获取中..."
    
    def _calculate_confidence_level(self, scores: Dict, market_data: Dict) -> float:
        """计算信号置信度"""
        try:
            # 基于数据质量和指标一致性计算置信度
            data_quality = 1.0 if market_data.get('market_overview') else 0.5
            
            # 指标一致性(方差越小置信度越高)
            score_variance = np.var(list(scores.values()))
            consistency = max(0, 1 - score_variance / 1000)
            
            confidence = (data_quality + consistency) / 2
            return round(confidence, 2)
        except:
            return 0.7
    
    def _get_default_result(self, error_msg: str) -> Dict[str, Any]:
        """获取默认结果"""
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_score': 50,
            'dimension_scores': {
                'market_sentiment': 50,
                'capital_flow': 50, 
                'technical_pattern': 50,
                'volatility_risk': 50,
                'stock_quality': 50
            },
            'veto_check': {'triggered': False, 'reasons': []},
            'recommendation': {
                'action': '数据异常',
                'reason': error_msg,
                'position_size': 0,
                'confidence': 0
            },
            'market_summary': error_msg,
            'confidence_level': 0.0
        }
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存有效性"""
        if cache_key not in self.cache:
            return False
        cache_time = getattr(self, f'{cache_key}_time', 0)
        return time.time() - cache_time < self.cache_duration
    
    def _set_cache_time(self, cache_key: str):
        """设置缓存时间"""
        setattr(self, f'{cache_key}_time', time.time())

if __name__ == "__main__":
    analyzer = DailyEntrySignalAnalyzer()
    result = analyzer.analyze_daily_entry_signal()
    
    print("🎯 当日进场信号分析结果")
    print("=" * 50)
    print(f"📊 综合得分: {result['overall_score']}/100")
    print(f"💡 投资建议: {result['recommendation']['action']}")
    print(f"📝 建议理由: {result['recommendation']['reason']}")
    print(f"📈 建议仓位: {result['recommendation']['position_size']*100:.0f}%")
    print(f"🎯 置信度: {result['confidence_level']*100:.0f}%")
    print(f"📰 {result['market_summary']}")
    
    if result['veto_check']['triggered']:
        print(f"⚠️ 风险提示: {'; '.join(result['veto_check']['reasons'])}")
    
    print("\n📊 各维度得分:")
    for dimension, score in result['dimension_scores'].items():
        print(f"  {dimension}: {score:.1f}/100")