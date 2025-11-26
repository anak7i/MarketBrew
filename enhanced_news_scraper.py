#!/usr/bin/env python3
"""
增强版新闻数据抓取器
支持多个数据源的新闻和公告抓取
"""

import requests
import json
import time
import random
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime, timedelta
import logging
import re
from typing import Dict, List, Optional
import sqlite3

logger = logging.getLogger(__name__)

class EnhancedNewsScraper:
    """增强版新闻抓取器"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        # 新闻源配置
        self.news_sources = {
            'eastmoney': {
                'name': '东方财富',
                'base_url': 'https://stock.eastmoney.com',
                'enabled': True
            },
            'sina': {
                'name': '新浪财经', 
                'base_url': 'https://finance.sina.com.cn',
                'enabled': True
            },
            'cninfo': {
                'name': '巨潮资讯',
                'base_url': 'http://www.cninfo.com.cn',
                'enabled': True
            }
        }
    
    def extract_stock_code_from_url(self, url: str) -> Optional[str]:
        """从URL中提取股票代码"""
        patterns = [
            r'stock/(\d{6})',
            r'sz(\d{6})',
            r'sh(\d{6})',
            r'(\d{6})\.sz',
            r'(\d{6})\.sh'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def fetch_eastmoney_stock_news(self, symbol: str) -> List[Dict]:
        """从东方财富获取个股新闻"""
        try:
            # 构造东方财富个股新闻API
            api_url = f"https://push2his.eastmoney.com/api/qt/stock/fflow/klinend"
            
            # 实际项目中需要解析具体的API响应
            # 这里提供模拟数据结构
            sample_news = [
                {
                    'title': f'{symbol} 三季报业绩超预期，机构上调目标价',
                    'content': '公司发布的三季度报告显示，营收和净利润均实现双位数增长，主要受益于核心业务的强劲表现。多家券商机构在业绩发布后上调了公司的目标价...',
                    'publish_date': datetime.now() - timedelta(hours=3),
                    'source': '东方财富',
                    'news_type': '业绩分析',
                    'sentiment': 'positive',
                    'relevance_score': 0.9,
                    'source_url': f'https://stock.eastmoney.com/{symbol}.html'
                },
                {
                    'title': f'{symbol} 获得政府补贴支持',
                    'content': '公司近日收到当地政府产业扶持资金，将用于技术研发和产能扩张，有助于提升公司竞争力...',
                    'publish_date': datetime.now() - timedelta(hours=8),
                    'source': '东方财富',
                    'news_type': '政策支持',
                    'sentiment': 'positive',
                    'relevance_score': 0.7,
                    'source_url': f'https://stock.eastmoney.com/{symbol}.html'
                }
            ]
            
            return sample_news
            
        except Exception as e:
            logger.error(f"获取东方财富新闻失败 {symbol}: {e}")
            return []
    
    def fetch_sina_stock_news(self, symbol: str) -> List[Dict]:
        """从新浪财经获取个股新闻"""
        try:
            # 新浪财经个股新闻页面
            url = f"https://finance.sina.com.cn/stock/quotes/{symbol}/news.html"
            
            # 模拟新闻数据
            sample_news = [
                {
                    'title': f'{symbol} 签署战略合作协议，拓展新兴市场',
                    'content': '公司与行业龙头企业签署战略合作协议，将在技术研发、市场拓展等方面深度合作，预计将带来新的增长点...',
                    'publish_date': datetime.now() - timedelta(hours=5),
                    'source': '新浪财经',
                    'news_type': '业务合作',
                    'sentiment': 'positive',
                    'relevance_score': 0.8,
                    'source_url': f'https://finance.sina.com.cn/stock/s_{symbol}.html'
                }
            ]
            
            return sample_news
            
        except Exception as e:
            logger.error(f"获取新浪财经新闻失败 {symbol}: {e}")
            return []
    
    def fetch_cninfo_announcements(self, symbol: str) -> List[Dict]:
        """从巨潮资讯获取公告数据"""
        try:
            # 巨潮资讯是主要的公告披露平台
            base_url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
            
            # 模拟公告数据
            sample_announcements = [
                {
                    'title': f'{symbol} 关于使用闲置募集资金进行现金管理的公告',
                    'content': '为提高募集资金使用效率，在保证募集资金安全的前提下，公司拟使用部分闲置募集资金进行现金管理...',
                    'announcement_type': '募集资金',
                    'publish_date': datetime.now() - timedelta(days=2),
                    'source_url': 'http://www.cninfo.com.cn',
                    'importance_level': 3,
                    'company_name': f'{symbol}股份有限公司'
                },
                {
                    'title': f'{symbol} 2024年第三季度报告',
                    'content': '公司2024年前三季度实现营业收入XX亿元，同比增长XX%；实现归属于上市公司股东的净利润XX亿元...',
                    'announcement_type': '定期报告',
                    'publish_date': datetime.now() - timedelta(days=5),
                    'source_url': 'http://www.cninfo.com.cn',
                    'importance_level': 5,
                    'company_name': f'{symbol}股份有限公司'
                },
                {
                    'title': f'{symbol} 关于股东减持股份计划的预披露公告',
                    'content': '公司收到持股5%以上股东的告知函，该股东计划在未来6个月内减持不超过公司总股本2%的股份...',
                    'announcement_type': '股东减持',
                    'publish_date': datetime.now() - timedelta(days=7),
                    'source_url': 'http://www.cninfo.com.cn',
                    'importance_level': 4,
                    'company_name': f'{symbol}股份有限公司'
                }
            ]
            
            return sample_announcements
            
        except Exception as e:
            logger.error(f"获取巨潮资讯公告失败 {symbol}: {e}")
            return []
    
    def fetch_market_news_rss(self) -> List[Dict]:
        """获取市场新闻RSS源"""
        try:
            rss_feeds = [
                'https://rss.cnn.com/rss/money_news_markets.rss',
                'https://feeds.finance.yahoo.com/rss/2.0/headline'
            ]
            
            all_market_news = []
            
            # 模拟市场新闻数据
            sample_market_news = [
                {
                    'title': '央行开展1000亿元逆回购操作，维护流动性合理充裕',
                    'content': '为维护银行体系流动性合理充裕，央行今日开展1000亿元7天期逆回购操作，中标利率维持1.80%不变...',
                    'publish_date': datetime.now() - timedelta(hours=2),
                    'source': '央行官网',
                    'news_type': '货币政策',
                    'sentiment': 'positive',
                    'relevance_score': 0.8
                },
                {
                    'title': '证监会：支持优质企业境内外上市融资',
                    'content': '证监会表示，将继续支持符合条件的优质企业在境内外资本市场上市融资，推动提高上市公司质量...',
                    'publish_date': datetime.now() - timedelta(hours=4),
                    'source': '证监会',
                    'news_type': '监管政策',
                    'sentiment': 'positive',
                    'relevance_score': 0.7
                },
                {
                    'title': 'A股三大指数集体收涨，创业板指涨超1%',
                    'content': '今日A股三大指数集体收涨，上证指数上涨0.8%，深证成指上涨1.2%，创业板指上涨1.5%。两市成交额突破8000亿元...',
                    'publish_date': datetime.now() - timedelta(hours=6),
                    'source': '证券时报',
                    'news_type': '市场动态',
                    'sentiment': 'positive',
                    'relevance_score': 0.9
                }
            ]
            
            all_market_news.extend(sample_market_news)
            
            return all_market_news
            
        except Exception as e:
            logger.error(f"获取市场新闻RSS失败: {e}")
            return []
    
    def analyze_sentiment(self, title: str, content: str) -> str:
        """简单的情感分析"""
        positive_words = ['上涨', '增长', '利好', '突破', '超预期', '收购', '合作', '获得', '支持', '回升']
        negative_words = ['下跌', '下滑', '亏损', '风险', '减持', '停牌', '违规', '调查', '处罚', '警示']
        
        text = title + ' ' + content
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def calculate_relevance_score(self, title: str, content: str, symbol: str) -> float:
        """计算新闻与股票的相关性评分"""
        # 基础相关性
        base_score = 0.3
        
        # 标题中包含股票代码
        if symbol in title:
            base_score += 0.4
        
        # 内容中包含股票代码
        if symbol in content:
            base_score += 0.2
        
        # 包含重要关键词
        important_keywords = ['财报', '业绩', '收购', '重组', '分红', '股东大会']
        for keyword in important_keywords:
            if keyword in title or keyword in content:
                base_score += 0.1
                break
        
        return min(base_score, 1.0)
    
    def fetch_all_data(self, symbol: str) -> Dict:
        """获取指定股票的所有新闻和公告数据"""
        try:
            all_news = []
            all_announcements = []
            
            # 获取各源新闻
            if self.news_sources['eastmoney']['enabled']:
                eastmoney_news = self.fetch_eastmoney_stock_news(symbol)
                all_news.extend(eastmoney_news)
            
            if self.news_sources['sina']['enabled']:
                sina_news = self.fetch_sina_stock_news(symbol)
                all_news.extend(sina_news)
            
            # 获取公告
            if self.news_sources['cninfo']['enabled']:
                cninfo_announcements = self.fetch_cninfo_announcements(symbol)
                all_announcements.extend(cninfo_announcements)
            
            # 处理新闻数据
            for news in all_news:
                if 'sentiment' not in news:
                    news['sentiment'] = self.analyze_sentiment(news['title'], news.get('content', ''))
                if 'relevance_score' not in news:
                    news['relevance_score'] = self.calculate_relevance_score(
                        news['title'], news.get('content', ''), symbol
                    )
            
            logger.info(f"为 {symbol} 获取了 {len(all_news)} 条新闻，{len(all_announcements)} 条公告")
            
            return {
                'symbol': symbol,
                'news': all_news,
                'announcements': all_announcements,
                'fetch_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取 {symbol} 数据失败: {e}")
            return {'symbol': symbol, 'news': [], 'announcements': [], 'error': str(e)}
    
    def save_to_database(self, data: Dict):
        """保存数据到数据库"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            symbol = data['symbol']
            
            # 保存新闻
            for news in data.get('news', []):
                cursor.execute('''
                    INSERT OR IGNORE INTO news_articles 
                    (symbol, title, content, summary, news_type, publish_date, source, sentiment, relevance_score, source_url)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    news['title'],
                    news.get('content', ''),
                    news.get('summary', ''),
                    news.get('news_type', ''),
                    news['publish_date'].isoformat() if isinstance(news['publish_date'], datetime) else news['publish_date'],
                    news.get('source', ''),
                    news.get('sentiment', 'neutral'),
                    news.get('relevance_score', 0.5),
                    news.get('source_url', '')
                ))
            
            # 保存公告
            for announcement in data.get('announcements', []):
                cursor.execute('''
                    INSERT OR IGNORE INTO company_announcements 
                    (symbol, company_name, title, content, announcement_type, publish_date, source_url, importance_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    announcement.get('company_name', ''),
                    announcement['title'],
                    announcement.get('content', ''),
                    announcement.get('announcement_type', ''),
                    announcement['publish_date'].isoformat() if isinstance(announcement['publish_date'], datetime) else announcement['publish_date'],
                    announcement.get('source_url', ''),
                    announcement.get('importance_level', 1)
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"成功保存 {symbol} 的 {len(data.get('news', []))} 条新闻和 {len(data.get('announcements', []))} 条公告")
            
        except Exception as e:
            logger.error(f"保存数据到数据库失败: {e}")

if __name__ == "__main__":
    # 测试抓取器
    scraper = EnhancedNewsScraper('marketbrew_news.db')
    
    # 测试获取数据
    test_symbols = ['000001', '600519', '300750']
    
    for symbol in test_symbols:
        print(f"正在获取 {symbol} 的数据...")
        data = scraper.fetch_all_data(symbol)
        scraper.save_to_database(data)
        time.sleep(1)  # 避免请求过于频繁
        
    print("数据获取完成！")