#!/usr/bin/env python3
"""
MarketBrew 增强版价格服务
整合东方财富API和腾讯财经API，支持市场温度计功能
"""

import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# 导入东方财富数据服务
from eastmoney_data_service import eastmoney_service

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # 允许跨域请求

class TencentFinanceAPI:
    """腾讯财经API接口类（保留兼容性）"""

    def __init__(self):
        self.base_url = "http://qt.gtimg.cn/q="
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取股票实时信息（优先使用东方财富API）"""
        try:
            # 尝试使用东方财富API
            em_data = eastmoney_service.get_stock_realtime(symbol)
            if em_data:
                return {
                    "symbol": symbol,
                    "name": em_data.get('name', ''),
                    "current_price": em_data.get('price', 0),
                    "prev_close": em_data.get('price', 0) / (1 + em_data.get('change_pct', 0) / 100) if em_data.get('change_pct') else 0,
                    "open": em_data.get('open', 0),
                    "high": em_data.get('high', 0),
                    "low": em_data.get('low', 0),
                    "volume": em_data.get('volume', 0),
                    "change_amount": em_data.get('change', 0),
                    "change_percent": em_data.get('change_pct', 0),
                    "timestamp": datetime.now().isoformat(),
                    "market_status": self._get_market_status(),
                    "data_source": "eastmoney"
                }
        except Exception as e:
            logger.warning(f"东方财富API获取失败，尝试腾讯API: {e}")

        # 降级到腾讯API
        try:
            formatted_symbol = self._format_symbol(symbol)
            url = f"{self.base_url}{formatted_symbol}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return self._parse_response(response.text, symbol)
        except Exception as e:
            logger.error(f"获取股票 {symbol} 数据失败: {e}")
            return {"error": f"获取数据失败: {str(e)}", "symbol": symbol}

    def get_multiple_stocks(self, symbols: List[str]) -> Dict[str, Any]:
        """批量获取多只股票信息"""
        results = {}
        for symbol in symbols:
            results[symbol] = self.get_stock_info(symbol)
            time.sleep(0.05)  # 避免频率限制
        return results

    def _format_symbol(self, symbol: str) -> str:
        """格式化股票代码为腾讯API格式"""
        clean_symbol = symbol.replace('sz', '').replace('sh', '').replace('.SZ', '').replace('.SH', '')

        if clean_symbol.startswith('00') or clean_symbol.startswith('30'):
            return f"sz{clean_symbol}"
        elif clean_symbol.startswith('60') or clean_symbol.startswith('68'):
            return f"sh{clean_symbol}"
        elif clean_symbol.startswith('51') or clean_symbol.startswith('15'):
            if len(clean_symbol) == 6:
                return f"sh{clean_symbol}" if clean_symbol.startswith('51') else f"sz{clean_symbol}"

        return f"sh{clean_symbol}" if clean_symbol.startswith('6') else f"sz{clean_symbol}"

    def _parse_response(self, response_text: str, original_symbol: str) -> Dict[str, Any]:
        """解析腾讯财经API返回的数据"""
        try:
            if not response_text or '~' not in response_text:
                return {"error": "数据格式错误", "symbol": original_symbol}

            data_part = response_text.split('"')[1] if '"' in response_text else response_text
            fields = data_part.split('~')

            if len(fields) < 20:
                return {"error": "数据字段不完整", "symbol": original_symbol}

            name = fields[1]
            current_price = float(fields[3]) if fields[3] and fields[3] != '' else 0
            prev_close = float(fields[4]) if fields[4] and fields[4] != '' else 0
            open_price = float(fields[5]) if fields[5] and fields[5] != '' else 0
            volume = int(fields[6]) if fields[6] and fields[6] != '' else 0
            high_price = float(fields[33]) if len(fields) > 33 and fields[33] else current_price
            low_price = float(fields[34]) if len(fields) > 34 and fields[34] else current_price

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
                "market_status": self._get_market_status(),
                "data_source": "tencent"
            }

        except Exception as e:
            logger.error(f"解析数据失败 {original_symbol}: {e}")
            return {"error": f"解析失败: {str(e)}", "symbol": original_symbol}

    def _get_market_status(self) -> str:
        """获取市场状态"""
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour
        minute = now.minute
        current_time = hour * 60 + minute

        if weekday >= 5:
            return "closed"

        morning_open = 9 * 60 + 30
        morning_close = 11 * 60 + 30
        afternoon_open = 13 * 60
        afternoon_close = 15 * 60

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
api = TencentFinanceAPI()

# ==================== 原有接口 ====================

@app.route('/api/stock/<symbol>', methods=['GET'])
def get_single_stock(symbol):
    """获取单只股票信息"""
    try:
        result = api.get_stock_info(symbol)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stocks', methods=['POST'])
def get_multiple_stocks():
    """批量获取股票信息（支持市场温度计）"""
    try:
        data = request.get_json()
        symbols = data.get('symbols', [])

        # 如果没有提供symbols，返回市场统计数据
        if not symbols:
            stocks = eastmoney_service.get_stock_list('all')
            up_count = len([s for s in stocks if s.get('change_pct', 0) > 0])
            down_count = len([s for s in stocks if s.get('change_pct', 0) < 0])

            return jsonify({
                "total_count": len(stocks),
                "up_count": up_count,
                "down_count": down_count,
                "up_down_ratio": round(up_count / down_count, 2) if down_count > 0 else 0,
                "timestamp": datetime.now().isoformat()
            })

        results = api.get_multiple_stocks(symbols)
        return jsonify(results)
    except Exception as e:
        logger.error(f"批量获取股票失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/market/status', methods=['GET'])
def get_market_status():
    """获取市场状态"""
    return jsonify({
        "status": api._get_market_status(),
        "timestamp": datetime.now().isoformat()
    })

# ==================== 东方财富API新接口 ====================

@app.route('/api/north-bound', methods=['GET'])
def get_north_bound():
    """获取北向资金流向"""
    try:
        data = eastmoney_service.get_north_bound_flow()
        return jsonify(data)
    except Exception as e:
        logger.error(f"获取北向资金失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/main-force', methods=['GET'])
def get_main_force():
    """获取主力资金流向"""
    try:
        data = eastmoney_service.get_main_force_flow()
        return jsonify(data)
    except Exception as e:
        logger.error(f"获取主力资金失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/index/<code>', methods=['GET'])
def get_index(code):
    """获取指数数据"""
    try:
        data = eastmoney_service.get_index_data(code)
        if data:
            return jsonify(data)
        return jsonify({"error": "指数数据获取失败"}), 404
    except Exception as e:
        logger.error(f"获取指数{code}失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/etf/list', methods=['GET'])
def get_etf_list():
    """获取ETF列表"""
    try:
        data = eastmoney_service.get_etf_list()
        return jsonify({"data": data, "count": len(data)})
    except Exception as e:
        logger.error(f"获取ETF列表失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/market-temperature', methods=['GET'])
def get_market_temperature():
    """获取市场温度数据（简化版）"""
    try:
        # 获取股票数据
        stocks = eastmoney_service.get_stock_list('all')
        up_count = len([s for s in stocks if s.get('change_pct', 0) > 0])
        down_count = len([s for s in stocks if s.get('change_pct', 0) < 0])
        total = up_count + down_count

        # 计算温度分数
        up_ratio = up_count / total if total > 0 else 0.5
        temp_score = int(up_ratio * 100)

        # 北向资金
        north_data = eastmoney_service.get_north_bound_flow()
        north_flow = north_data.get('total', 0)

        # 调整温度分数
        if north_flow > 50:
            temp_score += 5
        elif north_flow < -50:
            temp_score -= 5

        temp_score = max(0, min(100, temp_score))

        # 确定温度等级
        if temp_score >= 80:
            level = "过热"
        elif temp_score >= 60:
            level = "偏热"
        elif temp_score >= 40:
            level = "正常"
        elif temp_score >= 20:
            level = "偏冷"
        else:
            level = "冰冷"

        return jsonify({
            "status": "success",
            "data": {
                "temperature_score": temp_score,
                "temperature_level": level,
                "up_count": up_count,
                "down_count": down_count,
                "up_down_ratio": round(up_count / down_count, 2) if down_count > 0 else 0,
                "north_bound_flow": north_flow,
                "total_stocks": total
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"获取市场温度失败: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "MarketBrew Enhanced Price Service",
        "features": ["tencent", "eastmoney", "market-temperature"],
        "timestamp": datetime.now().isoformat()
    })

@app.route('/', methods=['GET'])
def index():
    """首页"""
    return jsonify({
        "name": "MarketBrew Enhanced Price Service",
        "version": "2.0.0",
        "endpoints": {
            "stock": "/api/stock/<symbol>",
            "stocks": "/api/stocks (POST)",
            "market_status": "/api/market/status",
            "north_bound": "/api/north-bound",
            "main_force": "/api/main-force",
            "index": "/api/index/<code>",
            "etf_list": "/api/etf/list",
            "market_temperature": "/api/market-temperature",
            "health": "/health"
        },
        "data_sources": ["eastmoney", "tencent"],
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 MarketBrew 增强版价格服务启动中...")
    print("=" * 60)
    print("📊 数据源: 东方财富 API (优先) + 腾讯财经 API (备用)")
    print("🌡️ 功能: 股票价格 + 市场温度计")
    print("=" * 60)
    print("📡 服务地址: http://localhost:5000")
    print("🔍 API文档: http://localhost:5000")
    print("❤️ 健康检查: http://localhost:5000/health")
    print("=" * 60)
    print()

    app.run(host='0.0.0.0', port=5000, debug=False)
