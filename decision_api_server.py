#!/usr/bin/env python3
"""
决策API服务器 - 为AI决策中心提供数据接口
"""

import os
import json
import threading
import subprocess
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging
from batch_optimized_decision_engine import BatchOptimizedDecisionEngine

class DecisionAPIHandler(BaseHTTPRequestHandler):
    """决策API请求处理器"""
    
    def __init__(self, *args, **kwargs):
        self.engine = BatchOptimizedDecisionEngine()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/status':
            self.handle_status_request()
        elif parsed_path.path == '/api/decisions':
            self.handle_decisions_request()
        elif parsed_path.path == '/api/analysis-status':
            self.handle_analysis_status_request()
        else:
            self.send_error(404, "API endpoint not found")
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/trigger-analysis':
            self.handle_trigger_analysis()
        else:
            self.send_error(404, "API endpoint not found")
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_status_request(self):
        """处理系统状态请求"""
        try:
            status = self.engine.get_analysis_status()
            
            # 添加服务器状态信息
            status.update({
                "server_time": datetime.now().isoformat(),
                "server_status": "running",
                "api_version": "1.0",
                "analysis_running": getattr(self.server, 'analysis_running', False)
            })
            
            self.send_json_response(status)
            
        except Exception as e:
            self.send_json_response({
                "error": str(e),
                "server_status": "error"
            }, status_code=500)
    
    def handle_decisions_request(self):
        """处理决策数据请求"""
        try:
            latest_data = self.engine.get_latest_decisions()
            
            if latest_data:
                # 构建前端需要的数据结构
                response_data = {
                    "analysis_time": latest_data["analysis_time"],
                    "buy_stocks": latest_data["buy_stocks"],
                    "sell_stocks": latest_data["sell_stocks"],
                    "hold_stocks": latest_data["hold_stocks"],
                    "market_context": latest_data.get("market_context", "")
                }
                self.send_json_response(response_data)
            else:
                self.send_json_response({
                    "message": "暂无决策数据，请先执行分析",
                    "has_data": False
                })
                
        except Exception as e:
            self.send_json_response({
                "error": str(e),
                "has_data": False
            }, status_code=500)
    
    def handle_analysis_status_request(self):
        """处理分析状态请求"""
        try:
            analysis_running = getattr(self.server, 'analysis_running', False)
            last_result = getattr(self.server, 'last_analysis_result', None)
            completed_time = getattr(self.server, 'analysis_completed_time', None)
            
            status_data = {
                'analysis_running': analysis_running,
                'last_result': last_result,
                'completed_time': completed_time.isoformat() if completed_time else None,
                'server_time': datetime.now().isoformat()
            }
            
            self.send_json_response(status_data)
            
        except Exception as e:
            self.send_json_response({
                "error": str(e)
            }, status_code=500)
    
    def handle_trigger_analysis(self):
        """处理触发分析请求"""
        try:
            # 检查是否已有分析在运行
            if getattr(self.server, 'analysis_running', False):
                self.send_json_response({
                    'success': False,
                    'error': '已有分析任务在运行中',
                    'status': 'running'
                })
                return
            
            # 标记分析开始
            self.server.analysis_running = True
            self.server.last_analysis_result = None
            
            # 在后台线程中启动分析
            analysis_thread = threading.Thread(target=self.run_analysis_background)
            analysis_thread.daemon = True
            analysis_thread.start()
            
            self.send_json_response({
                'success': True,
                'message': '决策分析已启动',
                'estimated_time': '15-20分钟',
                'status': 'started'
            })
            
        except Exception as e:
            self.send_json_response({
                'success': False,
                'error': str(e),
                'status': 'error'
            }, status_code=500)
    
    def run_analysis_background(self):
        """在后台运行分析"""
        try:
            print(f"🚀 开始后台决策分析 - {datetime.now().strftime('%H:%M:%S')}")
            
            # 使用统一决策引擎执行分析
            result = self.engine.run_full_analysis()
            
            if result:
                print("✅ 后台决策分析完成")
                self.server.last_analysis_result = "success"
            else:
                print("❌ 后台决策分析失败")
                self.server.last_analysis_result = "failed"
                
        except Exception as e:
            print(f"❌ 后台分析异常: {e}")
            self.server.last_analysis_result = f"exception: {str(e)}"
        finally:
            self.server.analysis_running = False
            self.server.analysis_completed_time = datetime.now()
    
    def send_json_response(self, data, status_code=200):
        """发送JSON响应"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        json_data = json.dumps(data, ensure_ascii=False, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {format % args}")

class DecisionAPIServer:
    """决策API服务器"""
    
    def __init__(self, port=8526):
        self.port = port
        self.server = None
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def start(self):
        """启动服务器"""
        try:
            self.server = HTTPServer(('localhost', self.port), DecisionAPIHandler)
            
            # 初始化服务器状态
            self.server.analysis_running = False
            self.server.last_analysis_result = None
            self.server.analysis_completed_time = None
            
            print(f"🌐 决策API服务器启动成功!")
            print(f"📱 服务地址: http://localhost:{self.port}")
            print(f"🔗 API端点:")
            print(f"  • POST /api/trigger-analysis - 触发决策分析")
            print(f"  • GET  /api/status - 查询系统状态")
            print(f"  • GET  /api/decisions - 获取决策数据")
            print(f"  • GET  /api/analysis-status - 查询分析状态")
            print(f"⏹️  按 Ctrl+C 停止服务")
            print("=" * 50)
            
            # 启动服务器
            self.server.serve_forever()
            
        except KeyboardInterrupt:
            print("\\n👋 决策API服务器已停止")
        except Exception as e:
            self.logger.error(f"❌ 服务器启动失败: {e}")
        finally:
            if self.server:
                self.server.shutdown()

def main():
    """主函数"""
    import sys
    
    port = 8526
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("❌ 端口号必须是数字")
            return
    
    server = DecisionAPIServer(port)
    server.start()

if __name__ == "__main__":
    main()