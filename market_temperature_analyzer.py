#!/usr/bin/env python3
"""
市场温度计分析器
监控涨跌家数、成交额、两融、ETF资金流等关键市场温度指标
"""

import requests
import json
import logging
import time
import numpy as np
import akshare as ak
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enhanced_technical_analyzer import EnhancedTechnicalAnalyzer
from money_flow_analyzer import MoneyFlowAnalyzer
from market_sentiment_analyzer import MarketSentimentAnalyzer
from market_emotion_indicators import MarketEmotionAnalyzer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MarketTemperatureResult:
    """市场温度分析结果"""
    temperature_score: float  # 0-100分，越高越热
    temperature_level: str    # 冰点/偏冷/温和/偏热/火热
    up_down_ratio: float      # 涨跌比
    turnover_billion: float   # 成交额(亿)
    margin_balance: float     # 两融余额变化%
    etf_inflow: float        # ETF资金净流入(亿)
    heat_sources: List[str]   # 升温因素
    cool_sources: List[str]   # 降温因素
    # 新增沪深300技术指标
    hs300_price: float       # 沪深300最新收盘价
    hs300_change: float      # 沪深300涨跌幅%
    hs300_ma20: float        # 沪深300 20日均线
    hs300_ma30: float        # 沪深300 30日均线
    hs300_ma20_5d_ago: float # 沪深300 20日均线(5天前)
    hs300_ma30_5d_ago: float # 沪深300 30日均线(5天前)
    hs300_vs_ma20: float     # 相对20日均线位置%
    hs300_vs_ma30: float     # 相对30日均线位置%
    ma_signal: str           # 均线信号（多头/空头/震荡）
    # 增强技术分析结果
    enhanced_signal: str     # 增强版技术信号
    signal_strength: float   # 信号强度
    consecutive_days: int    # 连续突破天数
    volume_breakout: bool    # 是否放量突破
    ma_trend_up: bool        # 均线是否向上
    pullback_hold: bool      # 回踩是否不破
    # 资金流数据
    today_north_bound: float      # 今日北向资金净流入
    today_etf_inflow: float       # 今日ETF资金净流入  
    today_main_force: float       # 今日主力资金净流入
    north_bound_3d_total: float   # 3天北向资金累计
    etf_inflow_3d_total: float    # 3天ETF资金累计
    main_force_3d_total: float    # 3天主力资金累计
    north_bound_7d_total: float   # 1周北向资金累计
    etf_inflow_7d_total: float    # 1周ETF资金累计
    main_force_7d_total: float    # 1周主力资金累计
    north_bound_30d_total: float  # 4周北向资金累计
    etf_inflow_30d_total: float   # 4周ETF资金累计
    main_force_30d_total: float   # 4周主力资金累计
    north_bound_trend: str        # 北向资金趋势
    etf_trend: str               # ETF资金趋势
    main_force_trend: str        # 主力资金趋势
    money_flow_score: float      # 资金流评分
    money_flow_level: str        # 资金流等级
    # 情绪周期数据
    sentiment_phase: str         # 情绪周期阶段
    sentiment_score: float       # 情绪评分
    # 核心市场情绪指标
    n_up_limit: int             # 涨停家数
    n_cont_limit: int           # 连板家数（≥2连板）
    win_ratio: float            # 赚钱比例
    vol_ratio: float            # 成交额放大倍数
    n_down_limit: int           # 跌停家数
    emotion_score: float        # 综合情绪评分
    emotion_level: str          # 情绪等级
    market_stage: str           # 市场阶段
    sentiment_confidence: float  # 判断置信度
    profit_effect_signal: str    # 赚钱效应信号
    high_standard_signal: str    # 高标人气信号
    turnover_signal: str         # 成交额信号
    theme_signal: str           # 主线信号
    etf_sentiment_signal: str    # ETF情绪信号
    
