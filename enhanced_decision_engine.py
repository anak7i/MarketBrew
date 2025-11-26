#!/usr/bin/env python3
"""
增强版AI决策引擎 - 平衡处理速度和分析质量
整合更多有价值的数据源，同时保持高效的分析速度
"""

import os
import json
import requests
import logging
import asyncio
import aiohttp
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from unified_decision_engine import UnifiedDecisionEngine

class EnhancedDecisionEngine(UnifiedDecisionEngine):
    """增强版决策引擎"""
    
    def __init__(self):
        super().__init__()
        self.data_services = {
            'price': 'http://localhost:5002',      # 实时价格
            'financial': 'http://localhost:5003',  # 财务数据  
            'news': 'http://localhost:5007',       # 新闻公告
            'sentiment': 'http://localhost:5005',  # 市场情绪
        }
        self.enable_enhanced_data = True
        self.max_data_wait_time = 3  # 最大等待时间3秒
        
    def get_enhanced_stock_data(self, symbol: str) -> Dict[str, Any]:
        """获取增强的股票数据 - 快速聚合多数据源"""
        enhanced_data = {
            'price_data': None,
            'financial_data': None,
            'news_data': None,
            'sentiment_data': None,
            'technical_indicators': None
        }
        
        if not self.enable_enhanced_data:
            return enhanced_data
            
        try:
            # 并行获取数据，设置超时保证速度
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = {}
                
                # 实时价格数据（必需）
                futures['price'] = executor.submit(self._get_price_data_fast, symbol)
                
                # 财务数据（重要但可选）
                futures['financial'] = executor.submit(self._get_financial_data_fast, symbol)
                
                # 新闻情绪（可选，增强判断）
                futures['news'] = executor.submit(self._get_news_data_fast, symbol)
                
                # 技术指标计算（本地计算，快速）
                futures['technical'] = executor.submit(self._calculate_technical_indicators, symbol)
                
                # 收集结果，设置超时
                for key, future in futures.items():
                    try:
                        enhanced_data[f'{key}_data'] = future.result(timeout=self.max_data_wait_time)
                    except Exception as e:
                        self.logger.warning(f"获取{key}数据失败: {e}")
                        enhanced_data[f'{key}_data'] = None
                        
        except Exception as e:
            self.logger.error(f"增强数据获取失败: {e}")
            
        return enhanced_data
    
    def _get_price_data_fast(self, symbol: str) -> Optional[Dict]:
        """快速获取价格数据"""
        try:
            response = requests.post(
                f"{self.data_services['price']}/api/stocks",
                json={"symbols": [symbol]},
                timeout=2
            )
            if response.status_code == 200:
                data = response.json()
                return data.get(symbol, {})
        except:
            pass
        return None
    
    def _get_financial_data_fast(self, symbol: str) -> Optional[Dict]:
        """快速获取财务数据"""
        try:
            response = requests.get(
                f"{self.data_services['financial']}/api/financial/{symbol}",
                timeout=2
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def _get_news_data_fast(self, symbol: str) -> Optional[Dict]:
        """快速获取新闻数据"""
        try:
            response = requests.get(
                f"{self.data_services['news']}/api/company-news/{symbol}?limit=3",
                timeout=2
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def _calculate_technical_indicators(self, symbol: str) -> Optional[Dict]:
        """计算技术指标 - 本地快速计算"""
        try:
            # 读取历史价格数据
            data_file = os.path.join(self.data_dir, f'daily_prices_{symbol}.json')
            if not os.path.exists(data_file):
                return None
                
            with open(data_file, 'r', encoding='utf-8') as f:
                stock_data = json.load(f)
            
            time_series = stock_data.get('Time Series (Daily)', {})
            if len(time_series) < 20:  # 需要足够数据计算指标
                return None
                
            # 获取最近20日数据计算技术指标
            recent_dates = sorted(time_series.keys(), reverse=True)[:20]
            prices = []
            volumes = []
            
            for date in recent_dates:
                day_data = time_series[date]
                price = float(day_data.get('4. close', day_data.get('4. sell price', 0)))
                volume = int(day_data.get('5. volume', 0))
                if price > 0:
                    prices.append(price)
                    volumes.append(volume)
            
            if len(prices) < 5:
                return None
            
            # 计算关键技术指标
            current_price = prices[0]
            
            # 5日、10日、20日均线
            ma5 = sum(prices[:5]) / min(5, len(prices))
            ma10 = sum(prices[:10]) / min(10, len(prices))
            ma20 = sum(prices[:20]) / min(20, len(prices))
            
            # 价格趋势
            price_trend = "上升" if current_price > ma5 > ma10 else "下降" if current_price < ma5 < ma10 else "震荡"
            
            # 成交量趋势（最近3日vs前10日平均）
            recent_vol = sum(volumes[:3]) / 3 if len(volumes) >= 3 else volumes[0]
            avg_vol = sum(volumes[:10]) / 10 if len(volumes) >= 10 else recent_vol
            volume_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
            
            # RSI简化计算
            gains = []
            losses = []
            for i in range(1, min(14, len(prices))):
                change = prices[i-1] - prices[i]  # 注意prices是倒序的
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(-change)
            
            if gains and losses:
                avg_gain = sum(gains) / len(gains)
                avg_loss = sum(losses) / len(losses)
                rs = avg_gain / avg_loss if avg_loss > 0 else 100
                rsi = 100 - (100 / (1 + rs))
            else:
                rsi = 50
            
            return {
                'ma5': round(ma5, 2),
                'ma10': round(ma10, 2), 
                'ma20': round(ma20, 2),
                'price_trend': price_trend,
                'volume_ratio': round(volume_ratio, 2),
                'rsi': round(rsi, 1),
                'support_level': round(min(prices[:10]), 2),
                'resistance_level': round(max(prices[:10]), 2)
            }
            
        except Exception as e:
            self.logger.warning(f"技术指标计算失败: {e}")
            return None
    
    def build_enhanced_decision_prompt(self, symbol, name, enhanced_data, current_price, change_pct, current_volume, avg_volume):
        """构建增强版分析提示词"""
        
        # 基础信息
        prompt_parts = [
            f"股票: {symbol} ({name})",
            f"价格: ¥{current_price:.2f} ({change_pct:+.1f}%)",
            f"成交量: {current_volume:,} (平均: {avg_volume:,})"
        ]
        
        # 添加技术指标信息
        tech_data = enhanced_data.get('technical_data')
        if tech_data:
            prompt_parts.append(f"技术面: MA5={tech_data['ma5']} MA10={tech_data['ma10']} 趋势={tech_data['price_trend']}")
            prompt_parts.append(f"量比={tech_data['volume_ratio']:.1f} RSI={tech_data['rsi']}")
        
        # 添加财务信息
        financial_data = enhanced_data.get('financial_data')
        if financial_data and financial_data.get('success'):
            metrics = financial_data.get('data', {})
            if metrics:
                pe_ratio = metrics.get('pe_ratio', 'N/A')
                pb_ratio = metrics.get('pb_ratio', 'N/A')
                roe = metrics.get('roe', 'N/A')
                prompt_parts.append(f"估值: PE={pe_ratio} PB={pb_ratio} ROE={roe}%")
        
        # 添加新闻情绪
        news_data = enhanced_data.get('news_data')
        if news_data and news_data.get('success'):
            news_list = news_data.get('data', [])
            if news_list:
                latest_news = news_list[0].get('title', '')[:50]
                prompt_parts.append(f"最新消息: {latest_news}...")
        
        # 构建完整prompt
        data_section = '\n'.join(prompt_parts)
        
        prompt = f"""{data_section}

请作为专业A股投资顾问，基于以上全面数据给出明确的投资决策：

1. 操作建议: [买入/卖出/持有] (必须明确选择)
2. 信号强度: [强烈/中等/较弱]
3. 核心理由: (综合价格、技术、基本面的主要判断依据)
4. 风险提示: (主要风险点)
5. 目标价位: (如适用)

要求：
- 综合考虑技术面、基本面、资金面
- 理由简洁有力，突出关键因子
- 考虑A股T+1特点和流动性风险
- 决策明确可执行
"""
        return prompt
    
    def analyze_single_stock_enhanced(self, symbol):
        """增强版单股票分析"""
        try:
            # 1. 获取基础数据
            data_file = os.path.join(self.data_dir, f'daily_prices_{symbol}.json')
            if not os.path.exists(data_file):
                return None
            
            with open(data_file, 'r', encoding='utf-8') as f:
                stock_data = json.load(f)
            
            stock_name = self.get_stock_name(symbol)
            time_series = stock_data.get('Time Series (Daily)', {})
            if not time_series:
                return None
                
            recent_dates = sorted(time_series.keys(), reverse=True)[:5]
            if len(recent_dates) < 3:
                return None
                
            # 2. 获取实时价格数据
            real_time_data = self.get_real_time_price(symbol)
            if real_time_data and real_time_data.get('current_price'):
                current_price = float(real_time_data['current_price'])
                change_pct = float(real_time_data.get('change_percent', 0))
                current_volume = int(real_time_data.get('volume', 0))
                self.logger.info(f"📊 {symbol} 使用实时数据: ¥{current_price:.2f} ({change_pct:+.2f}%) 量:{current_volume:,}")
            else:
                # 回退到历史数据
                latest_data = time_series[recent_dates[0]]
                current_price = float(latest_data.get('4. close', latest_data.get('4. sell price', 0)))
                current_volume = int(latest_data.get('5. volume', 0))
                change_pct = 0
                self.logger.info(f"📊 {symbol} 使用历史数据: ¥{current_price:.2f}")
            
            if current_price <= 0.01 or current_volume <= 0:
                return None
            
            # 3. 获取增强数据
            enhanced_data = self.get_enhanced_stock_data(symbol)
            
            # 4. 计算平均成交量
            avg_volume = sum([int(time_series[date].get('5. volume', 0)) for date in recent_dates[:3]]) // 3
            
            # 5. 构建增强版prompt
            prompt = self.build_enhanced_decision_prompt(
                symbol, stock_name, enhanced_data, 
                current_price, change_pct, current_volume, avg_volume
            )
            
            # 6. 调用AI分析
            analysis_result = self.call_deepseek_api(prompt)
            
            # 7. 解析结果
            decision_data = self.parse_analysis_result(
                symbol, stock_name, time_series[recent_dates[0]], 
                analysis_result, current_price, current_volume, change_pct
            )
            
            # 8. 添加增强数据到结果中
            if enhanced_data.get('technical_data'):
                decision_data['technical_indicators'] = enhanced_data['technical_data']
                
            return decision_data
            
        except Exception as e:
            self.logger.error(f"❌ {symbol} 增强分析失败: {e}")
            return None

def create_data_optimization_config():
    """创建数据优化配置"""
    config = {
        "data_priority": {
            "critical": ["real_time_price", "volume", "technical_indicators"],
            "important": ["financial_ratios", "recent_news"],  
            "optional": ["sentiment_analysis", "macro_data"]
        },
        "performance_settings": {
            "max_concurrent_requests": 4,
            "data_timeout_seconds": 3,
            "enable_caching": True,
            "cache_duration_minutes": 5
        },
        "quality_vs_speed": {
            "mode": "balanced",  # fast | balanced | comprehensive
            "min_data_sources": 2,
            "max_wait_time": 3
        }
    }
    return config

if __name__ == "__main__":
    print("=== 增强版决策引擎数据分析 ===")
    
    engine = EnhancedDecisionEngine()
    
    # 测试单股票分析
    test_symbol = "000977"
    result = engine.analyze_single_stock_enhanced(test_symbol)
    
    if result:
        print(f"\n股票: {result['symbol']} {result['name']}")
        print(f"决策: {result['decision']} ({result['strength']})")
        print(f"理由: {result['reason']}")
        print(f"价格: ¥{result['price']} ({result['change_pct']:+.1f}%)")
        print(f"成交量: {result['volume']:,}")
        
        if 'technical_indicators' in result:
            tech = result['technical_indicators']
            print(f"技术指标: MA5={tech['ma5']} 趋势={tech['price_trend']} RSI={tech['rsi']}")
    else:
        print("分析失败")