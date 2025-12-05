#!/usr/bin/env python3
"""
MarketBrew 独立价格服务
基于腾讯财经API获取A股实时价格数据
"""

import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

class TencentFinanceAPI:
    """腾讯财经API接口类"""
    
    def __init__(self):
        self.base_url = "http://qt.gtimg.cn/q="
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票实时信息
        
        Args:
            symbol: 股票代码，如 'sz000001' 或 'sh600519'
            
        Returns:
            包含股票信息的字典
        """
        try:
            # 腾讯财经API格式：sz000001 (深圳) 或 sh600519 (上海)
            formatted_symbol = self._format_symbol(symbol)
            
            url = f"{self.base_url}{formatted_symbol}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 解析返回的数据
            return self._parse_response(response.text, symbol)
            
        except Exception as e:
            logger.error(f"获取股票 {symbol} 数据失败: {e}")
            return {"error": f"获取数据失败: {str(e)}", "symbol": symbol}
    
    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Any]:
        """
        批量获取多只股票信息
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            包含所有股票信息的字典
        """
        results = {}
        
        # 批量请求，腾讯API支持一次查询多只股票
        try:
            formatted_symbols = [self._format_symbol(s) for s in symbols]
            symbols_str = ",".join(formatted_symbols)
            
            url = f"{self.base_url}{symbols_str}"
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # 解析每只股票的数据
            lines = response.text.strip().split('\n')
            for i, line in enumerate(lines):
                if i < len(symbols):
                    results[symbols[i]] = self._parse_response(line, symbols[i])
                    
        except Exception as e:
            logger.error(f"批量获取股票数据失败: {e}")
            # 如果批量失败，逐一获取
            for symbol in symbols:
                results[symbol] = self.get_stock_info(symbol)
                time.sleep(0.1)  # 避免频率限制
                
        return results
    
    def _format_symbol(self, symbol: str) -> str:
        """
        格式化股票代码为腾讯API格式
        
        Args:
            symbol: 原始股票代码，如 '000001', '600519'
            
        Returns:
            腾讯格式，如 'sz000001', 'sh600519'
        """
        # 移除可能的前缀
        clean_symbol = symbol.replace('sz', '').replace('sh', '').replace('.SZ', '').replace('.SH', '')
        
        # 根据代码判断市场
        if clean_symbol.startswith('00') or clean_symbol.startswith('30'):
            # 深圳市场：000xxx, 002xxx, 300xxx
            return f"sz{clean_symbol}"
        elif clean_symbol.startswith('60') or clean_symbol.startswith('68'):
            # 上海市场：600xxx, 601xxx, 603xxx, 688xxx
            return f"sh{clean_symbol}"
        elif clean_symbol.startswith('51') or clean_symbol.startswith('15'):
            # ETF基金
            if len(clean_symbol) == 6:
                if clean_symbol.startswith('51'):
                    return f"sh{clean_symbol}"
                else:
                    return f"sz{clean_symbol}"
        
        # 默认处理
        return f"sh{clean_symbol}" if clean_symbol.startswith('6') else f"sz{clean_symbol}"
    
    def _parse_response(self, response_text: str, original_symbol: str) -> Dict[str, Any]:
        """
        解析腾讯财经API返回的数据
        
        腾讯返回格式：
        v_sz000001="1~平安银行~000001~12.34~12.30~12.35~123456~61728~61728~12.33~12~12.34~10~..."
        """
        try:
            if not response_text or '~' not in response_text:
                return {"error": "数据格式错误", "symbol": original_symbol}
            
            # 提取数据部分
            data_part = response_text.split('"')[1] if '"' in response_text else response_text
            fields = data_part.split('~')
            
            if len(fields) < 20:
                return {"error": "数据字段不完整", "symbol": original_symbol}
            
            # 解析字段
            name = fields[1]  # 股票名称
            current_price = float(fields[3]) if fields[3] and fields[3] != '' else 0  # 当前价
            prev_close = float(fields[4]) if fields[4] and fields[4] != '' else 0  # 昨收价
            open_price = float(fields[5]) if fields[5] and fields[5] != '' else 0  # 开盘价
            volume = int(fields[6]) if fields[6] and fields[6] != '' else 0  # 成交量(手)
            high_price = float(fields[33]) if len(fields) > 33 and fields[33] else current_price  # 最高价
            low_price = float(fields[34]) if len(fields) > 34 and fields[34] else current_price   # 最低价
            
            # 计算涨跌
            change_amount = current_price - prev_close if prev_close > 0 else 0
            change_percent = (change_amount / prev_close * 100) if prev_close > 0 else 0
            
            return {
                "symbol": original_symbol,
                "name": name,
                "current_price": current_price,
                "prev_close": prev_close,
                "open": open_price,
                "high": high_price,
                "low": low_price,
                "volume": volume,
                "change_amount": change_amount,
                "change_percent": change_percent,
                "timestamp": datetime.now().isoformat(),
                "market_status": self._get_market_status()
            }
            
        except Exception as e:
            logger.error(f"解析数据失败 {original_symbol}: {e}")
            return {"error": f"解析失败: {str(e)}", "symbol": original_symbol}
    
    def _get_market_status(self) -> str:
        """获取市场状态"""
        now = datetime.now()
        weekday = now.weekday()  # 0=周一, 6=周日
        hour = now.hour
        minute = now.minute
        current_time = hour * 60 + minute
        
        # 周末
        if weekday >= 5:
            return "closed"
        
        # 交易时间: 9:30-11:30, 13:00-15:00
        morning_open = 9 * 60 + 30  # 9:30
        morning_close = 11 * 60 + 30  # 11:30
        afternoon_open = 13 * 60  # 13:00
        afternoon_close = 15 * 60  # 15:00
        
        if (morning_open <= current_time <= morning_close) or \
           (afternoon_open <= current_time <= afternoon_close):
            return "trading"
        elif current_time < morning_open:
            return "pre_market"
        elif morning_close < current_time < afternoon_open:
            return "lunch_break"
        else:
            return "after_market"

# 全局API实例
tencent_api = TencentFinanceAPI()

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_single_stock(symbol):
    """获取单只股票信息"""
    try:
        result = tencent_api.get_stock_info(symbol)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stocks', methods=['POST'])
def get_multiple_stocks():
    """批量获取股票信息"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])

        # 如果没有提供symbols，返回市场统计（用于市场温度计）
        if not symbols:
            import random
            # 模拟市场统计数据
            up_count = random.randint(2000, 3500)
            down_count = random.randint(1000, 2500)

            return jsonify({
                "total_count": up_count + down_count,
                "up_count": up_count,
                "down_count": down_count,
                "up_down_ratio": round(up_count / down_count, 2) if down_count > 0 else 0,
                "timestamp": datetime.now().isoformat()
            })

        results = tencent_api.get_multiple_stocks(symbols)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/market/status', methods=['GET'])
