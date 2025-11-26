#!/usr/bin/env python3
"""
MarketBrew 新闻和公告数据服务
提供公司公告、新闻资讯等数据，支持股票基本面分析
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import sqlite3
import json
import datetime
import logging
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, List, Optional
import feedparser
import threading
from concurrent.futures import ThreadPoolExecutor
from real_news_fetcher import RealNewsDataFetcher

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

DATABASE = 'marketbrew_news.db'

class NewsDatabase:
    """新闻和公告数据库管理类"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 公司公告表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS company_announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(20) NOT NULL,
                company_name VARCHAR(100),
                title VARCHAR(500) NOT NULL,
                content TEXT,
                announcement_type VARCHAR(50),  -- 公告类型: 财报、重大事项、股东大会等
                publish_date TIMESTAMP,
                source_url VARCHAR(500),
                importance_level INTEGER DEFAULT 1,  -- 重要性级别 1-5
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 为公司公告表创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_announcements_symbol_date ON company_announcements(symbol, publish_date)')
        
        # 新闻资讯表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol VARCHAR(20),
                title VARCHAR(500) NOT NULL,
                content TEXT,
                summary VARCHAR(1000),
                news_type VARCHAR(50),  -- 新闻类型: 行业新闻、公司新闻、市场分析等
                publish_date TIMESTAMP,
                source VARCHAR(100),  -- 新闻来源
                source_url VARCHAR(500),
                sentiment VARCHAR(20),  -- 情感分析: positive, negative, neutral
                relevance_score FLOAT DEFAULT 0.5,  -- 与股票的相关性得分
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 为新闻表创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_news_symbol_date ON news_articles(symbol, publish_date)')
        
        # 数据源配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_name VARCHAR(100) NOT NULL,
                source_type VARCHAR(50),  -- RSS, API, SCRAPER
                base_url VARCHAR(500),
                api_key VARCHAR(255),
                is_active BOOLEAN DEFAULT 1,
                last_fetch_time TIMESTAMP,
                fetch_interval_minutes INTEGER DEFAULT 60,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("新闻数据库初始化完成")

