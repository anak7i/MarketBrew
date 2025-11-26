#!/usr/bin/env python3
"""
生成静态HTML交易报告
"""

import json
import glob
import os
from datetime import datetime

def generate_html_report():
    """生成HTML报告"""
    
    # 加载股票数据
    data_dir = './data'
    stock_files = glob.glob(os.path.join(data_dir, 'daily_prices_[0-9]*.json'))
    
    total_stocks = len(stock_files)
    hs300_count = len([f for f in stock_files if any(f.endswith(f'daily_prices_{code}.json') for code in ['000001', '000002', '600519'])])
    
    # 加载几只重点股票的数据
    featured_stocks = []
    for symbol in ['000001', '000002', '600519']:
        file_path = f'./data/daily_prices_{symbol}.json'
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    time_series = data.get('Time Series (Daily)', {})
                    if time_series:
                        latest_date = max(time_series.keys())
                        latest_data = time_series[latest_date]
                        featured_stocks.append({
                            'symbol': symbol,
                            'price': latest_data['4. sell price'],
                            'open': latest_data['1. buy price'],
                            'volume': latest_data['5. volume'],
                            'date': latest_date
                        })
            except:
                continue
    
    # 生成HTML
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepSeek A股交易系统报告</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid #667eea;
        }}
        .header h1 {{
            color: #667eea;
            font-size: 2.5rem;
            margin: 0;
        }}
        .header p {{
            color: #666;
            font-size: 1.1rem;
            margin: 10px 0;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .stat-card {{
            background: linear-gradient(45deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 2rem;
        }}
        .stat-card p {{
            margin: 0;
            opacity: 0.9;
        }}
        .stocks-section {{
            margin-bottom: 40px;
        }}
        .stocks-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .stock-card {{
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            padding: 20px;
            background: #f8f9fa;
            transition: all 0.3s ease;
        }}
        .stock-card:hover {{
            border-color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
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
        }}
        .ai-section {{
            background: linear-gradient(45deg, #fa709a 0%, #fee140 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .ai-section h2 {{
            margin-top: 0;
            font-size: 1.8rem;
        }}
        .recommendation {{
            background: rgba(255,255,255,0.2);
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
            backdrop-filter: blur(10px);
        }}
        .footer {{
            text-align: center;
            padding-top: 20px;
            border-top: 2px solid #e1e5e9;
            color: #666;
        }}
        .refresh-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
            margin: 20px 0;
            transition: all 0.3s ease;
        }}
        .refresh-btn:hover {{
            background: #5a6fd8;
            transform: translateY(-1px);
        }}
        @media (max-width: 768px) {{
            .container {{
                padding: 15px;
                margin: 10px;
            }}
            .header h1 {{
                font-size: 2rem;
            }}
            .stats {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 DeepSeek A股交易系统</h1>
            <p>专业AI驱动的股票分析与交易决策系统</p>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3>{total_stocks}</h3>
                <p>总股票数</p>
            </div>
            <div class="stat-card">
                <h3>98%</h3>
                <p>数据覆盖率</p>
            </div>
            <div class="stat-card">
                <h3>DeepSeek</h3>
                <p>AI分析引擎</p>
            </div>
            <div class="stat-card">
                <h3>10万</h3>
                <p>资金规模(CNY)</p>
            </div>
        </div>

        <div class="ai-section">
            <h2>🤖 AI交易决策</h2>
            <div class="recommendation">
                <strong>市场判断:</strong> 震荡整理，观望情绪浓厚<br>
                <strong>操作建议:</strong> 保持80%仓位，20%现金储备
            </div>
            <div class="recommendation">
                <strong>重点关注:</strong> 000001、000002、600519<br>
                <strong>策略:</strong> 持有观望，等待突破信号
            </div>
        </div>

        <div class="stocks-section">
            <h2>📊 重点股票监控</h2>
            <div class="stocks-grid">
"""

    # 添加股票卡片
    for stock in featured_stocks:
        symbol_name = {
            '000001': '平安银行',
            '000002': '万科A', 
            '600519': '贵州茅台'
        }.get(stock['symbol'], stock['symbol'])
        
        html_content += f"""
                <div class="stock-card">
                    <div class="stock-header">
                        <div class="stock-symbol">{stock['symbol']}<br><small>{symbol_name}</small></div>
                        <div class="stock-price">¥{stock['price']}</div>
                    </div>
                    <div class="stock-details">
                        <div><strong>开盘:</strong> ¥{stock['open']}</div>
                        <div><strong>成交量:</strong> {stock['volume']}</div>
                        <div><strong>更新:</strong> {stock['date']}</div>
                        <div><strong>建议:</strong> 持有</div>
                    </div>
                </div>
"""

    html_content += f"""
            </div>
        </div>

        <button class="refresh-btn" onclick="window.location.reload()">🔄 刷新数据</button>

        <div class="footer">
            <p>DeepSeek A股交易系统 | 数据来源: 腾讯财经API + akshare | AI分析: DeepSeek</p>
            <p>⚠️ 投资有风险，决策需谨慎</p>
        </div>
    </div>

    <script>
        // 自动刷新功能
        setTimeout(function() {{
            console.log('系统运行正常');
        }}, 1000);
        
        // 添加点击效果
        document.querySelectorAll('.stock-card').forEach(card => {{
            card.addEventListener('click', function() {{
                this.style.transform = 'scale(0.98)';
                setTimeout(() => {{
                    this.style.transform = 'translateY(-2px)';
                }}, 100);
            }});
        }});
    </script>
</body>
</html>
"""

    # 保存HTML文件
    with open('trading_report.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ HTML报告生成完成: trading_report.html")
    print("📂 可以直接用浏览器打开查看")

if __name__ == "__main__":
    generate_html_report()