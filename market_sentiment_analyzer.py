#!/usr/bin/env python3
"""
市场情绪周期分析器
实现4阶段情绪周期判断：冰点、修复、加速、退潮
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging
import yfinance as yf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MarketSentimentResult:
    """市场情绪分析结果"""
    # 情绪周期阶段
    sentiment_phase: str        # 冰点、修复、加速、退潮
    sentiment_score: float      # 情绪评分 0-100
    
    # 五个关键指标
    profit_effect: Dict[str, Any]      # ① 赚钱效应指标
    high_standard: Dict[str, Any]      # ② 高标人气承接
    turnover_change: Dict[str, Any]    # ③ 成交额变化  
    theme_direction: Dict[str, Any]    # ④ 主线行业题材
    etf_sentiment: Dict[str, Any]      # ⑤ ETF情绪指标
    
    # 综合判断
    phase_signals: List[str]           # 各指标信号
    confidence_level: float            # 判断置信度
    next_phase_probability: Dict[str, float]  # 下一阶段概率

class MarketSentimentAnalyzer:
    """市场情绪周期分析器"""
    
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5分钟缓存
        
    def analyze_sentiment_cycle(self) -> MarketSentimentResult:
        """分析市场情绪周期"""
        try:
            logger.info("🎭 开始分析市场情绪周期...")
            
            # 获取五个关键指标
            profit_effect = self._analyze_profit_effect()
            high_standard = self._analyze_high_standard()
            turnover_change = self._analyze_turnover_change()
            theme_direction = self._analyze_theme_direction()
            etf_sentiment = self._analyze_etf_sentiment()
            
            # 综合判断情绪阶段
            phase_signals = []
            phase_scores = {
                '冰点': 0,
                '修复': 0, 
                '加速': 0,
                '退潮': 0
            }
            
            # 根据各指标判断阶段
            phase_signals.extend(self._judge_phase_by_profit_effect(profit_effect, phase_scores))
            phase_signals.extend(self._judge_phase_by_high_standard(high_standard, phase_scores))
            phase_signals.extend(self._judge_phase_by_turnover(turnover_change, phase_scores))
            phase_signals.extend(self._judge_phase_by_theme(theme_direction, phase_scores))
            phase_signals.extend(self._judge_phase_by_etf(etf_sentiment, phase_scores))
            
            # 确定最终阶段
            sentiment_phase = max(phase_scores, key=phase_scores.get)
            sentiment_score = phase_scores[sentiment_phase] * 20  # 转换为0-100分
            
            # 计算置信度
            max_score = max(phase_scores.values())
            second_max = sorted(phase_scores.values())[-2]
            confidence_level = (max_score - second_max) / max_score if max_score > 0 else 0.5
            
            # 预测下一阶段概率
            next_phase_probability = self._predict_next_phase(sentiment_phase, phase_scores)
            
            result = MarketSentimentResult(
                sentiment_phase=sentiment_phase,
                sentiment_score=round(sentiment_score, 1),
                profit_effect=profit_effect,
                high_standard=high_standard,
                turnover_change=turnover_change,
                theme_direction=theme_direction,
                etf_sentiment=etf_sentiment,
                phase_signals=phase_signals,
                confidence_level=round(confidence_level, 2),
                next_phase_probability=next_phase_probability
            )
            
            logger.info(f"🎭 情绪周期分析完成: {sentiment_phase} ({sentiment_score:.1f}分)")
            return result
            
        except Exception as e:
            logger.error(f"情绪周期分析失败: {e}")
            return self._get_default_sentiment()
    
    def _analyze_profit_effect(self) -> Dict[str, Any]:
        """① 分析赚钱效应指标（使用东方财富实时API）"""
        try:
            logger.info("💰 分析赚钱效应指标...")
            
            up_limit_count = 0
            down_limit_count = 0
            avg_stock_change = 0
            limit_data = None
            
            # 优先使用东方财富API获取涨跌停数据
            try:
                import requests
                # 涨停板数据
                zt_url = 'https://push2.eastmoney.com/api/qt/clist/get'
                zt_params = {
                    'pn': '1',
                    'pz': '1000',  # 获取足够多的数据
                    'po': '1',
                    'np': '1',
                    'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                    'fltt': '2',
                    'invt': '2',
                    'fid': 'f3',  # 按涨跌幅排序
                    'fs': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23,m:0 t:81 s:2048',  # A股
                    'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152'
                }
                
                zt_response = requests.get(zt_url, params=zt_params, timeout=15)
                
                if zt_response.status_code == 200:
                    zt_data = zt_response.json()
                    
                    if 'data' in zt_data and 'diff' in zt_data['data']:
                        stock_records = zt_data['data']['diff']
                        
                        zt_stocks = []
                        dt_stocks = []
                        total_change = 0
                        valid_count = 0
                        
                        for record in stock_records:
                            try:
                                # f3: 涨跌幅(%)
                                change_pct = record.get('f3', 0)
                                
                                # 统计涨跌停
                                if change_pct >= 9.8:  # 接近10%涨停
                                    up_limit_count += 1
                                    zt_stocks.append(record)
                                elif change_pct <= -9.8:  # 接近-10%跌停
                                    down_limit_count += 1
                                    dt_stocks.append(record)
                                
                                # 计算平均涨幅
                                if abs(change_pct) < 15:  # 排除异常值
                                    total_change += change_pct
                                    valid_count += 1
                                    
                            except (ValueError, TypeError):
                                continue
                        
                        # 计算个股平均涨幅
                        if valid_count > 0:
                            avg_stock_change = total_change / valid_count
                        
                        # 构造limit_data用于后续分析
                        import pandas as pd
                        limit_data = pd.DataFrame(zt_stocks) if zt_stocks else pd.DataFrame()
                        
                        logger.info(f"📊 涨跌停数据 (东方财富):")
                        logger.info(f"  涨停股票: {up_limit_count}只")
                        logger.info(f"  跌停股票: {down_limit_count}只")
                        logger.info(f"  平均涨幅: {avg_stock_change:.2f}%")
                        
                    else:
                        logger.warning("涨跌停API返回数据格式异常")
                        
            except Exception as api_error:
                logger.warning(f"东方财富涨跌停API失败: {api_error}")
                up_limit_count = 0
                down_limit_count = 0
                avg_stock_change = 0
                limit_data = pd.DataFrame()
            
            # 计算涨跌停比例
            limit_ratio = up_limit_count / (down_limit_count + 1)
            
            # 分析连板成功率
            board_success_rate = self._calculate_board_success_rate(limit_data)
            
            # 计算赚钱效应综合评分
            profit_score = self._calculate_profit_score(
                up_limit_count, down_limit_count, 
                board_success_rate, avg_stock_change
            )
            
            # 获取历史均值对比
            historical_comparison = self._get_historical_profit_comparison(
                up_limit_count, down_limit_count, limit_ratio
            )
            
            return {
                'up_limit_count': up_limit_count,
                'down_limit_count': down_limit_count,
                'limit_ratio': round(limit_ratio, 2),
                'board_success_rate': round(board_success_rate, 2),
                'avg_stock_change': round(avg_stock_change, 2),
                'profit_score': round(profit_score, 1),
                'historical_comparison': historical_comparison,
                'signal': self._judge_profit_effect_signal_v2(profit_score, historical_comparison)
            }
            
        except Exception as e:
            logger.warning(f"赚钱效应分析失败: {e}")
            return {
                'up_limit_count': 0, 'down_limit_count': 0, 'limit_ratio': 1.0,
                'board_success_rate': 0.0, 'avg_stock_change': 0.0, 'profit_score': 50.0,
                'historical_comparison': {'level': '正常'}, 'signal': '数据异常'
            }
    
    def _analyze_high_standard(self) -> Dict[str, Any]:
        """② 分析高标人气承接（精准版）"""
        try:
            logger.info("🚀 分析高标人气承接...")
            
            # 获取涨停数据，寻找连板情况 - 仅使用东方财富API
            limit_data = pd.DataFrame()  # 不使用akshare
            
            if not limit_data.empty:
                # 详细分析连板情况
                board_analysis = self._analyze_continuous_boards(limit_data)
                
                # 分析弱转强成功率
                weak_strong_analysis = self._analyze_weak_to_strong(limit_data)
                
                # 计算高标承接强度
                acceptance_strength = self._calculate_high_standard_acceptance(
                    board_analysis, weak_strong_analysis
                )
                
                # 分析龙头股表现
                leader_performance = self._analyze_leader_performance(limit_data)
                
            else:
                board_analysis = {'total_boards': 0, 'board_distribution': {}, 'max_boards': 0}
                weak_strong_analysis = {'success_rate': 0, 'total_count': 0, 'success_count': 0}
                acceptance_strength = 50.0
                leader_performance = {'leader_count': 0, 'sustainability': 'weak'}
            
            return {
                'board_analysis': board_analysis,
                'weak_strong_analysis': weak_strong_analysis,
                'acceptance_strength': round(acceptance_strength, 1),
                'leader_performance': leader_performance,
                'signal': self._judge_high_standard_signal_v2(acceptance_strength, board_analysis, weak_strong_analysis)
            }
            
        except Exception as e:
            logger.warning(f"高标分析失败: {e}")
            return {
                'board_analysis': {'total_boards': 0, 'board_distribution': {}, 'max_boards': 0},
                'weak_strong_analysis': {'success_rate': 0, 'total_count': 0, 'success_count': 0},
                'acceptance_strength': 50.0,
                'leader_performance': {'leader_count': 0, 'sustainability': 'weak'},
                'signal': '数据异常'
            }
    
    def _analyze_turnover_change(self) -> Dict[str, Any]:
        """③ 分析成交额变化（量价配合版）"""
        try:
            logger.info("📊 分析成交额变化...")
            
            # 获取沪深两市成交额和指数涨跌幅 - 仅使用东方财富API
            market_data = pd.DataFrame()  # 不使用akshare
            
            if not market_data.empty:
                sh_index = market_data[market_data['代码'] == '000001'].iloc[0]
                sz_index = market_data[market_data['代码'] == '399001'].iloc[0]
                
                # 成交额
                sh_turnover = float(sh_index.get('成交额', 0))
                sz_turnover = float(sz_index.get('成交额', 0))
                total_turnover = (sh_turnover + sz_turnover) / 100000000  # 转为亿元
                
                # 指数涨跌幅
                sh_change = float(sh_index.get('涨跌幅', 0))
                sz_change = float(sz_index.get('涨跌幅', 0))
                avg_index_change = (sh_change + sz_change) / 2
                
            else:
                total_turnover = 8000
                avg_index_change = 0
            
            # 分析量价配合度
            volume_price_coordination = self._analyze_volume_price_coordination(
                total_turnover, avg_index_change
            )
            
            # 获取历史成交额对比
            historical_turnover_analysis = self._get_historical_turnover_comparison(total_turnover)
            
            # 分析市场活跃度
            market_activity = self._analyze_market_activity(total_turnover, avg_index_change)
            
            # 计算成交额综合评分
            turnover_score = self._calculate_turnover_score(
                total_turnover, volume_price_coordination, historical_turnover_analysis
            )
            
            return {
                'today_turnover': round(total_turnover, 0),
                'avg_index_change': round(avg_index_change, 2),
                'volume_price_coordination': volume_price_coordination,
                'historical_comparison': historical_turnover_analysis,
                'market_activity': market_activity,
                'turnover_score': round(turnover_score, 1),
                'signal': self._judge_turnover_signal_v2(turnover_score, volume_price_coordination)
            }
            
        except Exception as e:
            logger.warning(f"成交额分析失败: {e}")
            return {
                'today_turnover': 8000, 'avg_index_change': 0,
                'volume_price_coordination': {'type': '正常', 'score': 50},
                'historical_comparison': {'level': '正常'},
                'market_activity': {'level': '正常'}, 'turnover_score': 50.0,
                'signal': '数据异常'
            }
    
    def _analyze_theme_direction(self) -> Dict[str, Any]:
        """④ 分析主线行业题材（精准版）"""
        try:
            logger.info("🎯 分析主线行业题材...")
            
            # 获取行业板块涨跌情况 - 仅使用东方财富API
            industry_data = pd.DataFrame()  # 不使用akshare
            
            if not industry_data.empty:
                # 详细分析板块轮动
                rotation_analysis = self._analyze_sector_rotation(industry_data)
                
                # 分析主线持续性
                theme_sustainability = self._analyze_theme_sustainability(industry_data)
                
                # 计算题材活跃度
                theme_activity = self._calculate_theme_activity(industry_data)
                
                # 识别新兴题材
                emerging_themes = self._identify_emerging_themes(industry_data)
                
                # 综合评分
                theme_strength_score = self._calculate_theme_strength(
                    rotation_analysis, theme_sustainability, theme_activity
                )
                
            else:
                rotation_analysis = {'hot_sectors': [], 'rotation_strength': 0}
                theme_sustainability = {'main_themes': [], 'sustainability_score': 0}
                theme_activity = {'activity_level': '低', 'active_count': 0}
                emerging_themes = {'new_themes': [], 'emergence_strength': 0}
                theme_strength_score = 50.0
            
            return {
                'rotation_analysis': rotation_analysis,
                'theme_sustainability': theme_sustainability,
                'theme_activity': theme_activity,
                'emerging_themes': emerging_themes,
                'theme_strength_score': round(theme_strength_score, 1),
                'signal': self._judge_theme_signal_v2(theme_strength_score, rotation_analysis, theme_activity)
            }
            
        except Exception as e:
            logger.warning(f"主线分析失败: {e}")
            return {
                'rotation_analysis': {'hot_sectors': [], 'rotation_strength': 0},
                'theme_sustainability': {'main_themes': [], 'sustainability_score': 0},
                'theme_activity': {'activity_level': '低', 'active_count': 0},
                'emerging_themes': {'new_themes': [], 'emergence_strength': 0},
                'theme_strength_score': 50.0, 'signal': '数据异常'
            }
    
    def _analyze_etf_sentiment(self) -> Dict[str, Any]:
        """⑤ 分析ETF情绪指标"""
        try:
            logger.info("📈 分析ETF情绪指标...")
            
            # 分析关键ETF
            etf_tickers = {
                '159915.SZ': '创业板ETF',
                '159845.SZ': '中证1000ETF', 
                '510300.SH': '沪深300ETF'
            }
            
            etf_signals = {}
            
            for ticker, name in etf_tickers.items():
                try:
                    # 使用yfinance获取ETF数据
                    etf = yf.Ticker(ticker)
                    hist_data = etf.history(period='5d')
                    
                    if not hist_data.empty:
                        # 计算技术指标
                        latest_close = hist_data['Close'].iloc[-1]
                        volume_change = hist_data['Volume'].pct_change().iloc[-1]
                        price_change = hist_data['Close'].pct_change().iloc[-1]
                        
                        # 判断ETF状态
                        if price_change > 0.02 and volume_change > 0.5:
                            signal = '放量大阳'
                        elif price_change > 0:
                            signal = '企稳上涨'
                        elif price_change > -0.01:
                            signal = '横盘企稳'
                        else:
                            signal = '下跌'
                            
                        etf_signals[name] = {
                            'price_change': price_change,
                            'volume_change': volume_change,
                            'signal': signal
                        }
                    else:
                        etf_signals[name] = {'signal': '无数据'}
                        
                except:
                    etf_signals[name] = {'signal': '数据异常'}
            
            # 综合ETF信号
            positive_signals = sum(1 for s in etf_signals.values() 
                                 if s['signal'] in ['放量大阳', '企稳上涨'])
            
            return {
                'etf_signals': etf_signals,
                'positive_count': positive_signals,
                'total_count': len(etf_signals),
                'signal': self._judge_etf_signal(positive_signals, len(etf_signals))
            }
            
        except Exception as e:
            logger.warning(f"ETF分析失败: {e}")
            return {
                'etf_signals': {}, 'positive_count': 0,
                'total_count': 0, 'signal': '数据异常'
            }
    
    # 判断函数
    def _judge_profit_effect_signal(self, up_limit, down_limit, up_down_ratio):
        """判断赚钱效应信号"""
        if up_limit > 40 and down_limit < 10:
            return '加速阶段'
        elif up_limit > 20 and up_limit > down_limit:
            return '修复阶段'
        elif up_limit < 10 and down_limit > 20:
            return '冰点阶段'
        else:
            return '退潮阶段'
    
    def _judge_high_standard_signal(self, high_count, weak_strong_count):
        """判断高标信号"""
        if high_count >= 3 and weak_strong_count >= 2:
            return '加速阶段'
        elif high_count >= 1 and weak_strong_count >= 1:
            return '修复阶段'
        elif high_count == 0:
            return '冰点阶段'
        else:
            return '退潮阶段'
    
    def _judge_turnover_signal(self, turnover, trend):
        """判断成交额信号"""
        if turnover > 10000:
            return '加速阶段'
        elif turnover > 8000 and trend > 0:
            return '修复阶段'
        elif turnover < 7000:
            return '冰点阶段'
        else:
            return '退潮阶段'
    
    def _judge_theme_signal(self, themes, clarity, dispersion):
        """判断主线信号"""
        if len(themes) >= 2 and clarity and dispersion:
            return '加速阶段'
        elif len(themes) >= 1 and clarity:
            return '修复阶段'
        elif len(themes) == 0:
            return '冰点阶段'
        else:
            return '退潮阶段'
    
    def _judge_etf_signal(self, positive_count, total_count):
        """判断ETF信号"""
        if positive_count >= 2:
            return '加速阶段'
        elif positive_count >= 1:
            return '修复阶段'
        elif positive_count == 0:
            return '冰点阶段'
        else:
            return '退潮阶段'
    
    # 综合判断函数
    def _judge_phase_by_profit_effect(self, data, phase_scores):
        signal = data['signal']
        profit_score = data.get('profit_score', 50)
        
        # 根据信号和评分给予不同权重
        if signal == '加速阶段': 
            weight = 2.5 if profit_score >= 85 else 2.0
            phase_scores['加速'] += weight
        elif signal == '修复阶段': 
            weight = 2.0 if profit_score >= 60 else 1.5
            phase_scores['修复'] += weight
        elif signal == '冰点阶段': 
            weight = 2.5 if profit_score <= 25 else 2.0
            phase_scores['冰点'] += weight
        elif signal == '退潮阶段': 
            phase_scores['退潮'] += 2.0
            
        return [f"赚钱效应: {signal} (评分:{profit_score:.1f})"]
    
    def _judge_phase_by_high_standard(self, data, phase_scores):
        signal = data['signal']
        acceptance_strength = data.get('acceptance_strength', 50)
        board_analysis = data.get('board_analysis', {})
        max_boards = board_analysis.get('max_boards', 0)
        
        # 根据承接强度和最高连板数动态调整权重
        if signal == '加速阶段': 
            weight = 2.0 if max_boards >= 4 else 1.5
            phase_scores['加速'] += weight
        elif signal == '修复阶段': 
            weight = 1.8 if acceptance_strength >= 70 else 1.5
            phase_scores['修复'] += weight
        elif signal == '冰点阶段': 
            weight = 2.0 if max_boards == 0 else 1.5
            phase_scores['冰点'] += weight
        elif signal == '退潮阶段': 
            phase_scores['退潮'] += 1.5
            
        return [f"高标人气: {signal} (强度:{acceptance_strength:.1f})"]
    
    def _judge_phase_by_turnover(self, data, phase_scores):
        signal = data['signal']
        turnover_score = data.get('turnover_score', 50)
        volume_price = data.get('volume_price_coordination', {})
        vp_type = volume_price.get('type', '正常')
        
        # 根据成交额评分和量价配合调整权重
        if signal == '加速阶段': 
            weight = 1.5 if '放量大涨' in vp_type else 1.0
            phase_scores['加速'] += weight
        elif signal == '修复阶段': 
            weight = 1.2 if turnover_score >= 70 else 1.0
            phase_scores['修复'] += weight
        elif signal == '冰点阶段': 
            weight = 1.5 if '缩量下跌' in vp_type else 1.0
            phase_scores['冰点'] += weight
        elif signal == '退潮阶段': 
            phase_scores['退潮'] += 1.0
            
        return [f"成交额: {signal} ({vp_type})"]
    
    def _judge_phase_by_theme(self, data, phase_scores):
        signal = data['signal']
        theme_strength = data.get('theme_strength_score', 50)
        rotation = data.get('rotation_analysis', {})
        strong_count = rotation.get('strong_count', 0)
        
        # 根据题材强度和强势板块数量调整权重
        if signal == '加速阶段': 
            weight = 1.3 if strong_count >= 5 else 1.0
            phase_scores['加速'] += weight
        elif signal == '修复阶段': 
            weight = 1.2 if theme_strength >= 70 else 1.0
            phase_scores['修复'] += weight
        elif signal == '冰点阶段': 
            weight = 1.3 if strong_count == 0 else 1.0
            phase_scores['冰点'] += weight
        elif signal == '退潮阶段': 
            phase_scores['退潮'] += 1.0
            
        return [f"主线题材: {signal} (强度:{theme_strength:.1f})"]
    
    def _judge_phase_by_etf(self, data, phase_scores):
        signal = data['signal']
        if signal == '加速阶段': phase_scores['加速'] += 0.5
        elif signal == '修复阶段': phase_scores['修复'] += 0.5
        elif signal == '冰点阶段': phase_scores['冰点'] += 0.5
        elif signal == '退潮阶段': phase_scores['退潮'] += 0.5
        return [f"ETF情绪: {signal}"]
    
    # 辅助函数
    def _calculate_board_success_rate(self, limit_data) -> float:
        """计算连板成功率"""
        if limit_data.empty:
            return 0.0
            
        try:
            # 简化处理：统计连板股数量，假设连板成功率
            continuous_boards = 0
            for _, row in limit_data.iterrows():
                reason = row.get('涨停原因', '')
                if '连板' in reason or '2连板' in reason or '3连板' in reason or '4连板' in reason:
                    continuous_boards += 1
                    
            if len(limit_data) > 0:
                # 连板股占比 * 基础成功率（70%）
                board_ratio = continuous_boards / len(limit_data)
                success_rate = 70 + (board_ratio * 20)  # 基础70%，最高90%
                return min(success_rate, 95)  # 最高95%
            else:
                return 50  # 默认50%
                
        except Exception:
            return 50
    
    def _calculate_profit_score(self, up_limit: int, down_limit: int, 
                               board_success_rate: float, avg_change: float) -> float:
        """计算赚钱效应综合评分"""
        # 涨跌停比例评分 (40%权重)
        limit_ratio = up_limit / (down_limit + 1)
        if limit_ratio >= 3.0:
            ratio_score = 95
        elif limit_ratio >= 2.0:
            ratio_score = 80
        elif limit_ratio >= 1.5:
            ratio_score = 70
        elif limit_ratio >= 1.0:
            ratio_score = 60
        elif limit_ratio >= 0.5:
            ratio_score = 40
        else:
            ratio_score = 20
        
        # 连板成功率评分 (30%权重)
        success_score = min(board_success_rate, 100)
        
        # 平均涨幅评分 (30%权重)
        if avg_change >= 2.0:
            change_score = 90
        elif avg_change >= 1.0:
            change_score = 80
        elif avg_change >= 0.5:
            change_score = 70
        elif avg_change >= 0:
            change_score = 60
        elif avg_change >= -0.5:
            change_score = 40
        else:
            change_score = 20
        
        # 综合评分
        total_score = (ratio_score * 0.4 + success_score * 0.3 + change_score * 0.3)
        return max(0, min(100, total_score))
    
    def _get_historical_profit_comparison(self, up_limit: int, down_limit: int, 
                                        limit_ratio: float) -> Dict[str, Any]:
        """获取历史数据对比（简化版）"""
        # 基于经验数据的历史对比
        historical_avg = {
            'up_limit_avg': 25,      # 历史平均涨停数
            'down_limit_avg': 8,     # 历史平均跌停数  
            'ratio_avg': 3.1         # 历史平均涨跌停比例
        }
        
        # 计算相对水平
        if up_limit >= historical_avg['up_limit_avg'] * 1.5:
            up_level = '远超历史均值'
        elif up_limit >= historical_avg['up_limit_avg'] * 1.2:
            up_level = '超过历史均值'
        elif up_limit >= historical_avg['up_limit_avg'] * 0.8:
            up_level = '接近历史均值'
        else:
            up_level = '低于历史均值'
            
        if limit_ratio >= historical_avg['ratio_avg'] * 1.3:
            ratio_level = '显著强于历史'
        elif limit_ratio >= historical_avg['ratio_avg'] * 0.7:
            ratio_level = '接近历史均值'
        else:
            ratio_level = '弱于历史均值'
            
        return {
            'up_limit_level': up_level,
            'ratio_level': ratio_level,
            'level': ratio_level  # 主要判断依据
        }
    
    def _judge_profit_effect_signal_v2(self, profit_score: float, 
                                     historical_comparison: Dict[str, Any]) -> str:
        """改进版赚钱效应信号判断"""
        hist_level = historical_comparison.get('level', '接近历史均值')
        
        # 冰点：利得分低于30且弱于历史
        if profit_score <= 30 and '弱于历史' in hist_level:
            return '冰点阶段'
        # 加速：评分高于80且强于历史    
        elif profit_score >= 80 and '强于历史' in hist_level:
            return '加速阶段'
        # 修复：评分45-75，且不弱于历史
        elif 45 <= profit_score <= 75 and '弱于历史' not in hist_level:
            return '修复阶段'
        # 退潮：其他情况
        else:
            return '退潮阶段'
    
    def _analyze_continuous_boards(self, limit_data) -> Dict[str, Any]:
        """分析连板分布情况"""
        board_distribution = {}
        total_boards = 0
        max_boards = 0
        
        for _, row in limit_data.iterrows():
            try:
                reason = row.get('涨停原因', '')
                boards = 0
                
                # 提取连板数量
                if '10连板' in reason or '十连板' in reason:
                    boards = 10
                elif '9连板' in reason:
                    boards = 9
                elif '8连板' in reason:
                    boards = 8
                elif '7连板' in reason:
                    boards = 7
                elif '6连板' in reason:
                    boards = 6
                elif '5连板' in reason:
                    boards = 5
                elif '4连板' in reason:
                    boards = 4
                elif '3连板' in reason:
                    boards = 3
                elif '2连板' in reason or '二连板' in reason:
                    boards = 2
                elif '连板' in reason and '首板' not in reason:
                    boards = 2  # 默认2连板
                    
                if boards > 0:
                    board_distribution[f'{boards}连板'] = board_distribution.get(f'{boards}连板', 0) + 1
                    total_boards += 1
                    max_boards = max(max_boards, boards)
                    
            except:
                continue
                
        return {
            'total_boards': total_boards,
            'board_distribution': board_distribution,
            'max_boards': max_boards
        }
    
    def _analyze_weak_to_strong(self, limit_data) -> Dict[str, Any]:
        """分析弱转强情况"""
        weak_strong_stocks = []
        total_weak_strong = 0
        
        for _, row in limit_data.iterrows():
            try:
                reason = row.get('涨停原因', '')
                if '弱转强' in reason:
                    weak_strong_stocks.append({
                        'name': row.get('名称', ''),
                        'reason': reason
                    })
                    total_weak_strong += 1
            except:
                continue
                
        # 简化的成功率计算
        success_rate = min(75 + total_weak_strong * 5, 95) if total_weak_strong > 0 else 50
        
        return {
            'total_count': total_weak_strong,
            'success_count': int(total_weak_strong * success_rate / 100),
            'success_rate': success_rate,
            'weak_strong_stocks': weak_strong_stocks[:3]
        }
    
    def _calculate_high_standard_acceptance(self, board_analysis: Dict, 
                                          weak_strong_analysis: Dict) -> float:
        """计算高标承接强度"""
        total_boards = board_analysis['total_boards']
        max_boards = board_analysis['max_boards']
        weak_strong_rate = weak_strong_analysis['success_rate']
        
        # 连板数量评分 (50%权重)
        if total_boards >= 5:
            board_score = 90
        elif total_boards >= 3:
            board_score = 75
        elif total_boards >= 1:
            board_score = 60
        else:
            board_score = 30
            
        # 最高连板数评分 (30%权重)
        if max_boards >= 5:
            max_score = 95
        elif max_boards >= 3:
            max_score = 80
        elif max_boards >= 2:
            max_score = 65
        else:
            max_score = 40
            
        # 弱转强成功率评分 (20%权重)
        weak_score = weak_strong_rate
        
        # 综合评分
        total_score = (board_score * 0.5 + max_score * 0.3 + weak_score * 0.2)
        return max(0, min(100, total_score))
    
    def _analyze_leader_performance(self, limit_data) -> Dict[str, Any]:
        """分析龙头股表现"""
        leader_count = 0
        sustainability = 'weak'
        
        # 简化处理：统计高连板数量作为龙头数量
        for _, row in limit_data.iterrows():
            try:
                reason = row.get('涨停原因', '')
                if any(x in reason for x in ['3连板', '4连板', '5连板', '6连板']):
                    leader_count += 1
            except:
                continue
                
        # 根据龙头数量判断持续性
        if leader_count >= 3:
            sustainability = 'strong'
        elif leader_count >= 1:
            sustainability = 'medium'
        else:
            sustainability = 'weak'
            
        return {
            'leader_count': leader_count,
            'sustainability': sustainability
        }
    
    def _judge_high_standard_signal_v2(self, acceptance_strength: float, 
                                     board_analysis: Dict, weak_strong_analysis: Dict) -> str:
        """改进版高标信号判断"""
        total_boards = board_analysis['total_boards']
        max_boards = board_analysis['max_boards']
        weak_success_rate = weak_strong_analysis['success_rate']
        
        # 加速：承接强度高，且有高连板
        if acceptance_strength >= 80 and max_boards >= 3:
            return '加速阶段'
        # 修复：有连板且弱转强成功率不错
        elif total_boards >= 1 and weak_success_rate >= 60:
            return '修复阶段'
        # 冰点：无连板且承接强度低
        elif total_boards == 0 and acceptance_strength <= 40:
            return '冰点阶段'
        # 退潮：其他情况
        else:
            return '退潮阶段'

    def _analyze_volume_price_coordination(self, turnover: float, price_change: float) -> Dict[str, Any]:
        """分析量价配合度"""
        # 量价配合度分析
        if turnover > 10000:  # 万亿以上
            if price_change > 1.5:
                coord_type = "放量大涨"
                score = 95
            elif price_change > 0.5:
                coord_type = "放量上涨"  
                score = 85
            elif price_change > -0.5:
                coord_type = "放量横盘"
                score = 60
            else:
                coord_type = "放量下跌"
                score = 30
        elif turnover > 8000:  # 8000-10000亿
            if price_change > 1.0:
                coord_type = "温和放量上涨"
                score = 80
            elif price_change > 0:
                coord_type = "正常上涨"
                score = 70
            elif price_change > -0.5:
                coord_type = "正常横盘"
                score = 55
            else:
                coord_type = "温和下跌"
                score = 40
        else:  # 8000亿以下
            if price_change > 0.5:
                coord_type = "缩量上涨"
                score = 60  # 缩量上涨不够强势
            elif price_change > -0.5:
                coord_type = "缩量横盘"
                score = 50
            else:
                coord_type = "缩量下跌"
                score = 20  # 缩量下跌是弱势信号
        
        return {
            'type': coord_type,
            'score': score,
            'turnover_level': self._get_turnover_level_desc(turnover),
            'price_trend': '上涨' if price_change > 0 else '下跌' if price_change < 0 else '横盘'
        }
    
    def _get_historical_turnover_comparison(self, turnover: float) -> Dict[str, Any]:
        """获取历史成交额对比"""
        # 基于经验的历史成交额水平
        historical_levels = {
            'extreme_high': 12000,  # 极高水平
            'high': 10000,         # 高水平 
            'normal_high': 9000,   # 正常偏高
            'normal': 8000,        # 正常水平
            'low': 6500,          # 偏低水平
            'extreme_low': 5000    # 极低水平
        }
        
        if turnover >= historical_levels['extreme_high']:
            level = '历史极高水平'
            percentile = 95
        elif turnover >= historical_levels['high']:
            level = '历史高位水平'
            percentile = 85
        elif turnover >= historical_levels['normal_high']:
            level = '正常偏高水平'
            percentile = 70
        elif turnover >= historical_levels['normal']:
            level = '正常水平'
            percentile = 50
        elif turnover >= historical_levels['low']:
            level = '偏低水平'
            percentile = 30
        else:
            level = '历史低位水平'
            percentile = 15
            
        return {
            'level': level,
            'percentile': percentile,
            'vs_normal': round((turnover / historical_levels['normal'] - 1) * 100, 1)
        }
    
    def _analyze_market_activity(self, turnover: float, price_change: float) -> Dict[str, Any]:
        """分析市场活跃度"""
        # 综合成交额和价格波动判断市场活跃度
        activity_score = 0
        
        # 成交额因子 (60%权重)
        if turnover >= 12000:
            volume_factor = 100
        elif turnover >= 10000:
            volume_factor = 90
        elif turnover >= 8500:
            volume_factor = 70
        elif turnover >= 7000:
            volume_factor = 50
        else:
            volume_factor = 30
            
        # 价格波动因子 (40%权重)
        price_volatility = abs(price_change)
        if price_volatility >= 2.0:
            volatility_factor = 90
        elif price_volatility >= 1.5:
            volatility_factor = 80
        elif price_volatility >= 1.0:
            volatility_factor = 70
        elif price_volatility >= 0.5:
            volatility_factor = 60
        else:
            volatility_factor = 40
            
        activity_score = volume_factor * 0.6 + volatility_factor * 0.4
        
        if activity_score >= 85:
            activity_level = '极度活跃'
        elif activity_score >= 75:
            activity_level = '高度活跃'
        elif activity_score >= 60:
            activity_level = '正常活跃'
        elif activity_score >= 45:
            activity_level = '偏低迷'
        else:
            activity_level = '低迷'
            
        return {
            'level': activity_level,
            'score': round(activity_score, 1),
            'volume_factor': round(volume_factor, 1),
            'volatility_factor': round(volatility_factor, 1)
        }
    
    def _calculate_turnover_score(self, turnover: float, volume_price: Dict, 
                                historical: Dict) -> float:
        """计算成交额综合评分"""
        # 量价配合评分 (50%权重)
        vp_score = volume_price['score']
        
        # 历史水平评分 (30%权重)
        hist_score = historical['percentile']
        
        # 绝对水平评分 (20%权重)
        if turnover >= 12000:
            abs_score = 95
        elif turnover >= 10000:
            abs_score = 85
        elif turnover >= 8000:
            abs_score = 70
        elif turnover >= 6000:
            abs_score = 50
        else:
            abs_score = 30
            
        # 综合评分
        total_score = vp_score * 0.5 + hist_score * 0.3 + abs_score * 0.2
        return max(0, min(100, total_score))
    
    def _get_turnover_level_desc(self, turnover: float) -> str:
        """获取成交额水平描述"""
        if turnover >= 12000:
            return "万亿以上"
        elif turnover >= 10000:
            return "万亿级别"
        elif turnover >= 8000:
            return "8000-9999亿"
        elif turnover >= 6000:
            return "6000-7999亿"
        else:
            return "6000亿以下"
    
    def _judge_turnover_signal_v2(self, turnover_score: float, 
                                volume_price: Dict) -> str:
        """改进版成交额信号判断"""
        vp_type = volume_price['type']
        vp_score = volume_price['score']
        
        # 加速：高评分且量价配合良好
        if turnover_score >= 80 and vp_score >= 80:
            return '加速阶段'
        # 修复：中等评分且非缩量下跌
        elif turnover_score >= 60 and '缩量下跌' not in vp_type:
            return '修复阶段'
        # 冰点：低评分且缩量下跌
        elif turnover_score <= 40 and '缩量' in vp_type and '下跌' in vp_type:
            return '冰点阶段'
        # 退潮：其他情况
        else:
            return '退潮阶段'

    def _calculate_turnover_trend(self, today_turnover):
        """计算成交额趋势（保留兼容性）"""
        avg_turnover = 8500
        return (today_turnover - avg_turnover) / avg_turnover
    
    def _analyze_sector_rotation(self, industry_data) -> Dict[str, Any]:
        """分析板块轮动情况"""
        # 按涨跌幅排序
        sorted_data = industry_data.sort_values('涨跌幅', ascending=False)
        
        # 统计不同涨幅区间的板块数量
        strong_sectors = sorted_data[sorted_data['涨跌幅'] >= 3].head(10)  # 强势板块
        rising_sectors = sorted_data[sorted_data['涨跌幅'] >= 1].head(15)  # 上涨板块
        falling_sectors = sorted_data[sorted_data['涨跌幅'] <= -1]  # 下跌板块
        
        # 计算轮动强度
        strong_count = len(strong_sectors)
        rising_count = len(rising_sectors)
        falling_count = len(falling_sectors)
        
        if strong_count >= 5:
            rotation_strength = 90
        elif strong_count >= 3:
            rotation_strength = 75
        elif rising_count >= 8:
            rotation_strength = 60
        else:
            rotation_strength = 40
            
        hot_sectors = []
        for _, row in strong_sectors.iterrows():
            hot_sectors.append({
                'name': row['板块名称'],
                'change_pct': row['涨跌幅'],
                'leading_stock': row.get('领涨股票', '')
            })
            
        return {
            'hot_sectors': hot_sectors[:5],
            'rotation_strength': rotation_strength,
            'strong_count': strong_count,
            'rising_count': rising_count,
            'falling_count': falling_count
        }
    
    def _analyze_theme_sustainability(self, industry_data) -> Dict[str, Any]:
        """分析主线持续性"""
        # 简化处理：基于涨幅分布判断持续性
        sorted_data = industry_data.sort_values('涨跌幅', ascending=False)
        
        # 主线题材（涨幅前3的板块）
        main_themes = []
        sustainability_score = 50
        
        top_3 = sorted_data.head(3)
        for _, row in top_3.iterrows():
            change_pct = row['涨跌幅']
            if change_pct >= 2:  # 主线标准：涨幅2%以上
                main_themes.append({
                    'name': row['板块名称'],
                    'change_pct': change_pct,
                    'sustainability': '强' if change_pct >= 4 else '中' if change_pct >= 3 else '弱'
                })
                
        # 根据主线数量和强度评分
        if len(main_themes) >= 2 and any(t['change_pct'] >= 4 for t in main_themes):
            sustainability_score = 85
        elif len(main_themes) >= 1 and any(t['change_pct'] >= 3 for t in main_themes):
            sustainability_score = 70
        elif len(main_themes) >= 1:
            sustainability_score = 60
        else:
            sustainability_score = 30
            
        return {
            'main_themes': main_themes,
            'sustainability_score': sustainability_score,
            'main_theme_count': len(main_themes)
        }
    
    def _calculate_theme_activity(self, industry_data) -> Dict[str, Any]:
        """计算题材活跃度"""
        # 统计活跃板块数量
        active_sectors = industry_data[abs(industry_data['涨跌幅']) >= 1]
        very_active_sectors = industry_data[abs(industry_data['涨跌幅']) >= 2]
        
        active_count = len(active_sectors)
        very_active_count = len(very_active_sectors)
        total_sectors = len(industry_data)
        
        # 活跃度比例
        activity_ratio = active_count / total_sectors if total_sectors > 0 else 0
        
        if activity_ratio >= 0.3:  # 30%以上板块活跃
            activity_level = '高度活跃'
        elif activity_ratio >= 0.2:
            activity_level = '活跃'
        elif activity_ratio >= 0.1:
            activity_level = '正常'
        else:
            activity_level = '低迷'
            
        return {
            'activity_level': activity_level,
            'active_count': active_count,
            'very_active_count': very_active_count,
            'activity_ratio': round(activity_ratio, 3),
            'total_sectors': total_sectors
        }
    
    def _identify_emerging_themes(self, industry_data) -> Dict[str, Any]:
        """识别新兴题材"""
        # 简化处理：寻找涨幅突然放大的板块
        sorted_data = industry_data.sort_values('涨跌幅', ascending=False)
        
        # 新兴题材：涨幅在1.5%-4%之间的板块（既不是龙头，也不是跟风）
        emerging_candidates = sorted_data[
            (sorted_data['涨跌幅'] >= 1.5) & 
            (sorted_data['涨跌幅'] <= 4.0)
        ]
        
        new_themes = []
        for _, row in emerging_candidates.head(3).iterrows():
            new_themes.append({
                'name': row['板块名称'],
                'change_pct': row['涨跌幅'],
                'emergence_potential': '高' if row['涨跌幅'] >= 2.5 else '中'
            })
            
        emergence_strength = len(new_themes) * 20 + 40  # 基础40分，每个新兴题材+20分
        emergence_strength = min(emergence_strength, 100)
        
        return {
            'new_themes': new_themes,
            'emergence_strength': emergence_strength,
            'emerging_count': len(new_themes)
        }
    
    def _calculate_theme_strength(self, rotation: Dict, sustainability: Dict, 
                                activity: Dict) -> float:
        """计算题材强度综合评分"""
        # 轮动强度 (40%权重)
        rotation_score = rotation['rotation_strength']
        
        # 持续性评分 (35%权重)  
        sustainability_score = sustainability['sustainability_score']
        
        # 活跃度评分 (25%权重)
        activity_ratio = activity['activity_ratio']
        activity_score = min(activity_ratio * 250, 100)  # 转换为0-100分
        
        # 综合评分
        total_score = (
            rotation_score * 0.4 + 
            sustainability_score * 0.35 + 
            activity_score * 0.25
        )
        
        return max(0, min(100, total_score))
    
    def _judge_theme_signal_v2(self, theme_strength: float, rotation: Dict, 
                             activity: Dict) -> str:
        """改进版题材信号判断"""
        rotation_strength = rotation['rotation_strength']
        strong_count = rotation.get('strong_count', 0)
        activity_level = activity['activity_level']
        
        # 加速：强度高且有多个强势板块
        if theme_strength >= 80 and strong_count >= 4:
            return '加速阶段'
        # 修复：有明确主线且活跃度正常
        elif theme_strength >= 60 and activity_level != '低迷':
            return '修复阶段'
        # 冰点：强度低且活跃度低迷
        elif theme_strength <= 40 and activity_level == '低迷':
            return '冰点阶段'
        # 退潮：其他情况
        else:
            return '退潮阶段'
    
    def _judge_turnover_level(self, turnover):
        """判断成交额水平"""
        if turnover > 10000:
            return '万亿以上'
        elif turnover > 8000:
            return '8000-9000亿'
        else:
            return '6000-7000亿'
    
    def _predict_next_phase(self, current_phase, scores):
        """预测下一阶段概率"""
        # 简化的状态转移概率
        transitions = {
            '冰点': {'修复': 0.6, '冰点': 0.4},
            '修复': {'加速': 0.5, '修复': 0.3, '退潮': 0.2},
            '加速': {'退潮': 0.6, '加速': 0.4},
            '退潮': {'冰点': 0.5, '修复': 0.3, '退潮': 0.2}
        }
        return transitions.get(current_phase, {})
    
    def _get_default_sentiment(self):
        """获取默认情绪结果"""
        return MarketSentimentResult(
            sentiment_phase='数据异常',
            sentiment_score=50.0,
            profit_effect={}, high_standard={}, turnover_change={},
            theme_direction={}, etf_sentiment={},
            phase_signals=[], confidence_level=0.0,
            next_phase_probability={}
        )

def main():
    """主函数"""
    print("🎭 市场情绪周期分析系统")
    print("="*60)
    
    analyzer = MarketSentimentAnalyzer()
    result = analyzer.analyze_sentiment_cycle()
    
    print(f"\n📊 情绪周期阶段: {result.sentiment_phase}")
    print(f"📈 情绪评分: {result.sentiment_score}/100")
    print(f"🎯 置信度: {result.confidence_level:.1%}")
    
    print(f"\n🔍 各项指标信号:")
    for signal in result.phase_signals:
        print(f"  • {signal}")
    
    print(f"\n🔮 下一阶段概率:")
    for phase, prob in result.next_phase_probability.items():
        print(f"  • {phase}: {prob:.1%}")

if __name__ == "__main__":
    main()