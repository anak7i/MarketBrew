#!/usr/bin/env python3
"""
综合数据聚合服务
整合所有数据源，为DeepSeek提供完整的投资分析数据
"""

import requests
import json
import asyncio
import aiohttp
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class ComprehensiveDataAggregator:
    """综合数据聚合器"""
    
    def __init__(self):
        self.services = {
            'price': 'http://localhost:5002',      # 价格服务
            'financial': 'http://localhost:5003',  # 财务服务
            'macro': 'http://localhost:5004',      # 宏观服务
            'sentiment': 'http://localhost:5005',  # 情绪服务
            'news': 'http://localhost:5007'        # 新闻公告服务
        }
        self.timeout = 10
        
    def get_complete_stock_analysis_data(self, symbol: str) -> Dict[str, Any]:
        """获取股票的完整分析数据"""
        try:
            logger.info(f"开始聚合股票 {symbol} 的完整数据")
            
            # 并行获取所有数据源
            with ThreadPoolExecutor(max_workers=6) as executor:
                futures = {}
                
                # 提交所有异步任务
                futures['price'] = executor.submit(self._get_price_data, symbol)
                futures['financial'] = executor.submit(self._get_financial_data, symbol)
                futures['macro'] = executor.submit(self._get_macro_data)
                futures['sentiment'] = executor.submit(self._get_sentiment_data, symbol)
                futures['industry'] = executor.submit(self._get_industry_data, symbol)
                futures['news'] = executor.submit(self._get_news_data, symbol)
                futures['announcements'] = executor.submit(self._get_announcements_data, symbol)
                
                # 收集所有结果
                results = {}
                for data_type, future in futures.items():
                    try:
                        results[data_type] = future.result(timeout=self.timeout)
                        logger.info(f"成功获取 {data_type} 数据")
                    except Exception as e:
                        logger.error(f"获取 {data_type} 数据失败: {e}")
                        results[data_type] = {"error": str(e)}
            
            # 聚合数据
            comprehensive_data = self._aggregate_data(symbol, results)
            
            logger.info(f"完成股票 {symbol} 数据聚合")
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"股票数据聚合失败 {symbol}: {e}")
            return {"error": f"数据聚合失败: {str(e)}"}
    
    def _get_price_data(self, symbol: str) -> Dict[str, Any]:
        """获取价格数据"""
        try:
            response = requests.get(f"{self.services['price']}/api/stock/{symbol}", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"价格数据获取失败: {str(e)}"}
    
    def _get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """获取财务数据"""
        try:
            response = requests.get(f"{self.services['financial']}/api/enhanced/{symbol}", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"财务数据获取失败: {str(e)}"}
    
    def _get_macro_data(self) -> Dict[str, Any]:
        """获取宏观数据"""
        try:
            response = requests.get(f"{self.services['macro']}/api/macro", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"宏观数据获取失败: {str(e)}"}
    
    def _get_sentiment_data(self, symbol: str) -> Dict[str, Any]:
        """获取情绪数据"""
        try:
            # 获取个股情绪
            stock_response = requests.get(f"{self.services['sentiment']}/api/stock-sentiment/{symbol}", timeout=self.timeout)
            stock_sentiment = stock_response.json() if stock_response.status_code == 200 else {}
            
            # 获取市场情绪
            market_response = requests.get(f"{self.services['sentiment']}/api/market-sentiment", timeout=self.timeout)
            market_sentiment = market_response.json() if market_response.status_code == 200 else {}
            
            return {
                'stock_sentiment': stock_sentiment,
                'market_sentiment': market_sentiment
            }
        except Exception as e:
            return {"error": f"情绪数据获取失败: {str(e)}"}
    
    def _get_industry_data(self, symbol: str) -> Dict[str, Any]:
        """获取行业数据"""
        try:
            # 推断行业
            sector = self._infer_sector(symbol)
            response = requests.get(f"{self.services['macro']}/api/industry/{sector}", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"行业数据获取失败: {str(e)}"}
    
    def _get_news_data(self, symbol: str) -> Dict[str, Any]:
        """获取新闻数据"""
        try:
            response = requests.get(f"{self.services['news']}/api/news/{symbol}?days=7&limit=10", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"新闻数据获取失败: {str(e)}"}
    
    def _get_announcements_data(self, symbol: str) -> Dict[str, Any]:
        """获取公告数据"""
        try:
            response = requests.get(f"{self.services['news']}/api/announcements/{symbol}?days=30&limit=5", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"公告数据获取失败: {str(e)}"}

    def _infer_sector(self, symbol: str) -> str:
        """推断股票行业"""
        sector_mapping = {
            '600519': '白酒',  # 茅台
            '000858': '白酒',  # 五粮液
            '000001': '银行',  # 平安银行
            '600036': '银行',  # 招商银行
            '300750': '电子',  # 宁德时代
            '002415': '电子',  # 海康威视
            '000002': '地产',  # 万科A
            '600276': '医药',  # 恒瑞医药
        }
        
        return sector_mapping.get(symbol, '电子')
    
    def _aggregate_data(self, symbol: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """聚合所有数据"""
        try:
            aggregated = {
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'data_quality': self._assess_data_quality(results),
                'sources_status': self._get_sources_status(results)
            }
            
            # 基础价格信息
            price_data = results.get('price', {})
            if 'error' not in price_data:
                aggregated['basic_info'] = {
                    'symbol': symbol,
                    'name': price_data.get('name', ''),
                    'current_price': price_data.get('current_price', 0),
                    'change_percent': price_data.get('change_percent', 0),
                    'volume': price_data.get('volume', 0),
                    'market_status': price_data.get('market_status', 'unknown')
                }
            
            # 财务指标数据
            financial_data = results.get('financial', {})
            if 'error' not in financial_data:
                aggregated['financial_metrics'] = {
                    'pe_ratio': financial_data.get('pe_ratio', 0),
                    'pb_ratio': financial_data.get('pb_ratio', 0),
                    'roe': financial_data.get('roe', 0),
                    'revenue_growth': financial_data.get('revenue_growth', 0),
                    'profit_growth': financial_data.get('profit_growth', 0),
                    'debt_ratio': financial_data.get('debt_ratio', 0),
                    'gross_margin': financial_data.get('gross_margin', 0),
                    'market_cap': financial_data.get('market_cap', 0),
                    'data_sources': financial_data.get('data_sources', [])
                }
                
                # 技术指标（基于历史价格计算）
                aggregated['technical_indicators'] = {
                    'ma5': financial_data.get('ma5', 0),
                    'ma20': financial_data.get('ma20', 0),
                    'rsi': financial_data.get('rsi', 50),
                    'macd_trend': financial_data.get('macd_trend', '中性'),
                    'support': financial_data.get('support', 0),
                    'resistance': financial_data.get('resistance', 0),
                    'price_position': financial_data.get('price_position', 0.5),
                    'recent_volatility': financial_data.get('recent_volatility', 0)
                }
            
            # 行业对比数据
            industry_data = results.get('industry', {})
            if 'error' not in industry_data:
                aggregated['industry_comparison'] = {
                    'sector': industry_data.get('sector', ''),
                    'industry_pe': industry_data.get('industry_pe', 0),
                    'industry_pb': industry_data.get('industry_pb', 0),
                    'industry_roe': industry_data.get('industry_roe', 0),
                    'industry_growth': industry_data.get('industry_growth', 0),
                    'policy_support': industry_data.get('policy_support', '中性'),
                    'key_trends': industry_data.get('key_trends', []),
                    'risk_factors': industry_data.get('risk_factors', []),
                    'leading_companies': industry_data.get('leading_companies', [])
                }
            
            # 宏观环境数据
            macro_data = results.get('macro', {})
            if 'error' not in macro_data:
                aggregated['macro_environment'] = {
                    'gdp_growth': macro_data.get('gdp_growth', 0),
                    'cpi': macro_data.get('cpi', 0),
                    'pmi': macro_data.get('pmi', 50),
                    'm2_growth': macro_data.get('m2_growth', 0),
                    'benchmark_rate': macro_data.get('benchmark_rate', 0),
                    'shanghai_index': macro_data.get('shanghai_index', 0),
                    'shanghai_change': macro_data.get('shanghai_change', 0),
                    'northbound_flow': macro_data.get('northbound_flow', 0),
                    'market_turnover': macro_data.get('market_turnover', 0)
                }
            
            # 市场情绪数据
            sentiment_data = results.get('sentiment', {})
            if 'error' not in sentiment_data:
                # 个股情绪
                stock_sentiment = sentiment_data.get('stock_sentiment', {})
                aggregated['stock_sentiment'] = {
                    'main_net_inflow': stock_sentiment.get('fund_flow', {}).get('main_net_inflow', 0),
                    'institutional_action': stock_sentiment.get('fund_flow', {}).get('institutional_action', '观望'),
                    'retail_sentiment': stock_sentiment.get('fund_flow', {}).get('retail_sentiment', '观望'),
                    'search_index': stock_sentiment.get('popularity', {}).get('search_index', 0),
                    'news_sentiment': stock_sentiment.get('popularity', {}).get('news_sentiment', 0),
                    'analyst_rating': stock_sentiment.get('popularity', {}).get('analyst_rating', '持有'),
                    'technical_rating': stock_sentiment.get('technical_sentiment', {}).get('technical_rating', '中性')
                }
                
                    # 市场整体情绪
                market_sentiment = sentiment_data.get('market_sentiment', {})
                sentiment_indicators = market_sentiment.get('sentiment_indicators', {})
                aggregated['market_sentiment'] = {
                    'overall_sentiment_score': sentiment_indicators.get('overall_sentiment_score', 50),
                    'sentiment_level': sentiment_indicators.get('sentiment_level', '中性'),
                    'key_drivers': sentiment_indicators.get('key_drivers', []),
                    'risk_signals': sentiment_indicators.get('risk_signals', []),
                    'fear_greed_index': market_sentiment.get('fear_greed_index', {}).get('index_value', 50)
                }
            
            # 新闻和公告数据
            news_data = results.get('news', {})
            if 'error' not in news_data:
                news_list = news_data.get('news', [])
                aggregated['recent_news'] = {
                    'news_count': len(news_list),
                    'important_news': [
                        {
                            'title': news['title'],
                            'sentiment': news.get('sentiment', 'neutral'),
                            'relevance': news.get('relevance_score', 0.5),
                            'publish_date': news.get('publish_date', ''),
                            'news_type': news.get('news_type', '')
                        }
                        for news in news_list[:5]  # 只取前5条重要新闻
                    ],
                    'positive_news_count': len([n for n in news_list if n.get('sentiment') == 'positive']),
                    'negative_news_count': len([n for n in news_list if n.get('sentiment') == 'negative']),
                    'news_sentiment_score': self._calculate_news_sentiment_score(news_list)
                }
            
            announcements_data = results.get('announcements', {})
            if 'error' not in announcements_data:
                ann_list = announcements_data.get('announcements', [])
                aggregated['recent_announcements'] = {
                    'announcement_count': len(ann_list),
                    'important_announcements': [
                        {
                            'title': ann['title'],
                            'type': ann.get('announcement_type', ''),
                            'importance': ann.get('importance_level', 1),
                            'publish_date': ann.get('publish_date', '')
                        }
                        for ann in ann_list[:3]  # 只取前3条重要公告
                    ],
                    'high_importance_count': len([a for a in ann_list if a.get('importance_level', 1) >= 4]),
                    'latest_financial_report': next(
                        (a for a in ann_list if '季度报告' in a.get('title', '') or '年报' in a.get('title', '')),
                        None
                    )
                }
            
            # 计算投资建议权重
            aggregated['analysis_weights'] = self._calculate_analysis_weights(aggregated)
            
            return aggregated
            
        except Exception as e:
            logger.error(f"数据聚合处理失败 {symbol}: {e}")
            return {"error": f"数据聚合处理失败: {str(e)}"}
    
    def _calculate_news_sentiment_score(self, news_list: List[Dict]) -> float:
        """计算新闻情感综合评分"""
        if not news_list:
            return 50.0  # 中性评分
        
        sentiment_scores = []
        for news in news_list:
            sentiment = news.get('sentiment', 'neutral')
            relevance = news.get('relevance_score', 0.5)
            
            # 基础情感评分
            if sentiment == 'positive':
                base_score = 75
            elif sentiment == 'negative':
                base_score = 25
            else:
                base_score = 50
            
            # 根据相关性调整权重
            weighted_score = base_score * relevance
            sentiment_scores.append(weighted_score)
        
        # 计算加权平均
        if sentiment_scores:
            return sum(sentiment_scores) / len(sentiment_scores)
        return 50.0

    def _assess_data_quality(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """评估数据质量"""
        quality = {
            'overall_score': 0,
            'sources_available': 0,
            'sources_total': len(self.services),
            'issues': []
        }
        
        available_sources = 0
        for source, data in results.items():
            if 'error' not in data:
                available_sources += 1
            else:
                quality['issues'].append(f"{source}数据获取失败")
        
        quality['sources_available'] = available_sources
        quality['overall_score'] = (available_sources / len(self.services)) * 100
        
        if quality['overall_score'] >= 80:
            quality['level'] = '优秀'
        elif quality['overall_score'] >= 60:
            quality['level'] = '良好'
        elif quality['overall_score'] >= 40:
            quality['level'] = '一般'
        else:
            quality['level'] = '较差'
        
        return quality
    
    def _get_sources_status(self, results: Dict[str, Any]) -> Dict[str, str]:
        """获取各数据源状态"""
        status = {}
        for source, data in results.items():
            if 'error' not in data:
                status[source] = '正常'
            else:
                status[source] = '异常'
        return status
    
    def _calculate_analysis_weights(self, data: Dict[str, Any]) -> Dict[str, float]:
        """计算分析权重"""
        weights = {
            'fundamental': 0.4,    # 基本面
            'technical': 0.25,     # 技术面
            'sentiment': 0.2,      # 情绪面
            'macro': 0.15         # 宏观面
        }
        
        # 根据数据可用性调整权重
        data_quality = data.get('data_quality', {})
        if data_quality.get('overall_score', 0) < 80:
            # 如果数据质量不高，降低依赖度，增加基本面权重
            weights['fundamental'] = 0.5
            weights['technical'] = 0.3
            weights['sentiment'] = 0.1
            weights['macro'] = 0.1
        
        return weights
    
    def get_market_overview(self) -> Dict[str, Any]:
        """获取市场总览数据"""
        try:
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = {}
                futures['macro'] = executor.submit(self._get_macro_data)
                futures['market_sentiment'] = executor.submit(self._get_market_sentiment)
                futures['market_context'] = executor.submit(self._get_market_context)
                
                results = {}
                for data_type, future in futures.items():
                    try:
                        results[data_type] = future.result(timeout=self.timeout)
                    except Exception as e:
                        results[data_type] = {"error": str(e)}
            
            overview = {
                'timestamp': datetime.now().isoformat(),
                'market_summary': self._create_market_summary(results),
                'investment_climate': self._assess_investment_climate(results),
                'key_opportunities': self._identify_opportunities(results),
                'major_risks': self._identify_risks(results)
            }
            
            return overview
            
        except Exception as e:
            return {"error": f"市场总览数据获取失败: {str(e)}"}
    
    def _get_market_sentiment(self) -> Dict[str, Any]:
        """获取市场情绪"""
        try:
            response = requests.get(f"{self.services['sentiment']}/api/market-sentiment", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def _get_market_context(self) -> Dict[str, Any]:
        """获取市场环境"""
        try:
            response = requests.post(f"{self.services['macro']}/api/context", 
                                   json={"symbols": ["600519", "000001", "300750"]}, 
                                   timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def _create_market_summary(self, results: Dict[str, Any]) -> Dict[str, str]:
        """创建市场摘要"""
        summary = {}
        
        # 宏观经济摘要
        macro = results.get('macro', {})
        if 'error' not in macro:
            gdp = macro.get('gdp_growth', 5.0)
            cpi = macro.get('cpi', 2.0)
            summary['economic'] = f"GDP增长{gdp:.1f}%, 通胀{cpi:.1f}%"
        
        # 市场情绪摘要
        sentiment = results.get('market_sentiment', {})
        if 'error' not in sentiment:
            sentiment_score = sentiment.get('sentiment_indicators', {}).get('overall_sentiment_score', 50)
            sentiment_level = sentiment.get('sentiment_indicators', {}).get('sentiment_level', '中性')
            summary['sentiment'] = f"情绪指数{sentiment_score:.0f}分({sentiment_level})"
        
        return summary
    
    def _assess_investment_climate(self, results: Dict[str, Any]) -> str:
        """评估投资环境"""
        # 简化的投资环境评估逻辑
        macro = results.get('macro', {})
        sentiment = results.get('market_sentiment', {})
        
        positive_signals = 0
        if macro.get('gdp_growth', 0) > 5:
            positive_signals += 1
        if macro.get('m2_growth', 0) > 8:
            positive_signals += 1
        if sentiment.get('sentiment_indicators', {}).get('overall_sentiment_score', 50) > 60:
            positive_signals += 1
        
        if positive_signals >= 2:
            return '积极'
        elif positive_signals == 1:
            return '谨慎乐观'
        else:
            return '谨慎'
    
    def _identify_opportunities(self, results: Dict[str, Any]) -> List[str]:
        """识别投资机会"""
        opportunities = []
        
        macro = results.get('macro', {})
        if macro.get('m2_growth', 0) > 9:
            opportunities.append('流动性宽松利好成长股')
        if macro.get('pmi', 0) > 52:
            opportunities.append('制造业景气度回升')
        
        return opportunities or ['结构性机会为主']
    
    def _identify_risks(self, results: Dict[str, Any]) -> List[str]:
        """识别主要风险"""
        risks = []
        
        macro = results.get('macro', {})
        if macro.get('cpi', 0) > 3:
            risks.append('通胀压力上升')
        if macro.get('northbound_flow', 0) < -20:
            risks.append('外资大幅流出')
        
        sentiment = results.get('market_sentiment', {})
        fear_greed = sentiment.get('fear_greed_index', {}).get('index_value', 50)
        if fear_greed > 75:
            risks.append('市场过度乐观')
        elif fear_greed < 25:
            risks.append('市场过度悲观')
        
        return risks or ['政策不确定性']

# 创建全局聚合器实例
data_aggregator = ComprehensiveDataAggregator()

@app.route('/api/comprehensive/<symbol>', methods=['GET'])
def get_comprehensive_analysis(symbol):
    """获取股票的完整分析数据"""
    try:
        data = data_aggregator.get_complete_stock_analysis_data(symbol)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/market-overview', methods=['GET'])
def get_market_overview():
    """获取市场总览"""
    try:
        data = data_aggregator.get_market_overview()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "Comprehensive Data Aggregation Service",
        "timestamp": datetime.now().isoformat(),
        "dependent_services": list(data_aggregator.services.keys()),
        "endpoints": [
            "/api/comprehensive/<symbol>",
            "/api/market-overview"
        ]
    })

if __name__ == '__main__':
    print("🔄 综合数据聚合服务启动中...")
    print("=" * 50)
    print("📡 服务端口: 5006")
    print("🔗 服务地址: http://localhost:5006")
    print("🎯 功能: 聚合所有数据源提供完整分析数据")
    print("📊 依赖服务: 价格/财务/宏观/情绪数据服务")
    print("\n可用接口:")
    print("  GET  /api/comprehensive/<symbol> - 获取完整股票分析数据")
    print("  GET  /api/market-overview        - 获取市场总览")
    print("  GET  /health                     - 健康检查")
    
    app.run(host='0.0.0.0', port=5006, debug=False)