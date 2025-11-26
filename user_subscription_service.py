#!/usr/bin/env python3
"""
MarketBrew 用户订阅管理服务
管理用户的个性化股票订阅和分析历史
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import datetime
import logging
import requests
from functools import wraps
import jwt

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

DATABASE = 'marketbrew_users.db'
SECRET_KEY = 'marketbrew_secret_key_2024'

# 认证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '需要登录认证', 'code': 'AUTH_REQUIRED'}), 401
        
        token = auth_header.split(' ')[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.user = {
                'id': payload['user_id'],
                'username': payload['username']
            }
            return f(*args, **kwargs)
        except jwt.ExpiredSignatureError:
            return jsonify({'error': '登录已过期，请重新登录', 'code': 'TOKEN_EXPIRED'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': '无效的认证令牌', 'code': 'INVALID_TOKEN'}), 401
    return decorated_function

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'service': 'MarketBrew User Subscription API',
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/api/subscriptions', methods=['GET'])
@login_required
def get_user_subscriptions():
    """获取用户股票订阅列表"""
    try:
        user_id = request.user['id']
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT symbol, name, subscribed_at, alerts_enabled
            FROM user_subscriptions 
            WHERE user_id = ? AND is_active = 1
            ORDER BY subscribed_at DESC
        ''', (user_id,))
        
        subscriptions = []
        for row in cursor.fetchall():
            symbol, name, subscribed_at, alerts_enabled = row
            subscriptions.append({
                'symbol': symbol,
                'name': name,
                'subscribed_at': subscribed_at,
                'alerts_enabled': bool(alerts_enabled)
            })
        
        conn.close()
        
        # 获取实时价格信息
        for sub in subscriptions:
            try:
                response = requests.get(f'http://localhost:5002/api/stock/{sub["symbol"]}', timeout=5)
                if response.status_code == 200:
                    price_data = response.json()
                    sub.update({
                        'current_price': price_data.get('current_price'),
                        'change_percent': price_data.get('change_percent'),
                        'market_status': price_data.get('market_status')
                    })
            except:
                pass  # 价格获取失败，忽略
        
        return jsonify({
            'success': True,
            'subscriptions': subscriptions,
            'total_count': len(subscriptions)
        })
        
    except Exception as e:
        logger.error(f"获取订阅列表失败: {e}")
        return jsonify({'error': '获取订阅列表失败', 'code': 'FETCH_FAILED'}), 500

@app.route('/api/subscriptions', methods=['POST'])
@login_required
def add_subscription():
    """添加股票订阅"""
    try:
        data = request.get_json()
        
        if not data or 'symbol' not in data:
            return jsonify({'error': '股票代码必填', 'code': 'MISSING_SYMBOL'}), 400
        
        user_id = request.user['id']
        symbol = data['symbol'].upper().strip()
        name = data.get('name', '')
        alerts_enabled = data.get('alerts_enabled', True)
        
        # 验证股票代码有效性
        try:
            response = requests.get(f'http://localhost:5002/api/stock/{symbol}', timeout=5)
            if response.status_code != 200:
                return jsonify({'error': '股票代码不存在', 'code': 'INVALID_SYMBOL'}), 400
            
            stock_data = response.json()
            if not name:
                name = stock_data.get('name', symbol)
        except:
            # 如果价格服务不可用，仍然允许添加
            pass
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 检查是否已订阅
        cursor.execute('''
            SELECT id FROM user_subscriptions 
            WHERE user_id = ? AND symbol = ?
        ''', (user_id, symbol))
        
        existing = cursor.fetchone()
        if existing:
            # 重新激活订阅
            cursor.execute('''
                UPDATE user_subscriptions 
                SET is_active = 1, alerts_enabled = ?, subscribed_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND symbol = ?
            ''', (alerts_enabled, user_id, symbol))
        else:
            # 创建新订阅
            cursor.execute('''
                INSERT INTO user_subscriptions (user_id, symbol, name, alerts_enabled)
                VALUES (?, ?, ?, ?)
            ''', (user_id, symbol, name, alerts_enabled))
        
        conn.commit()
        conn.close()
        
        logger.info(f"用户 {request.user['username']} 添加订阅: {symbol}")
        
        return jsonify({
            'success': True,
            'message': '订阅添加成功',
            'subscription': {
                'symbol': symbol,
                'name': name,
                'alerts_enabled': alerts_enabled
            }
        }), 201
        
    except Exception as e:
        logger.error(f"添加订阅失败: {e}")
        return jsonify({'error': '添加订阅失败', 'code': 'ADD_FAILED'}), 500

@app.route('/api/subscriptions/<symbol>', methods=['DELETE'])
@login_required
def remove_subscription(symbol):
    """移除股票订阅"""
    try:
        user_id = request.user['id']
        symbol = symbol.upper().strip()
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_subscriptions 
            SET is_active = 0 
            WHERE user_id = ? AND symbol = ? AND is_active = 1
        ''', (user_id, symbol))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': '订阅不存在', 'code': 'SUBSCRIPTION_NOT_FOUND'}), 404
        
        conn.commit()
        conn.close()
        
        logger.info(f"用户 {request.user['username']} 移除订阅: {symbol}")
        
        return jsonify({
            'success': True,
            'message': '订阅移除成功'
        })
        
    except Exception as e:
        logger.error(f"移除订阅失败: {e}")
        return jsonify({'error': '移除订阅失败', 'code': 'REMOVE_FAILED'}), 500

@app.route('/api/subscriptions/<symbol>/alerts', methods=['PUT'])
@login_required
def toggle_alerts(symbol):
    """切换股票提醒开关"""
    try:
        data = request.get_json()
        user_id = request.user['id']
        symbol = symbol.upper().strip()
        alerts_enabled = data.get('alerts_enabled', True)
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE user_subscriptions 
            SET alerts_enabled = ? 
            WHERE user_id = ? AND symbol = ? AND is_active = 1
        ''', (alerts_enabled, user_id, symbol))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': '订阅不存在', 'code': 'SUBSCRIPTION_NOT_FOUND'}), 404
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'提醒已{"开启" if alerts_enabled else "关闭"}',
            'alerts_enabled': alerts_enabled
        })
        
    except Exception as e:
        logger.error(f"切换提醒失败: {e}")
        return jsonify({'error': '切换提醒失败', 'code': 'TOGGLE_FAILED'}), 500

@app.route('/api/analysis-history', methods=['GET'])
@login_required
def get_analysis_history():
    """获取用户分析历史"""
    try:
        user_id = request.user['id']
        page = int(request.args.get('page', 1))
        limit = min(int(request.args.get('limit', 20)), 100)  # 最多100条
        analysis_type = request.args.get('type', '')  # 'stock', 'market', 'report'
        
        offset = (page - 1) * limit
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 构建查询条件
        where_clause = 'WHERE user_id = ?'
        params = [user_id]
        
        if analysis_type:
            where_clause += ' AND analysis_type = ?'
            params.append(analysis_type)
        
        # 获取总数
        cursor.execute(f'''
            SELECT COUNT(*) FROM user_analysis_history {where_clause}
        ''', params)
        total_count = cursor.fetchone()[0]
        
        # 获取分页数据
        cursor.execute(f'''
            SELECT analysis_type, symbols, analysis_result, created_at
            FROM user_analysis_history 
            {where_clause}
            ORDER BY created_at DESC 
            LIMIT ? OFFSET ?
        ''', params + [limit, offset])
        
        history = []
        for row in cursor.fetchall():
            analysis_type, symbols, analysis_result, created_at = row
            
            try:
                symbols_list = json.loads(symbols) if symbols else []
                result_data = json.loads(analysis_result) if analysis_result else {}
            except:
                symbols_list = []
                result_data = {}
            
            history.append({
                'analysis_type': analysis_type,
                'symbols': symbols_list,
                'result': result_data,
                'created_at': created_at
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'history': history,
            'pagination': {
                'page': page,
                'limit': limit,
                'total_count': total_count,
                'total_pages': (total_count + limit - 1) // limit
            }
        })
        
    except Exception as e:
        logger.error(f"获取分析历史失败: {e}")
        return jsonify({'error': '获取分析历史失败', 'code': 'HISTORY_FAILED'}), 500

@app.route('/api/analysis-history', methods=['POST'])
@login_required
def save_analysis_history():
    """保存分析历史记录"""
    try:
        data = request.get_json()
        
        if not data or 'analysis_type' not in data:
            return jsonify({'error': '分析类型必填', 'code': 'MISSING_TYPE'}), 400
        
        user_id = request.user['id']
        analysis_type = data['analysis_type']
        symbols = json.dumps(data.get('symbols', []), ensure_ascii=False)
        analysis_result = json.dumps(data.get('result', {}), ensure_ascii=False)
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO user_analysis_history (user_id, analysis_type, symbols, analysis_result)
            VALUES (?, ?, ?, ?)
        ''', (user_id, analysis_type, symbols, analysis_result))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '分析历史保存成功'
        }), 201
        
    except Exception as e:
        logger.error(f"保存分析历史失败: {e}")
        return jsonify({'error': '保存分析历史失败', 'code': 'SAVE_FAILED'}), 500

if __name__ == '__main__':
    print("🚀 MarketBrew 用户订阅管理服务启动中...")
    print("📚 API文档:")
    print("  GET /api/subscriptions - 获取用户订阅列表")
    print("  POST /api/subscriptions - 添加股票订阅")
    print("  DELETE /api/subscriptions/<symbol> - 移除股票订阅")
    print("  PUT /api/subscriptions/<symbol>/alerts - 切换提醒开关")
    print("  GET /api/analysis-history - 获取分析历史")
    print("  POST /api/analysis-history - 保存分析历史")
    print(f"🌐 服务运行在: http://localhost:7002")
    
    app.run(host='0.0.0.0', port=7002, debug=True)