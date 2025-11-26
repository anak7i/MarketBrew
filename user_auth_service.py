#!/usr/bin/env python3
"""
MarketBrew 用户认证服务
提供用户注册、登录、个人资料管理等功能
"""

from flask import Flask, request, jsonify, session
from flask_cors import CORS
import sqlite3
import hashlib
import secrets
import jwt
import datetime
import os
from functools import wraps
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 配置
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'marketbrew_secret_key_2024')
app.secret_key = SECRET_KEY
DATABASE = 'marketbrew_users.db'

class UserDatabase:
    """用户数据库管理类"""
    
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                salt VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                phone VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                subscription_level VARCHAR(20) DEFAULT 'basic',
                preferences TEXT  -- JSON格式存储用户偏好
            )
        ''')
        
        # 用户会话表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # 用户股票订阅表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                symbol VARCHAR(20) NOT NULL,
                name VARCHAR(100),
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                alerts_enabled BOOLEAN DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, symbol)
            )
        ''')
        
        # 用户分析历史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_analysis_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                analysis_type VARCHAR(50),  -- 'stock', 'market', 'report'
                symbols TEXT,  -- JSON格式存储股票代码列表
                analysis_result TEXT,  -- JSON格式存储分析结果
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("数据库初始化完成")

class UserAuth:
    """用户认证管理类"""
    
    def __init__(self, db_path):
        self.db = UserDatabase(db_path)
    
    def hash_password(self, password, salt=None):
        """密码哈希加密"""
        if salt is None:
            salt = secrets.token_hex(32)
        password_hash = hashlib.pbkdf2_hmac('sha256', 
                                           password.encode('utf-8'), 
                                           salt.encode('utf-8'), 
                                           100000)
        return password_hash.hex(), salt
    
    def verify_password(self, password, password_hash, salt):
        """验证密码"""
        new_hash, _ = self.hash_password(password, salt)
        return new_hash == password_hash
    
    def generate_jwt_token(self, user_id, username):
        """生成JWT令牌"""
        payload = {
            'user_id': user_id,
            'username': username,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),  # 7天有效期
            'iat': datetime.datetime.utcnow()
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return token
    
    def verify_jwt_token(self, token):
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

# 初始化认证系统
user_auth = UserAuth(DATABASE)

# 认证装饰器
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': '需要登录认证', 'code': 'AUTH_REQUIRED'}), 401
        
        token = auth_header.split(' ')[1]
        payload = user_auth.verify_jwt_token(token)
        if not payload:
            return jsonify({'error': '登录已过期，请重新登录', 'code': 'TOKEN_EXPIRED'}), 401
        
        request.user = {
            'id': payload['user_id'],
            'username': payload['username']
        }
        return f(*args, **kwargs)
    return decorated_function

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'service': 'MarketBrew User Auth API',
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'database_connected': True
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        required_fields = ['username', 'email', 'password']
        if not all(field in data for field in required_fields):
            return jsonify({'error': '缺少必需字段', 'code': 'MISSING_FIELDS'}), 400
        
        username = data['username'].strip()
        email = data['email'].strip().lower()
        password = data['password']
        
        # 基本验证
        if len(username) < 3:
            return jsonify({'error': '用户名至少3个字符', 'code': 'USERNAME_TOO_SHORT'}), 400
        
        if len(password) < 6:
            return jsonify({'error': '密码至少6个字符', 'code': 'PASSWORD_TOO_SHORT'}), 400
        
        # 连接数据库
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 检查用户名和邮箱是否已存在
        cursor.execute('SELECT id FROM users WHERE username = ? OR email = ?', (username, email))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': '用户名或邮箱已存在', 'code': 'USER_EXISTS'}), 409
        
        # 创建用户
        password_hash, salt = user_auth.hash_password(password)
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, salt, subscription_level)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, password_hash, salt, 'basic'))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # 生成JWT令牌
        token = user_auth.generate_jwt_token(user_id, username)
        
        logger.info(f"新用户注册成功: {username}")
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'subscription_level': 'basic'
            },
            'token': token
        }), 201
        
    except Exception as e:
        logger.error(f"注册失败: {e}")
        return jsonify({'error': '注册失败，请稍后重试', 'code': 'REGISTER_FAILED'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': '用户名和密码必填', 'code': 'MISSING_CREDENTIALS'}), 400
        
        username = data['username'].strip()
        password = data['password']
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # 查找用户
        cursor.execute('''
            SELECT id, username, email, password_hash, salt, full_name, subscription_level, is_active
            FROM users WHERE username = ? OR email = ?
        ''', (username, username))
        
        user = cursor.fetchone()
        if not user or not user[7]:  # 用户不存在或已禁用
            conn.close()
            return jsonify({'error': '用户名或密码错误', 'code': 'INVALID_CREDENTIALS'}), 401
        
        # 验证密码
        user_id, username, email, password_hash, salt, full_name, subscription_level, is_active = user
        if not user_auth.verify_password(password, password_hash, salt):
            conn.close()
            return jsonify({'error': '用户名或密码错误', 'code': 'INVALID_CREDENTIALS'}), 401
        
        # 更新最后登录时间
        cursor.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        # 生成JWT令牌
        token = user_auth.generate_jwt_token(user_id, username)
        
        logger.info(f"用户登录成功: {username}")
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'full_name': full_name,
                'subscription_level': subscription_level
            },
            'token': token
        })
        
    except Exception as e:
        logger.error(f"登录失败: {e}")
        return jsonify({'error': '登录失败，请稍后重试', 'code': 'LOGIN_FAILED'}), 500