class MarketTemperatureAnalyzer:
    """市场温度计分析器"""
    
    def __init__(self):
        self.market_index_url = "http://localhost:5008"
        
        # 温度等级阈值
        self.temperature_thresholds = {
            'freezing': 20,      # 冰点 0-20
            'cold': 40,         # 偏冷 20-40
            'mild': 60,         # 温和 40-60
            'warm': 80,         # 偏热 60-80
            'hot': 100          # 火热 80-100
        }
        
        # 市场标准参数（用于计算相对温度）
        self.market_standards = {
            'normal_turnover': 10000,      # 正常成交额10000亿
            'normal_up_ratio': 0.5,        # 正常涨跌比50%
            'normal_margin_growth': 0,     # 正常两融增长0%
            'normal_etf_flow': 0          # 正常ETF流入0亿
        }
        
        self.cache = {}
        self.cache_duration = 120  # 2分钟缓存
        
        # 初始化增强技术分析器
        self.enhanced_analyzer = EnhancedTechnicalAnalyzer()
        
        # 初始化资金流分析器
        self.money_flow_analyzer = MoneyFlowAnalyzer()
        
        # 初始化市场情绪指标分析器
        self.emotion_analyzer = MarketEmotionAnalyzer()
        
        # 初始化情绪周期分析器
        self.sentiment_analyzer = MarketSentimentAnalyzer()
        
    def analyze_market_temperature(self) -> MarketTemperatureResult:
        """分析市场温度"""
        try:
            logger.info("🌡️ 开始分析市场温度...")
            
            # 获取基础市场数据
            market_data = self._get_market_data()
            
            # 获取沪深300技术指标数据
            hs300_data = self._get_hs300_technical_data()
            
            # 获取增强版技术分析结果
            enhanced_signal = self.enhanced_analyzer.analyze_technical_signal()
            
            # 获取资金流分析结果
            money_flow_result = self.money_flow_analyzer.analyze_money_flow()
            
            # 获取情绪周期分析结果
            sentiment_result = self.sentiment_analyzer.analyze_sentiment_cycle()
            
            # 获取核心市场情绪指标
            emotion_indicators = self.emotion_analyzer.analyze_market_emotion()
            
            # 计算各项温度指标
            up_down_score = self._calculate_up_down_temperature(market_data)
            turnover_score = self._calculate_turnover_temperature(market_data)
            margin_score = self._calculate_margin_temperature(market_data)
            etf_score = self._calculate_etf_temperature(market_data)
            ma_score = self._calculate_ma_temperature(hs300_data)
            
            # 增强信号对温度的贡献（新增）
            enhanced_score = self._calculate_enhanced_signal_temperature(enhanced_signal)
            
            # 资金流对温度的贡献（新增）
            money_flow_score = money_flow_result.money_flow_score
            
            # 情绪周期对温度的贡献（新增）
            sentiment_temperature_score = sentiment_result.sentiment_score
            
            # 综合温度评分（新增资金流和情绪周期权重）
            weights = {
                'up_down': 0.15,     # 涨跌家数权重15%
                'turnover': 0.08,    # 成交额权重8%
                'margin': 0.07,      # 两融权重7%
                'etf': 0.10,         # ETF权重10%
                'ma': 0.12,          # 基础均线权重12%
                'enhanced': 0.13,    # 增强信号权重13%
                'money_flow': 0.20,  # 资金流权重20%
                'sentiment': 0.15    # 情绪周期权重15%
            }
            
            total_score = (
                up_down_score * weights['up_down'] +
                turnover_score * weights['turnover'] +
                margin_score * weights['margin'] +
                etf_score * weights['etf'] +
                ma_score * weights['ma'] +
                enhanced_score * weights['enhanced'] +
                money_flow_score * weights['money_flow'] +
                sentiment_temperature_score * weights['sentiment']
            )
            
            # 确定温度等级
            temperature_level = self._determine_temperature_level(total_score)
            
            # 识别升温和降温因素
            heat_sources, cool_sources = self._identify_temperature_sources(
                market_data, up_down_score, turnover_score, margin_score, etf_score, ma_score, enhanced_signal
            )
            
            # 提取关键指标
            overview = market_data.get('market_overview', {})
            up_stocks = overview.get('up_stocks', 0)
            down_stocks = overview.get('down_stocks', 0)
            total_stocks = overview.get('total_stocks', 1)
            up_down_ratio = up_stocks / max(total_stocks, 1)
            
            turnover_billion = overview.get('total_turnover', 0)
            
            # 模拟两融和ETF数据（实际应用中需要真实API）
            margin_balance = self._simulate_margin_data()
            etf_inflow = self._simulate_etf_data()
            
            result = MarketTemperatureResult(
                temperature_score=round(total_score, 1),
                temperature_level=temperature_level,
                up_down_ratio=round(up_down_ratio, 3),
                turnover_billion=turnover_billion,
                margin_balance=margin_balance,
                etf_inflow=etf_inflow,
                heat_sources=heat_sources,
                cool_sources=cool_sources,
                # 沪深300技术指标
                hs300_price=hs300_data.get('price', 0),
                hs300_change=hs300_data.get('change', 0),
                hs300_ma20=hs300_data.get('ma20', 0),
                hs300_ma30=hs300_data.get('ma30', 0),
                hs300_ma20_5d_ago=hs300_data.get('ma20_5d_ago', 0),
                hs300_ma30_5d_ago=hs300_data.get('ma30_5d_ago', 0),
                hs300_vs_ma20=hs300_data.get('vs_ma20', 0),
                hs300_vs_ma30=hs300_data.get('vs_ma30', 0),
                ma_signal=hs300_data.get('signal', '数据异常'),
                # 增强技术分析结果
                enhanced_signal=enhanced_signal.signal_type,
                signal_strength=round(enhanced_signal.signal_strength, 1),
                consecutive_days=enhanced_signal.consecutive_days,
                volume_breakout=enhanced_signal.volume_breakout,
                ma_trend_up=enhanced_signal.ma_trend_up,
                pullback_hold=enhanced_signal.pullback_hold,
                # 资金流数据
                today_north_bound=money_flow_result.today_north_bound,
                today_etf_inflow=money_flow_result.today_etf_inflow,
                today_main_force=money_flow_result.today_main_force,
                north_bound_3d_total=money_flow_result.north_bound_3d_total,
                etf_inflow_3d_total=money_flow_result.etf_inflow_3d_total,
                main_force_3d_total=money_flow_result.main_force_3d_total,
                north_bound_7d_total=money_flow_result.north_bound_7d_total,
                etf_inflow_7d_total=money_flow_result.etf_inflow_7d_total,
                main_force_7d_total=money_flow_result.main_force_7d_total,
                north_bound_30d_total=money_flow_result.north_bound_30d_total,
                etf_inflow_30d_total=money_flow_result.etf_inflow_30d_total,
                main_force_30d_total=money_flow_result.main_force_30d_total,
                north_bound_trend=money_flow_result.north_bound_trend,
                etf_trend=money_flow_result.etf_trend,
                main_force_trend=money_flow_result.main_force_trend,
                money_flow_score=money_flow_result.money_flow_score,
                money_flow_level=money_flow_result.money_flow_level,
                # 情绪周期数据
                sentiment_phase=sentiment_result.sentiment_phase,
                sentiment_score=sentiment_result.sentiment_score,
                sentiment_confidence=sentiment_result.confidence_level,
                profit_effect_signal=sentiment_result.profit_effect.get('signal', '数据异常'),
                high_standard_signal=sentiment_result.high_standard.get('signal', '数据异常'),
                turnover_signal=sentiment_result.turnover_change.get('signal', '数据异常'),
                theme_signal=sentiment_result.theme_direction.get('signal', '数据异常'),
                etf_sentiment_signal=sentiment_result.etf_sentiment.get('signal', '数据异常'),
                # 核心市场情绪指标
                n_up_limit=emotion_indicators.n_up_limit,
                n_cont_limit=emotion_indicators.n_cont_limit,
                win_ratio=emotion_indicators.win_ratio,
                vol_ratio=emotion_indicators.vol_ratio,
                n_down_limit=emotion_indicators.n_down_limit,
                emotion_score=emotion_indicators.emotion_score,
                emotion_level=emotion_indicators.emotion_level,
                market_stage=emotion_indicators.market_stage
            )
            
            logger.info(f"🌡️ 市场温度分析完成: {total_score:.1f}分 - {temperature_level}")
            return result
            
        except Exception as e:
            logger.error(f"市场温度分析失败: {e}")
            return self._get_default_temperature()
    
    def _get_market_data(self) -> Dict:
        """获取市场数据"""
        cache_key = "temperature_market_data"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            market_data = {}
            
            # 获取主要指数数据
            response = requests.get(f"{self.market_index_url}/api/main-indices", timeout=10)
            if response.status_code == 200:
                indices_data = response.json()
                market_data.update(indices_data)
            
            # 获取行业数据
            response = requests.get(f"{self.market_index_url}/api/sector-indices", timeout=10)
            if response.status_code == 200:
                sector_data = response.json()
                market_data['sector_data'] = sector_data
            
            # 缓存数据
            self.cache[cache_key] = market_data
            self._set_cache_time(cache_key)
            
            return market_data
            
        except Exception as e:
            logger.error(f"获取市场数据失败: {e}")
            return {}
    
    def _get_hs300_technical_data(self) -> Dict:
        """获取沪深300技术指标数据（MA20, MA30等）"""
        cache_key = "hs300_technical_data"
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key]
        
        try:
            logger.info("📊 获取沪深300技术指标数据...")
            
            # 首先尝试使用yfinance获取数据（更稳定）
            try:
                import yfinance as yf
                ticker = "000300.SS"
                stock = yf.Ticker(ticker)
                
                # 获取历史数据（最近60天）
                hist = stock.history(period="60d")
                
                if not hist.empty:
                    # 计算移动平均线
                    hist['MA20'] = hist['Close'].rolling(window=20).mean()
                    hist['MA30'] = hist['Close'].rolling(window=30).mean()
                    
                    # 获取最新数据
                    latest = hist.iloc[-1]
                    prev_day = hist.iloc[-2] if len(hist) >= 2 else latest
                    
                    # 提取关键数据
                    current_price = latest['Close']
                    ma20 = latest['MA20']
                    ma30 = latest['MA30']
                    
                    # 获取5天前的均线值
                    ma20_5d_ago = hist['MA20'].iloc[-6] if len(hist) >= 6 else ma20
                    ma30_5d_ago = hist['MA30'].iloc[-6] if len(hist) >= 6 else ma30
                    
                    vs_ma20 = ((current_price - ma20) / ma20 * 100) if ma20 > 0 else 0
                    vs_ma30 = ((current_price - ma30) / ma30 * 100) if ma30 > 0 else 0
                    
                    # 计算涨跌幅
                    change_pct = ((current_price - prev_day['Close']) / prev_day['Close'] * 100)
                    
                    # 判断均线信号
                    ma_signal = self._determine_ma_signal(current_price, ma20, ma30, vs_ma20, vs_ma30)
                    
                    result = {
                        'price': round(current_price, 2),
                        'change': round(change_pct, 2),
                        'ma20': round(ma20, 2),
                        'ma30': round(ma30, 2),
                        'ma20_5d_ago': round(ma20_5d_ago, 2),
                        'ma30_5d_ago': round(ma30_5d_ago, 2),
                        'vs_ma20': round(vs_ma20, 2),
                        'vs_ma30': round(vs_ma30, 2),
                        'signal': ma_signal,
                        'date': hist.index[-1].strftime('%Y-%m-%d')
                    }
                    
                    # 缓存数据
                    self.cache[cache_key] = result
                    self._set_cache_time(cache_key)
                    
                    logger.info(f"📊 沪深300数据获取成功(yfinance): {current_price:.2f} ({change_pct:+.2f}%)")
                    return result
            
            except Exception as yf_error:
                logger.warning(f"yfinance获取失败，尝试东方财富API: {yf_error}")
            
            # 备选方案：使用东方财富API
            try:
                import requests
                # 东方财富沪深300历史数据API
                url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
                params = {
                    'secid': '1.000300',  # 沪深300指数
                    'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                    'fields1': 'f1,f2,f3,f4,f5,f6',
                    'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                    'klt': '101',  # 日线
                    'fqt': '1',
                    'beg': '0',
                    'end': '20500000'  # 获取足够多的历史数据
                }
                
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'data' in data and 'klines' in data['data']:
                        klines = data['data']['klines']
                        
                        # 构造DataFrame
                        import pandas as pd
                        records = []
                        
                        for kline in klines[-100:]:  # 取最近100天
                            parts = kline.split(',')
                            if len(parts) >= 6:
                                records.append({
                                    '日期': parts[0],
                                    '开盘': float(parts[1]),
                                    '收盘': float(parts[2]),
                                    '最高': float(parts[3]),
                                    '最低': float(parts[4]),
                                    '成交量': float(parts[5])
                                })
                        
                        hs300_data = pd.DataFrame(records)
                        
                        if not hs300_data.empty:
                            logger.info(f"✅ 东方财富沪深300数据获取成功: {len(hs300_data)}天")
                        else:
                            logger.warning("东方财富沪深300数据为空")
                            # 继续使用akshare备用
                            end_date = datetime.now().strftime('%Y%m%d')
                            start_date = (datetime.now() - timedelta(days=100)).strftime('%Y%m%d')
                            hs300_data = ak.index_zh_a_hist(symbol="000300", period="daily", 
                                                          start_date=start_date, end_date=end_date)
                    else:
                        logger.warning("东方财富API返回数据格式异常，回退到akshare")
                        end_date = datetime.now().strftime('%Y%m%d')
                        start_date = (datetime.now() - timedelta(days=100)).strftime('%Y%m%d')
                        hs300_data = ak.index_zh_a_hist(symbol="000300", period="daily", 
                                                      start_date=start_date, end_date=end_date)
                else:
                    logger.warning(f"东方财富API请求失败: {response.status_code}")
                    # 继续使用akshare备用
                    end_date = datetime.now().strftime('%Y%m%d')
                    start_date = (datetime.now() - timedelta(days=100)).strftime('%Y%m%d')
                    hs300_data = ak.index_zh_a_hist(symbol="000300", period="daily", 
                                                  start_date=start_date, end_date=end_date)
                    
            except Exception as em_error:
                logger.warning(f"东方财富API失败，回退到akshare: {em_error}")
                # 最后备选：使用akshare
                end_date = datetime.now().strftime('%Y%m%d')
                start_date = (datetime.now() - timedelta(days=100)).strftime('%Y%m%d')
                hs300_data = ak.index_zh_a_hist(symbol="000300", period="daily", 
                                              start_date=start_date, end_date=end_date)
            
            if hs300_data.empty:
                logger.warning("沪深300数据为空")
                return self._get_default_hs300_data()
            
            # 确保数据按日期排序
            hs300_data = hs300_data.sort_values('日期').reset_index(drop=True)
            
            # 计算移动平均线
            hs300_data['MA20'] = hs300_data['收盘'].rolling(window=20).mean()
            hs300_data['MA30'] = hs300_data['收盘'].rolling(window=30).mean()
            
            # 获取最新数据
            latest = hs300_data.iloc[-1]
            
            # 计算相对位置
            current_price = latest['收盘']
            ma20 = latest['MA20']
            ma30 = latest['MA30']
            
            # 获取5天前的均线值
            ma20_5d_ago = hs300_data['MA20'].iloc[-6] if len(hs300_data) >= 6 else ma20
            ma30_5d_ago = hs300_data['MA30'].iloc[-6] if len(hs300_data) >= 6 else ma30
            
            vs_ma20 = ((current_price - ma20) / ma20 * 100) if ma20 > 0 else 0
            vs_ma30 = ((current_price - ma30) / ma30 * 100) if ma30 > 0 else 0
            
            # 计算涨跌幅
            prev_close = hs300_data.iloc[-2]['收盘'] if len(hs300_data) > 1 else current_price
            change_pct = ((current_price - prev_close) / prev_close * 100) if prev_close > 0 else 0
            
            # 判断均线信号
            ma_signal = self._determine_ma_signal(current_price, ma20, ma30, vs_ma20, vs_ma30)
            
            result = {
                'price': round(current_price, 2),
                'change': round(change_pct, 2),
                'ma20': round(ma20, 2),
                'ma30': round(ma30, 2),
                'ma20_5d_ago': round(ma20_5d_ago, 2),
                'ma30_5d_ago': round(ma30_5d_ago, 2),
                'vs_ma20': round(vs_ma20, 2),
                'vs_ma30': round(vs_ma30, 2),
                'signal': ma_signal,
                'date': latest['日期'].strftime('%Y-%m-%d')
            }
            
            # 缓存数据
            self.cache[cache_key] = result
            self._set_cache_time(cache_key)
            
            logger.info(f"📊 沪深300数据获取成功(akshare): {current_price:.2f} ({change_pct:+.2f}%)")
            return result
            
        except Exception as e:
            logger.error(f"获取沪深300技术指标失败: {e}")
            return self._get_default_hs300_data()
    
    def _get_default_hs300_data(self) -> Dict:
        """获取默认沪深300数据"""
        return {
            'price': 3500.0,
            'change': 0.0,
            'ma20': 3500.0,
            'ma30': 3500.0,
            'ma20_5d_ago': 3500.0,
            'ma30_5d_ago': 3500.0,
            'vs_ma20': 0.0,
            'vs_ma30': 0.0,
            'signal': '数据异常',
            'date': datetime.now().strftime('%Y-%m-%d')
        }
    
    def _determine_ma_signal(self, price: float, ma20: float, ma30: float, 
                           vs_ma20: float, vs_ma30: float) -> str:
        """判断均线信号"""
        if ma20 > ma30 and price > ma20 and vs_ma20 > 2:
            return '强势多头'
        elif ma20 > ma30 and price > ma20:
            return '温和多头'
        elif ma20 < ma30 and price < ma20 and vs_ma20 < -2:
            return '强势空头'
        elif ma20 < ma30 and price < ma20:
            return '温和空头'
        elif abs(vs_ma20) < 1 and abs(vs_ma30) < 1:
            return '均线纠缠'
        else:
            return '震荡整理'
    
    def _calculate_ma_temperature(self, hs300_data: Dict) -> float:
        """计算均线温度 (0-100)"""
        try:
            vs_ma20 = hs300_data.get('vs_ma20', 0)
            vs_ma30 = hs300_data.get('vs_ma30', 0)
            signal = hs300_data.get('signal', '震荡整理')
            
            # 基础温度（基于相对均线位置）
            base_score = 50  # 中性位置
            
            # 相对20日均线的温度贡献
            if vs_ma20 > 5:      # 超过均线5%以上
                ma20_score = 85
            elif vs_ma20 > 3:    # 超过均线3-5%
                ma20_score = 75
            elif vs_ma20 > 1:    # 超过均线1-3%
                ma20_score = 65
            elif vs_ma20 > 0:    # 略超过均线
                ma20_score = 55
            elif vs_ma20 > -1:   # 略低于均线
                ma20_score = 45
            elif vs_ma20 > -3:   # 低于均线1-3%
                ma20_score = 35
            elif vs_ma20 > -5:   # 低于均线3-5%
                ma20_score = 25
            else:                # 低于均线5%以上
                ma20_score = 15
            
            # 相对30日均线的温度贡献
            if vs_ma30 > 5:
                ma30_score = 85
            elif vs_ma30 > 3:
                ma30_score = 75
            elif vs_ma30 > 1:
                ma30_score = 65
            elif vs_ma30 > 0:
                ma30_score = 55
            elif vs_ma30 > -1:
                ma30_score = 45
            elif vs_ma30 > -3:
                ma30_score = 35
            elif vs_ma30 > -5:
                ma30_score = 25
            else:
                ma30_score = 15
            
            # 均线信号加成
            signal_bonus = 0
            if signal == '强势多头':
                signal_bonus = 20
            elif signal == '温和多头':
                signal_bonus = 10
            elif signal == '强势空头':
                signal_bonus = -20
            elif signal == '温和空头':
                signal_bonus = -10
            
            # 综合评分（MA20权重60%, MA30权重40%）
            final_score = ma20_score * 0.6 + ma30_score * 0.4 + signal_bonus
            
            return max(0, min(100, final_score))  # 限制在0-100范围内
            
        except Exception as e:
            logger.warning(f"均线温度计算失败: {e}")
            return 50
    
    def _calculate_enhanced_signal_temperature(self, enhanced_signal) -> float:
        """计算增强信号温度贡献 (0-100)"""
        try:
            # 基于信号强度直接转换
            base_score = enhanced_signal.signal_strength
            
            # 根据信号类型调整权重
            signal_multiplier = 1.0
            if enhanced_signal.signal_type == "强势突破":
                signal_multiplier = 1.2  # 强势突破加权20%
            elif enhanced_signal.signal_type == "温和突破":
                signal_multiplier = 1.1  # 温和突破加权10%
            elif enhanced_signal.signal_type == "震荡突破":
                signal_multiplier = 1.0  # 震荡突破正常权重
            elif enhanced_signal.signal_type == "弱势突破":
                signal_multiplier = 0.9  # 弱势突破减权10%
            else:
                signal_multiplier = 0.8  # 其他情况减权20%
            
            final_score = base_score * signal_multiplier
            
            return max(0, min(100, final_score))
            
        except Exception as e:
            logger.warning(f"增强信号温度计算失败: {e}")
            return 50
    
    def _calculate_up_down_temperature(self, market_data: Dict) -> float:
        """计算涨跌家数温度 (0-100)"""
        try:
            overview = market_data.get('market_overview', {})
            up_stocks = overview.get('up_stocks', 0)
            down_stocks = overview.get('down_stocks', 0)
            total_stocks = overview.get('total_stocks', 1)
            
            if total_stocks == 0:
                return 50  # 无数据时返回中性温度
            
            up_ratio = up_stocks / total_stocks
            
            # 根据涨跌比计算温度
            if up_ratio >= 0.8:  # 80%以上上涨
                return 95
            elif up_ratio >= 0.7:  # 70-80%上涨
                return 85
            elif up_ratio >= 0.6:  # 60-70%上涨
                return 70
            elif up_ratio >= 0.55:  # 55-60%上涨
                return 60
            elif up_ratio >= 0.45:  # 45-55%平衡
                return 50
            elif up_ratio >= 0.4:  # 40-45%下跌
                return 40
            elif up_ratio >= 0.3:  # 30-40%下跌
                return 30
            elif up_ratio >= 0.2:  # 20-30%下跌
                return 15
            else:  # 20%以下上涨
                return 5
                
        except Exception as e:
            logger.warning(f"涨跌家数温度计算失败: {e}")
            return 50
    
    def _calculate_turnover_temperature(self, market_data: Dict) -> float:
        """计算成交额温度 (0-100)"""
        try:
            overview = market_data.get('market_overview', {})
            turnover = overview.get('total_turnover', 0)
            
            if turnover == 0:
                return 20  # 无成交额时温度很低
            
            # 基于成交额水平计算温度
            if turnover >= 20000:  # 2万亿以上
                return 100
            elif turnover >= 15000:  # 1.5-2万亿
                return 85
            elif turnover >= 12000:  # 1.2-1.5万亿
                return 70
            elif turnover >= 10000:  # 1-1.2万亿
                return 55
            elif turnover >= 8000:   # 0.8-1万亿
                return 45
            elif turnover >= 6000:   # 0.6-0.8万亿
                return 30
            elif turnover >= 4000:   # 0.4-0.6万亿
                return 20
            else:  # 0.4万亿以下
                return 10
                
        except Exception as e:
            logger.warning(f"成交额温度计算失败: {e}")
            return 50
    
    def _calculate_margin_temperature(self, market_data: Dict) -> float:
        """计算两融温度 (0-100)"""
        try:
            # 在真实环境中，这里需要调用两融数据API
            # 目前使用模拟数据
            margin_change = self._simulate_margin_data()
            
            # 基于两融余额变化计算温度
            if margin_change >= 3:     # 增长3%以上
                return 90
            elif margin_change >= 2:   # 增长2-3%
                return 80
            elif margin_change >= 1:   # 增长1-2%
                return 70
            elif margin_change >= 0.5: # 增长0.5-1%
                return 60
            elif margin_change >= 0:   # 小幅增长
                return 50
            elif margin_change >= -0.5: # 小幅下降
                return 40
            elif margin_change >= -1:  # 下降0.5-1%
                return 30
            elif margin_change >= -2:  # 下降1-2%
                return 20
            else:  # 下降2%以上
                return 10
                
        except Exception as e:
            logger.warning(f"两融温度计算失败: {e}")
            return 50
    
    def _calculate_etf_temperature(self, market_data: Dict) -> float:
        """计算ETF资金流温度 (0-100)"""
        try:
            # 在真实环境中，这里需要调用ETF资金流API
            # 目前使用模拟数据
            etf_inflow = self._simulate_etf_data()
            
            # 基于ETF资金净流入计算温度
            if etf_inflow >= 100:      # 流入100亿以上
                return 95
            elif etf_inflow >= 50:     # 流入50-100亿
                return 85
            elif etf_inflow >= 20:     # 流入20-50亿
                return 70
            elif etf_inflow >= 10:     # 流入10-20亿
                return 60
            elif etf_inflow >= 0:      # 小幅流入
                return 50
            elif etf_inflow >= -10:    # 小幅流出
                return 40
            elif etf_inflow >= -20:    # 流出10-20亿
                return 30
            elif etf_inflow >= -50:    # 流出20-50亿
                return 15
            else:  # 流出50亿以上
                return 5
                
        except Exception as e:
            logger.warning(f"ETF温度计算失败: {e}")
            return 50
    
    def _determine_temperature_level(self, score: float) -> str:
        """确定温度等级"""
        if score <= self.temperature_thresholds['freezing']:
            return '冰点'
        elif score <= self.temperature_thresholds['cold']:
            return '偏冷'
        elif score <= self.temperature_thresholds['mild']:
            return '温和'
        elif score <= self.temperature_thresholds['warm']:
            return '偏热'
        else:
            return '火热'
    
    def _identify_temperature_sources(self, market_data: Dict, up_down_score: float, 
                                    turnover_score: float, margin_score: float, 
                                    etf_score: float, ma_score: float, enhanced_signal=None) -> Tuple[List[str], List[str]]:
        """识别升温和降温因素"""
        heat_sources = []
        cool_sources = []
        
        # 分析各项指标贡献
        if up_down_score >= 70:
            heat_sources.append(f"涨跌比例健康，上涨股票占优")
        elif up_down_score <= 30:
            cool_sources.append(f"下跌股票较多，市场承压")
        
        if turnover_score >= 70:
            heat_sources.append(f"成交额放大，资金活跃度高")
        elif turnover_score <= 30:
            cool_sources.append(f"成交额萎缩，市场流动性不足")
        
        if margin_score >= 70:
            heat_sources.append(f"两融余额增长，杠杆资金入场")
        elif margin_score <= 30:
            cool_sources.append(f"两融余额下降，杠杆资金退场")
        
        if etf_score >= 70:
            heat_sources.append(f"ETF资金大幅流入，机构看好")
        elif etf_score <= 30:
            cool_sources.append(f"ETF资金流出，机构态度谨慎")
        
        if ma_score >= 70:
            heat_sources.append(f"沪深300突破均线支撑，技术面向好")
        elif ma_score <= 30:
            cool_sources.append(f"沪深300跌破均线支撑，技术面偏弱")
        
        # 增强信号因素分析
        if enhanced_signal:
            if enhanced_signal.signal_type == "强势突破":
                heat_sources.append(f"技术面强势突破，连续{enhanced_signal.consecutive_days}天在均线之上")
                if enhanced_signal.volume_breakout:
                    heat_sources.append(f"放量突破确认，资金大幅流入")
                if enhanced_signal.ma_trend_up:
                    heat_sources.append(f"均线向上排列，趋势明确")
            elif enhanced_signal.signal_type == "温和突破":
                heat_sources.append(f"技术面温和突破，需观察持续性")
            elif enhanced_signal.signal_type in ["震荡整理", "弱势突破"]:
                cool_sources.append(f"技术面缺乏明确方向，处于{enhanced_signal.signal_type}状态")
            
            if not enhanced_signal.above_ma:
                cool_sources.append(f"价格未能站上关键均线，技术面偏弱")
            
            if not enhanced_signal.ma_trend_up:
                cool_sources.append(f"均线趋势向下，中期压力较大")
        
        return heat_sources, cool_sources
    
    def _simulate_margin_data(self) -> float:
        """模拟两融数据"""
        # 实际应用中需要调用真实的两融API
        # 这里模拟一个-2%到+3%的变化范围
        return round(np.random.uniform(-2, 3), 2)
    
    def _simulate_etf_data(self) -> float:
        """模拟ETF资金流数据"""
        # 实际应用中需要调用真实的ETF资金流API
        # 这里模拟一个-80到+120亿的流入流出范围
        return round(np.random.uniform(-80, 120), 1)
    
    def _get_default_temperature(self) -> MarketTemperatureResult:
        """获取默认温度结果"""
        return MarketTemperatureResult(
            temperature_score=50.0,
            temperature_level='温和',
            up_down_ratio=0.5,
            turnover_billion=8000,
            margin_balance=0.0,
            etf_inflow=0.0,
            heat_sources=['数据获取异常'],
            cool_sources=['等待数据恢复'],
            hs300_price=3500.0,
            hs300_change=0.0,
            hs300_ma20=3500.0,
            hs300_ma30=3500.0,
            hs300_ma20_5d_ago=3500.0,
            hs300_ma30_5d_ago=3500.0,
            hs300_vs_ma20=0.0,
            hs300_vs_ma30=0.0,
            ma_signal='数据异常',
            # 增强技术分析默认值
            enhanced_signal='数据异常',
            signal_strength=0.0,
            consecutive_days=0,
            volume_breakout=False,
            ma_trend_up=False,
            pullback_hold=False,
            # 资金流默认值
            today_north_bound=0.0,
            today_etf_inflow=0.0,
            today_main_force=0.0,
            north_bound_3d_total=0.0,
            etf_inflow_3d_total=0.0,
            main_force_3d_total=0.0,
            north_bound_7d_total=0.0,
            etf_inflow_7d_total=0.0,
            main_force_7d_total=0.0,
            north_bound_30d_total=0.0,
            etf_inflow_30d_total=0.0,
            main_force_30d_total=0.0,
            north_bound_trend='数据异常',
            etf_trend='数据异常',
            main_force_trend='数据异常',
            money_flow_score=50.0,
            money_flow_level='数据异常',
            # 情绪周期默认值
            sentiment_phase='数据异常',
            sentiment_score=50.0,
            sentiment_confidence=0.0,
            profit_effect_signal='数据异常',
            high_standard_signal='数据异常',
            turnover_signal='数据异常',
            theme_signal='数据异常',
            etf_sentiment_signal='数据异常'
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
    
    def generate_temperature_report(self) -> str:
        """生成市场温度报告"""
        result = self.analyze_market_temperature()
        
        temperature_icons = {
            '冰点': '🧊',
            '偏冷': '❄️',
            '温和': '🌤️',
            '偏热': '🌡️',
            '火热': '🔥'
        }
        
        icon = temperature_icons.get(result.temperature_level, '🌤️')
        
        report = f"""
🌡️ 市场温度计报告
{'='*40}

{icon} **市场温度**: {result.temperature_score:.1f}/100 ({result.temperature_level})

📊 **关键指标**:
  • 涨跌比例: {result.up_down_ratio:.1%}
  • 成交金额: {result.turnover_billion:.0f}亿元
  • 两融变化: {result.margin_balance:+.2f}%
  • ETF流向: {result.etf_inflow:+.1f}亿元

📈 **沪深300技术分析**:
  • 最新价格: {result.hs300_price:.2f} ({result.hs300_change:+.2f}%)
  • MA20均线: {result.hs300_ma20:.2f} (距离: {result.hs300_vs_ma20:+.2f}%)
  • MA30均线: {result.hs300_ma30:.2f} (距离: {result.hs300_vs_ma30:+.2f}%)
  • 技术信号: {result.ma_signal}

🔥 **升温因素**:"""
        
        if result.heat_sources:
            for source in result.heat_sources:
                report += f"\n  • {source}"
        else:
            report += "\n  • 暂无明显升温因素"
        
        report += f"\n\n❄️ **降温因素**:"
        if result.cool_sources:
            for source in result.cool_sources:
                report += f"\n  • {source}"
        else:
            report += "\n  • 暂无明显降温因素"
        
        report += f"""

💡 **温度建议**:
"""
        if result.temperature_score >= 80:
            report += "  • 市场火热，注意追高风险\n  • 可适度参与，但要控制仓位\n  • 关注回调机会"
        elif result.temperature_score >= 60:
            report += "  • 市场温度适中，可正常操作\n  • 关注热点板块机会\n  • 保持灵活策略"
        elif result.temperature_score >= 40:
            report += "  • 市场偏冷，谨慎参与\n  • 等待升温信号\n  • 可关注超跌标的"
        else:
            report += "  • 市场冰冷，建议观望\n  • 等待明确转暖信号\n  • 保持现金为王"
        
        return report

def main():
    """主函数 - 演示市场温度计功能"""
    print("🌡️ MarketBrew 市场温度计系统")
    print("=" * 50)
    
    analyzer = MarketTemperatureAnalyzer()
    
    # 分析市场温度
    print("🔍 正在分析市场温度...")
    result = analyzer.analyze_market_temperature()
    
    # 生成报告
    report = analyzer.generate_temperature_report()
    print(report)
    
    print(f"\n🔧 技术详情:")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据源: 腾讯财经 + 东方财富 + 模拟数据")

if __name__ == "__main__":
    main()