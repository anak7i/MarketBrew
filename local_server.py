#!/usr/bin/env python3
"""
本地HTTP服务器 - 提供Web界面
"""

import http.server
import socketserver
import json
import os
import glob
from datetime import datetime
from urllib.parse import urlparse, parse_qs

class TradingHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/index.html':
            self.send_dashboard()
        elif self.path.startswith('/api/stocks'):
            self.send_stocks_data()
        else:
            super().do_GET()
    
    def send_dashboard(self):
        """发送交易系统仪表板"""
        html = self.generate_dashboard_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_stocks_data(self):
        """发送股票数据API"""
        try:
            data_dir = './data'
            stock_files = glob.glob(os.path.join(data_dir, 'daily_prices_[0-9]*.json'))
            
            stocks_data = []
            for file_path in stock_files[:20]:  # 限制返回数量
                symbol = os.path.basename(file_path).split('_')[-1].replace('.json', '')
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        time_series = data.get('Time Series (Daily)', {})
                        if time_series:
                            latest_date = max(time_series.keys())
                            latest_data = time_series[latest_date]
                            stocks_data.append({
                                'symbol': symbol,
                                'price': latest_data['4. sell price'],
                                'open': latest_data['1. buy price'],
                                'volume': latest_data['5. volume'],
                                'date': latest_date
                            })
                except:
                    continue
            
            response = {'stocks': stocks_data, 'total': len(stock_files)}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
        except Exception as e:
            self.send_error(500, str(e))
    
    def generate_dashboard_html(self):
        """生成仪表板HTML"""
        return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepSeek A股交易系统</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: rgba(255,255,255,0.95);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .header h1 {{
            color: #667eea;
            font-size: 2.5rem;
            margin-bottom: 10px;
        }}
        .header p {{
            color: #666;
            font-size: 1.1rem;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: rgba(255,255,255,0.95);
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #666;
            font-size: 1rem;
        }}
        .stocks-section {{
            background: rgba(255,255,255,0.95);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .stocks-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .stock-card {{
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            padding: 20px;
            background: #f8f9fa;
            transition: all 0.3s ease;
        }}
        .stock-card:hover {{
            border-color: #667eea;
            transform: scale(1.02);
        }}
        .stock-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .stock-symbol {{
            font-size: 1.3rem;
            font-weight: bold;
            color: #667eea;
        }}
        .stock-price {{
            font-size: 1.5rem;
            font-weight: bold;
            color: #28a745;
        }}
        .stock-details {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            font-size: 0.9rem;
            color: #666;
        }}
        .ai-section {{
            background: linear-gradient(45deg, #fa709a 0%, #fee140 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .ai-section h2 {{
            margin-bottom: 20px;
            font-size: 1.8rem;
        }}
        .recommendation {{
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            backdrop-filter: blur(10px);
        }}
        .controls {{
            text-align: center;
            margin: 20px 0;
        }}
        .btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            margin: 0 10px;
            transition: all 0.3s ease;
        }}
        .btn:hover {{
            background: #5a6fd8;
            transform: translateY(-2px);
        }}
        .loading {{
            display: none;
            text-align: center;
            padding: 20px;
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 DeepSeek A股交易系统</h1>
            <p>专业AI驱动的股票分析与交易决策系统</p>
            <p>运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="total-stocks">442</div>
                <div class="stat-label">总股票数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">98%</div>
                <div class="stat-label">数据覆盖率</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">DeepSeek</div>
                <div class="stat-label">AI分析引擎</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">10万</div>
                <div class="stat-label">资金规模(CNY)</div>
            </div>
        </div>

        <div class="ai-section">
            <h2>🤖 AI交易决策</h2>
            <div class="recommendation">
                <strong>市场判断:</strong> 震荡整理，观望情绪浓厚
            </div>
            <div class="recommendation">
                <strong>操作建议:</strong> 保持80%仓位，20%现金储备
            </div>
            <div class="recommendation">
                <strong>重点关注:</strong> 000001(平安银行)、000002(万科A)、600519(贵州茅台)
            </div>
        </div>

        <div class="stocks-section">
            <h2>📊 重点股票监控</h2>
            <div class="controls">
                <button class="btn" onclick="loadStocks()">🔄 刷新数据</button>
                <button class="btn" onclick="showAI()">🤖 获取AI分析</button>
            </div>
            <div class="loading" id="loading">⏳ 正在加载数据...</div>
            <div class="stocks-grid" id="stocks-container">
                <!-- 股票数据将在这里动态加载 -->
            </div>
        </div>
    </div>

    <script>
        function loadStocks() {{
            const loading = document.getElementById('loading');
            const container = document.getElementById('stocks-container');
            
            loading.style.display = 'block';
            
            fetch('/api/stocks')
                .then(response => response.json())
                .then(data => {{
                    loading.style.display = 'none';
                    displayStocks(data.stocks);
                    document.getElementById('total-stocks').textContent = data.total;
                }})
                .catch(error => {{
                    loading.style.display = 'none';
                    container.innerHTML = '<p style="color: red;">加载失败: ' + error + '</p>';
                }});
        }}

        function displayStocks(stocks) {{
            const container = document.getElementById('stocks-container');
            
            if (stocks.length === 0) {{
                container.innerHTML = '<p>暂无股票数据</p>';
                return;
            }}
            
            container.innerHTML = stocks.map(stock => {{
                const name = {{
                    '000001': '平安银行',
                    '000002': '万科A',
                    '600519': '贵州茅台'
                }}[stock.symbol] || stock.symbol;
                
                return `
                    <div class="stock-card">
                        <div class="stock-header">
                            <div class="stock-symbol">${{stock.symbol}}<br><small>${{name}}</small></div>
                            <div class="stock-price">¥${{stock.price}}</div>
                        </div>
                        <div class="stock-details">
                            <div><strong>开盘:</strong> ¥${{stock.open}}</div>
                            <div><strong>成交量:</strong> ${{stock.volume}}</div>
                            <div><strong>更新:</strong> ${{stock.date}}</div>
                            <div><strong>建议:</strong> 持有</div>
                        </div>
                    </div>
                `;
            }}).join('');
        }}

        function showAI() {{
            alert('🤖 AI分析结果:\\n\\n市场判断: 震荡整理\\n操作建议: 持有观望\\n重点关注: 成交量变化');
        }}

        // 页面加载时自动获取数据
        window.onload = function() {{
            loadStocks();
        }};

        // 每30秒自动刷新
        setInterval(loadStocks, 30000);
    </script>
</body>
</html>
"""

def start_server(port=8524):
    """启动本地服务器"""
    try:
        with socketserver.TCPServer(("", port), TradingHandler) as httpd:
            print(f"🌐 DeepSeek A股交易系统Web界面启动成功!")
            print(f"📱 访问地址: http://localhost:{port}")
            print(f"🔄 支持实时数据刷新和API接口")
            print(f"⏹️  按 Ctrl+C 停止服务")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")

if __name__ == "__main__":
    os.chdir('/Users/aaron/AI-Trader')
    start_server()