@app.route('/api/auth/profile', methods=['GET'])
@login_required
def get_profile():
    """获取用户资料"""
    try:
        user_id = request.user['id']
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT username, email, full_name, phone, subscription_level, created_at, last_login
            FROM users WHERE id = ?
        ''', (user_id,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'error': '用户不存在', 'code': 'USER_NOT_FOUND'}), 404
        
        username, email, full_name, phone, subscription_level, created_at, last_login = user
        
        return jsonify({
            'success': True,
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'full_name': full_name,
                'phone': phone,
                'subscription_level': subscription_level,
                'created_at': created_at,
                'last_login': last_login
            }
        })
        
    except Exception as e:
        logger.error(f"获取用户资料失败: {e}")
        return jsonify({'error': '获取用户资料失败', 'code': 'PROFILE_FAILED'}), 500

@app.route('/api/auth/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新用户资料"""
    try:
        data = request.get_json()
        user_id = request.user['id']
        
        # 可更新的字段
        updatable_fields = ['full_name', 'phone', 'email']
        update_data = {}
        
        for field in updatable_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': '没有要更新的数据', 'code': 'NO_UPDATE_DATA'}), 400
        
        # 构建SQL更新语句
        set_clause = ', '.join([f"{field} = ?" for field in update_data.keys()])
        values = list(update_data.values()) + [user_id]
        
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        cursor.execute(f'UPDATE users SET {set_clause} WHERE id = ?', values)
        conn.commit()
        conn.close()
        
        logger.info(f"用户资料更新成功: {request.user['username']}")
        
        return jsonify({
            'success': True,
            'message': '资料更新成功',
            'updated_fields': list(update_data.keys())
        })
        
    except Exception as e:
        logger.error(f"更新用户资料失败: {e}")
        return jsonify({'error': '更新资料失败', 'code': 'UPDATE_FAILED'}), 500

if __name__ == '__main__':
    print("🚀 MarketBrew 用户认证服务启动中...")
    print("📚 API文档:")
    print("  POST /api/auth/register - 用户注册")
    print("  POST /api/auth/login - 用户登录")  
    print("  GET /api/auth/profile - 获取用户资料")
    print("  PUT /api/auth/profile - 更新用户资料")
    print("  GET /health - 健康检查")
    print(f"🌐 服务运行在: http://localhost:7001")
    
    app.run(host='0.0.0.0', port=7001, debug=True)