class NewsDataCollector:
    """新闻数据收集器"""
    
    def __init__(self, db_path):
        self.db = NewsDatabase(db_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        # 集成真实数据获取器
        self.real_fetcher = RealNewsDataFetcher()
    
    def fetch_sina_finance_news(self, symbol: str) -> List[Dict]:
        """获取新浪财经新闻"""
        try:
            # 新浪财经个股新闻API
            url = f"https://finance.sina.com.cn/stock/quotes/{symbol}/news.html"
            
            # 模拟数据，实际使用时需要解析网页
            sample_news = [
                {
                    'title': f'{symbol} 发布三季度财报，营收同比增长15%',
                    'content': f'公司发布2024年第三季度财务报告，实现营业收入同比增长15%，净利润同比增长12%...',
                    'publish_date': datetime.datetime.now() - datetime.timedelta(hours=2),
                    'source': '新浪财经',
                    'news_type': '财报发布',
                    'sentiment': 'positive',
                    'relevance_score': 0.9
                },
                {
                    'title': f'{symbol} 获得重大合同订单',
                    'content': f'公司近日成功签署重大合作协议，预计将为公司带来显著业绩增长...',
                    'publish_date': datetime.datetime.now() - datetime.timedelta(hours=6),
                    'source': '新浪财经',
                    'news_type': '重大事项',
                    'sentiment': 'positive',
                    'relevance_score': 0.8
                }
            ]
            
            return sample_news
            
        except Exception as e:
            logger.error(f"获取新浪财经新闻失败: {e}")
            return []
    
    def fetch_eastmoney_announcements(self, symbol: str) -> List[Dict]:
        """获取东方财富公告数据"""
        try:
            # 东方财富公告API（模拟）
            sample_announcements = [
                {
                    'title': f'{symbol} 关于召开2024年第三次临时股东大会的通知',
                    'content': '公司董事会决定于2024年12月1日召开临时股东大会...',
                    'announcement_type': '股东大会',
                    'publish_date': datetime.datetime.now() - datetime.timedelta(days=1),
                    'source_url': 'http://www.cninfo.com.cn',
                    'importance_level': 3
                },
                {
                    'title': f'{symbol} 2024年第三季度报告',
                    'content': '公司2024年第三季度实现营业收入...',
                    'announcement_type': '定期报告',
                    'publish_date': datetime.datetime.now() - datetime.timedelta(days=3),
                    'source_url': 'http://www.cninfo.com.cn',
                    'importance_level': 5
                }
            ]
            
            return sample_announcements
            
        except Exception as e:
            logger.error(f"获取东方财富公告失败: {e}")
            return []
    
    def fetch_market_news_rss(self) -> List[Dict]:
        """获取市场新闻RSS源"""
        try:
            rss_sources = [
                'https://finance.sina.com.cn/stock/rss.xml',  # 示例RSS
                'https://www.eastmoney.com/rss/market.xml'
            ]
            
            all_news = []
            for rss_url in rss_sources:
                try:
                    # 实际使用时解析RSS
                    # feed = feedparser.parse(rss_url)
                    
                    # 模拟RSS数据
                    sample_market_news = [
                        {
                            'title': '央行降准释放流动性，A股有望迎来反弹',
                            'content': '央行宣布下调存款准备金率0.25个百分点...',
                            'publish_date': datetime.datetime.now() - datetime.timedelta(minutes=30),
                            'source': '财经新闻',
                            'news_type': '宏观政策',
                            'sentiment': 'positive',
                            'relevance_score': 0.7
                        }
                    ]
                    
                    all_news.extend(sample_market_news)
                    
                except Exception as e:
                    logger.error(f"解析RSS源 {rss_url} 失败: {e}")
                    continue
            
            return all_news
            
        except Exception as e:
            logger.error(f"获取市场新闻RSS失败: {e}")
            return []
    
    def save_news_to_db(self, symbol: str, news_data: List[Dict]):
        """保存新闻数据到数据库"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        for news in news_data:
            try:
                cursor.execute('''
                    INSERT INTO news_articles 
                    (symbol, title, content, summary, news_type, publish_date, source, sentiment, relevance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    news['title'],
                    news.get('content', ''),
                    news.get('summary', ''),
                    news.get('news_type', ''),
                    news['publish_date'].isoformat(),
                    news.get('source', ''),
                    news.get('sentiment', 'neutral'),
                    news.get('relevance_score', 0.5)
                ))
                
            except Exception as e:
                logger.error(f"保存新闻数据失败: {e}")
                continue
        
        conn.commit()
        conn.close()
        logger.info(f"保存了 {len(news_data)} 条新闻数据")
    
    def save_announcements_to_db(self, symbol: str, announcements: List[Dict]):
        """保存公告数据到数据库"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        for announcement in announcements:
            try:
                cursor.execute('''
                    INSERT INTO company_announcements 
                    (symbol, title, content, announcement_type, publish_date, source_url, importance_level)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    symbol,
                    announcement['title'],
                    announcement.get('content', ''),
                    announcement.get('announcement_type', ''),
                    announcement['publish_date'].isoformat(),
                    announcement.get('source_url', ''),
                    announcement.get('importance_level', 1)
                ))
                
            except Exception as e:
                logger.error(f"保存公告数据失败: {e}")
                continue
        
        conn.commit()
        conn.close()
        logger.info(f"保存了 {len(announcements)} 条公告数据")

# 初始化收集器
news_collector = NewsDataCollector(DATABASE)

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'service': 'MarketBrew News & Announcements API',
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/news/<symbol>', methods=['GET'])
def get_stock_news(symbol):
    """获取特定股票的新闻"""
    try:
        symbol = symbol.upper()
        days = int(request.args.get('days', 7))  # 默认获取7天内的新闻
        limit = int(request.args.get('limit', 20))  # 默认限制20条
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 查询最近N天的新闻
        start_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        cursor.execute('''
            SELECT title, content, summary, news_type, publish_date, source, sentiment, relevance_score
            FROM news_articles 
            WHERE symbol = ? AND publish_date >= ?
            ORDER BY publish_date DESC, relevance_score DESC
            LIMIT ?
        ''', (symbol, start_date.isoformat(), limit))
        
        news_list = []
        for row in cursor.fetchall():
            title, content, summary, news_type, publish_date, source, sentiment, relevance_score = row
            news_list.append({
                'title': title,
                'content': content,
                'summary': summary or content[:200] + '...' if content else '',
                'news_type': news_type,
                'publish_date': publish_date,
                'source': source,
                'sentiment': sentiment,
                'relevance_score': relevance_score
            })
        
        conn.close()
        
        # 始终获取实时数据和DeepSeek分析
        # 使用真实数据获取器获取个股新闻（包含DeepSeek分析）
        fresh_news = news_collector.real_fetcher.get_real_company_news(symbol, limit)
        if fresh_news:
            news_list = fresh_news
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'news_count': len(news_list),
            'news': news_list
        })
        
    except Exception as e:
        logger.error(f"获取股票新闻失败: {e}")
        return jsonify({'error': '获取新闻数据失败'}), 500

@app.route('/api/announcements/<symbol>', methods=['GET'])
def get_stock_announcements(symbol):
    """获取特定股票的公告"""
    try:
        symbol = symbol.upper()
        days = int(request.args.get('days', 30))  # 默认获取30天内的公告
        limit = int(request.args.get('limit', 10))
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        start_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        cursor.execute('''
            SELECT title, content, announcement_type, publish_date, source_url, importance_level
            FROM company_announcements 
            WHERE symbol = ? AND publish_date >= ?
            ORDER BY importance_level DESC, publish_date DESC
            LIMIT ?
        ''', (symbol, start_date.isoformat(), limit))
        
        announcements = []
        for row in cursor.fetchall():
            title, content, announcement_type, publish_date, source_url, importance_level = row
            announcements.append({
                'title': title,
                'content': content,
                'announcement_type': announcement_type,
                'publish_date': publish_date,
                'source_url': source_url,
                'importance_level': importance_level
            })
        
        conn.close()
        
        # 始终获取实时数据和DeepSeek分析
        # 使用真实数据获取器获取公司公告（包含DeepSeek分析）
        fresh_announcements = news_collector.real_fetcher.get_real_company_announcements(symbol, limit)
        if fresh_announcements:
            announcements = fresh_announcements
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'announcement_count': len(announcements),
            'announcements': announcements
        })
        
    except Exception as e:
        logger.error(f"获取股票公告失败: {e}")
        return jsonify({'error': '获取公告数据失败'}), 500

@app.route('/api/market-news', methods=['GET'])
def get_market_news():
    """获取市场新闻"""
    try:
        days = int(request.args.get('days', 3))
        limit = int(request.args.get('limit', 15))
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        start_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        cursor.execute('''
            SELECT title, content, summary, news_type, publish_date, source, sentiment
            FROM news_articles 
            WHERE (symbol IS NULL OR symbol = '') AND publish_date >= ?
            ORDER BY publish_date DESC
            LIMIT ?
        ''', (start_date.isoformat(), limit))
        
        market_news = []
        for row in cursor.fetchall():
            title, content, summary, news_type, publish_date, source, sentiment = row
            market_news.append({
                'title': title,
                'content': content,
                'summary': summary or content[:200] + '...' if content else '',
                'news_type': news_type,
                'publish_date': publish_date,
                'source': source,
                'sentiment': sentiment
            })
        
        conn.close()
        
        # 始终获取实时数据和DeepSeek分析
        # 使用真实数据获取器获取市场新闻（包含DeepSeek分析）
        fresh_market_news = news_collector.real_fetcher.get_real_market_news(limit)
        if fresh_market_news:
            market_news = fresh_market_news
        
        return jsonify({
            'success': True,
            'news_count': len(market_news),
            'market_news': market_news
        })
        
    except Exception as e:
        logger.error(f"获取市场新闻失败: {e}")
        return jsonify({'error': '获取市场新闻失败'}), 500

@app.route('/api/news-summary/<symbol>', methods=['GET'])
def get_news_summary(symbol):
    """获取股票新闻摘要（用于AI分析）"""
    try:
        symbol = symbol.upper()
        days = int(request.args.get('days', 7))
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        start_date = datetime.datetime.now() - datetime.timedelta(days=days)
        
        # 获取重要新闻和公告
        cursor.execute('''
            SELECT title, news_type, sentiment, relevance_score, publish_date
            FROM news_articles 
            WHERE symbol = ? AND publish_date >= ? AND relevance_score >= 0.6
            ORDER BY relevance_score DESC, publish_date DESC
            LIMIT 5
        ''', (symbol, start_date.isoformat()))
        
        important_news = cursor.fetchall()
        
        cursor.execute('''
            SELECT title, announcement_type, importance_level, publish_date
            FROM company_announcements 
            WHERE symbol = ? AND publish_date >= ? AND importance_level >= 3
            ORDER BY importance_level DESC, publish_date DESC
            LIMIT 3
        ''', (symbol, start_date.isoformat()))
        
        important_announcements = cursor.fetchall()
        
        conn.close()
        
        # 构建摘要
        summary = {
            'symbol': symbol,
            'period': f'最近{days}天',
            'important_news': [
                {
                    'title': news[0],
                    'type': news[1],
                    'sentiment': news[2],
                    'relevance': news[3],
                    'date': news[4]
                } for news in important_news
            ],
            'important_announcements': [
                {
                    'title': ann[0],
                    'type': ann[1],
                    'importance': ann[2],
                    'date': ann[3]
                } for ann in important_announcements
            ]
        }
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"获取新闻摘要失败: {e}")
        return jsonify({'error': '获取新闻摘要失败'}), 500

@app.route('/api/refresh-data/<symbol>', methods=['POST'])
def refresh_stock_data(symbol):
    """手动刷新股票数据"""
    try:
        symbol = symbol.upper()
        
        # 获取新闻数据
        news_data = news_collector.fetch_sina_finance_news(symbol)
        if news_data:
            news_collector.save_news_to_db(symbol, news_data)
        
        # 获取公告数据
        announcement_data = news_collector.fetch_eastmoney_announcements(symbol)
        if announcement_data:
            news_collector.save_announcements_to_db(symbol, announcement_data)
        
        return jsonify({
            'success': True,
            'message': f'已刷新 {symbol} 的数据',
            'news_updated': len(news_data),
            'announcements_updated': len(announcement_data)
        })
        
    except Exception as e:
        logger.error(f"刷新股票数据失败: {e}")
        return jsonify({'error': '刷新数据失败'}), 500

if __name__ == '__main__':
    print("🚀 MarketBrew 新闻和公告服务启动中...")
    print("📚 API文档:")
    print("  GET /api/news/<symbol> - 获取股票新闻")
    print("  GET /api/announcements/<symbol> - 获取股票公告")
    print("  GET /api/market-news - 获取市场新闻")
    print("  GET /api/news-summary/<symbol> - 获取新闻摘要")
    print("  POST /api/refresh-data/<symbol> - 刷新数据")
    print("  GET /health - 健康检查")
    print(f"🌐 服务运行在: http://localhost:5007")
    
    app.run(host='0.0.0.0', port=5007, debug=True)