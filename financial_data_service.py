#!/usr/bin/env python3
"""
财务数据获取服务
整合多个数据源获取A股财务指标
"""

import requests
import json
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

class FinancialDataProvider:
    """财务数据提供器"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def get_financial_data(self, symbol: str) -> Dict[str, Any]:
        """获取股票财务数据"""
        try:
            # 尝试多个数据源
            data = {}
            
            # 1. 从腾讯财经获取基础数据
            tencent_data = self._get_tencent_financial_data(symbol)
            if tencent_data:
                data.update(tencent_data)
            
            # 2. 从新浪财经获取补充数据
            sina_data = self._get_sina_financial_data(symbol)
            if sina_data:
                data.update(sina_data)
            
            # 3. 从东方财富获取估值数据
            eastmoney_data = self._get_eastmoney_financial_data(symbol)
            if eastmoney_data:
                data.update(eastmoney_data)
            
            # 确保基本字段存在
            data['symbol'] = symbol
            data['timestamp'] = datetime.now().isoformat()
            
            return data
            
        except Exception as e:
            logger.error(f"获取 {symbol} 财务数据失败: {e}")
            return {"error": f"获取财务数据失败: {str(e)}", "symbol": symbol}
    
    def _get_tencent_financial_data(self, symbol: str) -> Dict[str, Any]:
        """从腾讯财经获取财务数据"""
        try:
            # 腾讯财经财务数据API
            formatted_symbol = self._format_symbol_for_tencent(symbol)
            url = f"http://qt.gtimg.cn/q={formatted_symbol}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 解析腾讯数据
            if response.text and '~' in response.text:
                fields = response.text.split('"')[1].split('~')
                if len(fields) > 45:
                    return {
                        'current_price': float(fields[3]) if fields[3] else 0,
                        'market_cap': float(fields[45]) * 10000 if fields[45] and fields[45] != '' else 0,  # 总市值(万元转元)
                        'pe_ratio': float(fields[39]) if fields[39] and fields[39] != '' else 0,  # PE
                        'pb_ratio': float(fields[46]) if fields[46] and fields[46] != '' else 0,  # PB
                        'turnover_rate': float(fields[38]) if fields[38] and fields[38] != '' else 0,  # 换手率
                    }
            
            return {}
            
        except Exception as e:
            logger.warning(f"腾讯财经数据获取失败 {symbol}: {e}")
            return {}
    
    def _get_sina_financial_data(self, symbol: str) -> Dict[str, Any]:
        """从新浪财经获取财务数据"""
        try:
            # 新浪财经API
            formatted_symbol = self._format_symbol_for_sina(symbol)
            url = f"http://hq.sinajs.cn/list={formatted_symbol}"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 解析新浪数据
            if response.text and '=' in response.text:
                data_str = response.text.split('=')[1].strip('"; \n')
                fields = data_str.split(',')
                
                if len(fields) > 30:
                    return {
                        'volume': int(float(fields[8])) if fields[8] else 0,  # 成交量
                        'amount': float(fields[9]) if fields[9] else 0,  # 成交金额
                        'high_52w': float(fields[3]) if fields[3] else 0,  # 当日最高价
                        'low_52w': float(fields[4]) if fields[4] else 0,   # 当日最低价
                    }
            
            return {}
            
        except Exception as e:
            logger.warning(f"新浪财经数据获取失败 {symbol}: {e}")
            return {}
    
    def _get_eastmoney_financial_data(self, symbol: str) -> Dict[str, Any]:
        """从东方财富获取估值数据"""
        try:
            # 构造东方财富API请求
            # 这里使用东方财富的公开API获取更详细的财务数据
            market = 1 if symbol.startswith('6') else 0  # 1=沪市, 0=深市
            url = f"https://push2.eastmoney.com/api/qt/stock/get"
            
            params = {
                'secid': f"{market}.{symbol}",
                'fields': 'f57,f58,f162,f167,f168,f169,f170,f171,f161'  # 各种财务指标
            }
            
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data.get('data'):
                stock_data = data['data']
                return {
                    'roe': stock_data.get('f167', 0) / 100 if stock_data.get('f167') else 0,  # ROE
                    'revenue_growth': stock_data.get('f168', 0) / 100 if stock_data.get('f168') else 0,  # 营收增长率
                    'profit_growth': stock_data.get('f169', 0) / 100 if stock_data.get('f169') else 0,   # 净利润增长率
                    'debt_ratio': stock_data.get('f170', 0) / 100 if stock_data.get('f170') else 0,     # 负债率
                    'gross_margin': stock_data.get('f171', 0) / 100 if stock_data.get('f171') else 0,   # 毛利率
                }
            
            return {}
            
        except Exception as e:
            logger.warning(f"东方财富数据获取失败 {symbol}: {e}")
            return {}
    
    def _format_symbol_for_tencent(self, symbol: str) -> str:
        """格式化股票代码为腾讯格式"""
        clean_symbol = symbol.replace('sz', '').replace('sh', '')
        if clean_symbol.startswith('00') or clean_symbol.startswith('30'):
            return f"sz{clean_symbol}"
        else:
            return f"sh{clean_symbol}"
    
    def _format_symbol_for_sina(self, symbol: str) -> str:
        """格式化股票代码为新浪格式"""
        clean_symbol = symbol.replace('sz', '').replace('sh', '')
        if clean_symbol.startswith('00') or clean_symbol.startswith('30'):
            return f"sz{clean_symbol}"
        else:
            return f"sh{clean_symbol}"
    
    def get_historical_prices(self, symbol: str, days: int = 30) -> List[Dict[str, Any]]:
        """获取历史价格数据"""
        try:
            # 使用腾讯财经获取历史数据
            formatted_symbol = self._format_symbol_for_tencent(symbol)
            url = f"http://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
            
            params = {
                'param': f"{formatted_symbol},day,,,{days},qfq",
                '_var': 'kline_dayqfq'
            }
            
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            # 解析返回的JavaScript格式数据
            text = response.text
            if 'kline_dayqfq=' in text:
                json_str = text.split('kline_dayqfq=')[1]
                data = json.loads(json_str)
                
                if data.get('code') == 0 and data.get('data'):
                    klines = data['data'][symbol.upper()]['day'] if data['data'].get(symbol.upper()) else []
                    
                    result = []
                    for kline in klines[-days:]:  # 取最近N天
                        result.append({
                            'date': kline[0],
                            'open': float(kline[1]),
                            'close': float(kline[2]),
                            'high': float(kline[3]),
                            'low': float(kline[4]),
                            'volume': int(kline[5])
                        })
                    
                    return result
            
            return []
            
        except Exception as e:
            logger.warning(f"获取 {symbol} 历史价格失败: {e}")
            return []

# 创建全局数据提供器实例
financial_provider = FinancialDataProvider()

@app.route('/api/financial/<symbol>', methods=['GET'])
def get_financial_data(symbol):
    """获取单只股票财务数据"""
    try:
        data = financial_provider.get_financial_data(symbol)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/historical/<symbol>', methods=['GET'])
def get_historical_data(symbol):
    """获取历史价格数据"""
    try:
        days = request.args.get('days', 30, type=int)
        data = financial_provider.get_historical_prices(symbol, days)
        return jsonify({
            "symbol": symbol,
            "days": days,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/enhanced/<symbol>', methods=['GET'])
def get_enhanced_data(symbol):
    """获取增强的股票数据（包含财务+历史价格）"""
    try:
        # 获取财务数据
        financial_data = financial_provider.get_financial_data(symbol)
        
        # 获取历史价格
        historical_data = financial_provider.get_historical_prices(symbol, 30)
        
        # 合并数据
        enhanced_data = {
            **financial_data,
            'historical_prices': historical_data,
            'data_sources': ['tencent', 'sina', 'eastmoney'],
            'enhanced': True
        }
        
        return jsonify(enhanced_data)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "Financial Data Service",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/api/financial/<symbol>",
            "/api/historical/<symbol>", 
            "/api/enhanced/<symbol>"
        ]
    })

if __name__ == '__main__':
    print("📊 财务数据服务启动中...")
    print("=" * 50)
    print("📡 服务端口: 5003")
    print("🔗 服务地址: http://localhost:5003")
    print("📈 数据源: 腾讯财经 + 新浪财经 + 东方财富")
    print("\n可用接口:")
    print("  GET  /api/financial/<symbol>   - 获取财务数据")
    print("  GET  /api/historical/<symbol>  - 获取历史价格") 
    print("  GET  /api/enhanced/<symbol>    - 获取增强数据")
    print("  GET  /health                   - 健康检查")
    
    app.run(host='0.0.0.0', port=5003, debug=False)