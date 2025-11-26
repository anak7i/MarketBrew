#!/usr/bin/env python3
"""
AI分析服务器 - 处理Web界面的分析请求
"""

import os
import json
import subprocess
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging

class AnalysisRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.analysis_status = "idle"  # idle, running, completed
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/status':
            self.send_status_response()
        elif parsed_path.path == '/api/logs':
            self.send_logs_response()
        else:
            self.send_error(404, "API endpoint not found")
    
    def do_POST(self):
        """处理POST请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/trigger-analysis':
            self.handle_analysis_request()
        else:
            self.send_error(404, "API endpoint not found")
    
    def do_OPTIONS(self):
        """处理OPTIONS请求 (CORS支持)"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def handle_analysis_request(self):
        """处理分析请求"""
        try:
            # 检查是否已有分析在运行
            if hasattr(self.server, 'analysis_running') and self.server.analysis_running:
                self.send_json_response({
                    'success': False,
                    'error': '已有分析任务在运行中',
                    'status': 'running'
                })
                return
            
            # 标记分析开始
            self.server.analysis_running = True
            
            # 在后台线程中启动分析
            analysis_thread = threading.Thread(target=self.run_analysis_background)
            analysis_thread.daemon = True
            analysis_thread.start()
            
            self.send_json_response({
                'success': True,
                'message': '全量分析已启动',
                'estimated_time': '15-20分钟',
                'status': 'started'
            })
            
        except Exception as e:
            self.send_json_response({
                'success': False,
                'error': str(e),
                'status': 'error'
            })
    
    def run_analysis_background(self):
        """在后台运行分析"""
        try:
            print(f"🚀 开始后台全量分析 - {datetime.now().strftime('%H:%M:%S')}")
            
            # 切换到项目目录
            os.chdir('/Users/aaron/AI-Trader')
            
            # 启动分析脚本
            result = subprocess.run([
                'python', 'run_full_analysis.py'
            ], 
            capture_output=True, 
            text=True,
            timeout=1800  # 30分钟超时
            )
            
            if result.returncode == 0:
                print("✅ 后台分析完成")
                self.server.last_analysis_result = "success"
            else:
                print(f"❌ 后台分析失败: {result.stderr}")
                self.server.last_analysis_result = f"error: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            print("⏰ 后台分析超时")
            self.server.last_analysis_result = "timeout"
        except Exception as e:
            print(f"❌ 后台分析异常: {e}")
            self.server.last_analysis_result = f"exception: {str(e)}"
        finally:
            self.server.analysis_running = False
            self.server.analysis_completed_time = datetime.now()
    
    def send_status_response(self):
        """发送状态响应"""
        status_data = {
            'analysis_running': getattr(self.server, 'analysis_running', False),
            'last_result': getattr(self.server, 'last_analysis_result', None),
            'completed_time': getattr(self.server, 'analysis_completed_time', None),
            'server_time': datetime.now().isoformat()
        }
        
        if hasattr(self.server, 'analysis_completed_time') and self.server.analysis_completed_time:
            status_data['completed_time'] = self.server.analysis_completed_time.isoformat()
        
        self.send_json_response(status_data)
    
    def send_logs_response(self):
        """发送日志响应"""
        try:
            # 读取最新的分析日志
            log_files = [
                'analysis_log.txt',
                'remaining_analysis_log.txt'
            ]
            
            latest_logs = []
            for log_file in log_files:
                if os.path.exists(log_file):
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        latest_logs.extend(lines[-10:])  # 最后10行
            
            self.send_json_response({
                'logs': latest_logs,
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            self.send_json_response({
                'error': str(e),
                'logs': []
            })
    
    def send_json_response(self, data):
        """发送JSON响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        """自定义日志格式"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] {format % args}")

class AnalysisServer:
    def __init__(self, port=8525):
        self.port = port
        self.server = None
        
    def start(self):
        """启动服务器"""
        self.server = HTTPServer(('localhost', self.port), AnalysisRequestHandler)
        self.server.analysis_running = False
        self.server.last_analysis_result = None
        self.server.analysis_completed_time = None
        
        print(f"🌐 AI分析服务器启动成功!")
        print(f"📱 服务地址: http://localhost:{self.port}")
        print(f"🔗 API端点:")
        print(f"  • POST /api/trigger-analysis - 触发全量分析")
        print(f"  • GET  /api/status - 查询分析状态")
        print(f"  • GET  /api/logs - 查看分析日志")
        print(f"⏹️  按 Ctrl+C 停止服务")
        print("=" * 50)
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 AI分析服务器已停止")
            self.server.shutdown()

def main():
    server = AnalysisServer()
    server.start()

if __name__ == "__main__":
    main()