def get_market_status():
    """获取市场状态"""
    return jsonify({
        "status": tencent_api._get_market_status(),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/north-bound', methods=['GET'])
def get_north_bound():
    """获取北向资金（模拟数据）"""
    import random
    return jsonify({
        "total": round(random.uniform(-50, 100), 2),
        "sh": round(random.uniform(-30, 60), 2),
        "sz": round(random.uniform(-20, 40), 2),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/index/<code>', methods=['GET'])
def get_index(code):
    """获取指数数据"""
    result = tencent_api.get_stock_info(code)
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "MarketBrew Price Service",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 MarketBrew 价格服务启动中...")
    print("=" * 60)
    print("📊 数据源: 腾讯财经 API")
    print("🌡️ 功能: 股票价格 + 市场温度计")
    print("=" * 60)
    print("🔗 服务地址: http://localhost:5000")
    print("\n可用接口:")
    print("  GET  /api/stock/<symbol>     - 获取单只股票")
    print("  POST /api/stocks            - 批量获取股票")
    print("  GET  /api/market/status     - 市场状态")
    print("  GET  /api/north-bound       - 北向资金")
    print("  GET  /api/index/<code>      - 指数数据")
    print("  GET  /health               - 健康检查")
    print("=" * 60)
    print()

    app.run(host='0.0.0.0', port=5000, debug=False)