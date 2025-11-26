#!/usr/bin/env python3
"""
股票订阅推送API服务器
提供订阅管理、推送服务的RESTful API接口
"""

import os
import json
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

from subscription_manager import StockSubscriptionManager

class SubscriptionAPIHandler(BaseHTTPRequestHandler):
    """订阅API请求处理器"""
    
    def __init__(self, *args, **kwargs):
        # 使用全局的订阅管理器实例
        self.manager = getattr(self.server, 'subscription_manager', None)
        if not self.manager:
            self.manager = StockSubscriptionManager()
            self.server.subscription_manager = self.manager
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/subscriptions':
            self.handle_get_subscriptions()
        elif parsed_path.path == '/api/history':
            self.handle_get_history()
        elif parsed_path.path == '/api/statistics':
            self.handle_get_statistics()
        elif parsed_path.path == '/api/status':
            self.handle_status_request()
        elif parsed_path.path == '/api/search':
            query_params = parse_qs(parsed_path.query)
            query = query_params.get('q', [''])[0]
            self.handle_search_stocks(query)
        else:
            self.send_error(404, "API endpoint not found")
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/subscribe':
            self.handle_add_subscription()
        elif parsed_path.path == '/api/unsubscribe':
            self.handle_remove_subscription()
        elif parsed_path.path == '/api/push/manual':
            self.handle_manual_push()
        elif parsed_path.path == '/api/push/test':
            self.handle_test_push()
        elif parsed_path.path == '/api/toggle':
            self.handle_toggle_subscription()
        else:
            self.send_error(404, "API endpoint not found")
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def get_request_body(self):
        """获取请求体数据"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            body = self.rfile.read(content_length)
            return json.loads(body.decode('utf-8'))
        return {}
    
    def handle_status_request(self):
        """处理状态请求"""
        try:
            stats = self.manager.get_statistics()
            
            status = {
                "server_time": datetime.now().isoformat(),
                "server_status": "running",
                "api_version": "1.0",
                "service": "subscription_push",
                "statistics": stats
            }
            
            self.send_json_response(status)
            
        except Exception as e:
            self.send_json_response({
                "error": str(e),
                "server_status": "error"
            }, status_code=500)
    
    def handle_get_subscriptions(self):
        """获取订阅列表"""
        try:
            subscriptions = self.manager.get_subscriptions()
            
            response_data = {
                "success": True,
                "subscriptions": subscriptions,
                "total": len(subscriptions),
                "timestamp": datetime.now().isoformat()
            }
            
            self.send_json_response(response_data)
            
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status_code=500)
    
    def handle_add_subscription(self):
        """添加股票订阅"""
        try:
            data = self.get_request_body()
            symbol = data.get('symbol', '').upper()
            name = data.get('name', '')
            
            if not symbol:
                self.send_json_response({
                    "success": False,
                    "error": "股票代码不能为空"
                }, status_code=400)
                return
            
            success = self.manager.add_subscription(symbol, name)
            
            if success:
                self.send_json_response({
                    "success": True,
                    "message": f"成功添加订阅: {symbol}",
                    "symbol": symbol
                })
            else:
                self.send_json_response({
                    "success": False,
                    "error": "添加订阅失败，可能已存在"
                }, status_code=409)
                
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status_code=500)
    
    def handle_remove_subscription(self):
        """移除股票订阅"""
        try:
            data = self.get_request_body()
            symbol = data.get('symbol', '').upper()
            
            if not symbol:
                self.send_json_response({
                    "success": False,
                    "error": "股票代码不能为空"
                }, status_code=400)
                return
            
            success = self.manager.remove_subscription(symbol)
            
            if success:
                self.send_json_response({
                    "success": True,
                    "message": f"成功移除订阅: {symbol}"
                })
            else:
                self.send_json_response({
                    "success": False,
                    "error": "移除订阅失败，未找到该股票"
                }, status_code=404)
                
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status_code=500)
    
    def handle_toggle_subscription(self):
        """切换订阅状态"""
        try:
            data = self.get_request_body()
            symbol = data.get('symbol', '').upper()
            
            success = self.manager.toggle_subscription(symbol)
            
            if success:
                self.send_json_response({
                    "success": True,
                    "message": f"成功切换订阅状态: {symbol}"
                })
            else:
                self.send_json_response({
                    "success": False,
                    "error": "切换状态失败，未找到该股票"
                }, status_code=404)
                
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status_code=500)
    
    def handle_search_stocks(self, query):
        """搜索股票"""
        try:
            # 模拟股票搜索 - 实际应该从数据库或API获取
            all_stocks = [
                {"symbol": "000001", "name": "平安银行"},
                {"symbol": "000002", "name": "万科A"},
                {"symbol": "000063", "name": "中兴通讯"},
                {"symbol": "000100", "name": "TCL科技"},
                {"symbol": "000858", "name": "五粮液"},
                {"symbol": "000895", "name": "双汇发展"},
                {"symbol": "600519", "name": "贵州茅台"},
                {"symbol": "300750", "name": "宁德时代"},
                {"symbol": "002594", "name": "比亚迪"},
                {"symbol": "600036", "name": "招商银行"},
                {"symbol": "601318", "name": "中国平安"},
                {"symbol": "002415", "name": "海康威视"},
                {"symbol": "000568", "name": "泸州老窖"},
                {"symbol": "300059", "name": "东方财富"},
                {"symbol": "002230", "name": "科大讯飞"},
            ]
            
            if query:
                filtered_stocks = [
                    stock for stock in all_stocks
                    if query.upper() in stock['symbol'] or query in stock['name']
                ]
            else:
                filtered_stocks = all_stocks[:10]  # 返回前10个
            
            self.send_json_response({
                "success": True,
                "query": query,
                "results": filtered_stocks[:20],  # 最多返回20个结果
                "total": len(filtered_stocks)
            })
            
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status_code=500)
    
    def handle_get_history(self):
        """获取推送历史"""
        try:
            parsed_path = urlparse(self.path)
            query_params = parse_qs(parsed_path.query)
            days = int(query_params.get('days', [7])[0])
            
            history = self.manager.get_push_history(days)
            
            self.send_json_response({
                "success": True,
                "history": history,
                "total": len(history),
                "days": days,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status_code=500)
    
    def handle_get_statistics(self):
        """获取统计信息"""
        try:
            stats = self.manager.get_statistics()
            
            self.send_json_response({
                "success": True,
                "statistics": stats,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status_code=500)
    
    def handle_manual_push(self):
        """手动推送"""
        try:
            # 在后台线程中执行推送
            def run_push():
                result = self.manager.daily_analysis_and_push()
                setattr(self.server, 'last_push_result', result)
            
            push_thread = threading.Thread(target=run_push, daemon=True)
            push_thread.start()
            
            self.send_json_response({
                "success": True,
                "message": "手动推送已启动，正在后台执行...",
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status_code=500)
    
    def handle_test_push(self):
        """测试推送"""
        try:
            subscriptions = self.manager.get_subscriptions()
            
            if not subscriptions:
                self.send_json_response({
                    "success": False,
                    "error": "没有订阅股票，无法测试推送"
                }, status_code=400)
                return
            
            # 选择第一只股票进行测试
            test_stock = subscriptions[0]
            analysis = self.manager.analyze_subscription(test_stock['symbol'])
            
            if analysis:
                # 标记为测试推送
                analysis['push_type'] = 'test'
                analysis['title'] = f"🧪 [测试] {analysis['title']}"
                
                success = self.manager.send_push_notification(analysis)
                
                self.send_json_response({
                    "success": True,
                    "message": "测试推送已发送",
                    "test_data": analysis,
                    "push_success": success
                })
            else:
                self.send_json_response({
                    "success": False,
                    "error": "无法获取测试股票数据"
                }, status_code=500)
                
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            }, status_code=500)

class SubscriptionPushServer:
    """订阅推送服务器"""
    
    def __init__(self, host='localhost', port=8527):
        self.host = host
        self.port = port
        self.server = None
        self.subscription_manager = StockSubscriptionManager()
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """启动服务器"""
        try:
            self.server = HTTPServer((self.host, self.port), SubscriptionAPIHandler)
            self.server.subscription_manager = self.subscription_manager
            
            self.logger.info(f"🚀 股票订阅推送服务器启动")
            self.logger.info(f"🌐 监听地址: http://{self.host}:{self.port}")
            self.logger.info(f"📊 当前订阅数量: {len(self.subscription_manager.get_subscriptions())}")
            
            print(f"📱 股票订阅推送服务器已启动")
            print(f"🔗 访问地址: http://{self.host}:{self.port}")
            print(f"📖 API文档:")
            print(f"  GET  /api/subscriptions - 获取订阅列表")
            print(f"  POST /api/subscribe - 添加订阅")
            print(f"  POST /api/unsubscribe - 移除订阅")
            print(f"  GET  /api/search?q=<query> - 搜索股票")
            print(f"  GET  /api/history - 获取推送历史")
            print(f"  POST /api/push/test - 测试推送")
            print(f"  POST /api/push/manual - 手动推送")
            print(f"")
            print(f"按 Ctrl+C 停止服务器")
            
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            self.logger.info("👋 收到停止信号")
            self.stop()
        except OSError as e:
            if e.errno == 48:  # Address already in use
                self.logger.error(f"❌ 端口 {self.port} 已被占用，请检查是否有其他服务在运行")
                print(f"❌ 端口 {self.port} 已被占用")
                print(f"💡 请尝试停止其他服务或使用不同端口")
            else:
                self.logger.error(f"❌ 服务器启动失败: {e}")
                print(f"❌ 服务器启动失败: {e}")
        except Exception as e:
            self.logger.error(f"❌ 服务器异常: {e}")
            print(f"❌ 服务器异常: {e}")
    
    def stop(self):
        """停止服务器"""
        if self.server:
            self.logger.info("🛑 正在停止服务器...")
            self.server.shutdown()
            self.server.server_close()
            print("✅ 服务器已停止")

if __name__ == "__main__":
    server = SubscriptionPushServer()
    server.start()