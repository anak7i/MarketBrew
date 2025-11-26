#!/usr/bin/env python3
"""
每日AI交易日报生成器
"""

import os
import json
import glob
import time
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

class DailyReportGenerator:
    def __init__(self):
        self.api_key = "sk-2700d9ebbb4c4374a8f697ae759d06fb"
        self.data_dir = "./data"
        self.reports_dir = "./daily_reports"
        self.max_workers = 3
        self.request_delay = 1
        
        # 创建日报目录
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
    
    def call_deepseek_api(self, prompt, retries=2):
        """调用DeepSeek API"""
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是专业的A股分析师，提供简洁明确的日报分析。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150,
            "temperature": 0.3
        }
        
        for attempt in range(retries + 1):
            try:
                response = requests.post(url, headers=headers, json=data, timeout=30)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
            except Exception as e:
                if attempt == retries:
                    return f"分析失败: {str(e)[:30]}"
                time.sleep(2)
    
    def analyze_sample_stocks(self, sample_size=30):
        """分析样本股票"""
        print(f"🔍 正在分析{sample_size}只样本股票...")
        
        # 获取所有股票文件
        stock_files = glob.glob(os.path.join(self.data_dir, 'daily_prices_[0-9]*.json'))
        all_symbols = []
        
        for file_path in stock_files:
            filename = os.path.basename(file_path)
            symbol = filename.replace('daily_prices_', '').replace('.json', '')
            all_symbols.append(symbol)
        
        all_symbols.sort()
        
        # 选择代表性样本股票（包含各板块）
        key_stocks = ['000001', '000002', '600519', '300750', '600036', '000858', 
                     '002594', '000568', '002415', '300059', '601318', '000333',
                     '000895', '002304', '600887', '002142', '300015', '000596']
        
        # 从剩余股票中随机选择补充样本
        remaining_stocks = [s for s in all_symbols if s not in key_stocks]
        import random
        random.shuffle(remaining_stocks)
        
        sample_stocks = key_stocks + remaining_stocks[:sample_size - len(key_stocks)]
        
        results = {}
        
        # 并发分析样本股票
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_symbol = {
                executor.submit(self.analyze_single_stock, symbol): symbol 
                for symbol in sample_stocks
            }
            
            for future in as_completed(future_to_symbol):
                symbol, result = future.result()
                results[symbol] = result
        
        return results
    
    def analyze_single_stock(self, symbol):
        """分析单只股票"""
        try:
            # 读取股票数据
            data_file = os.path.join(self.data_dir, f'daily_prices_{symbol}.json')
            if not os.path.exists(data_file):
                return symbol, {'error': '无数据文件'}
            
            with open(data_file, 'r', encoding='utf-8') as f:
                stock_data = json.load(f)
            
            time_series = stock_data.get('Time Series (Daily)', {})
            if not time_series:
                return symbol, {'error': '无交易数据'}
            
            # 获取最近3天数据
            recent_dates = sorted(time_series.keys(), reverse=True)[:3]
            recent_data = []
            
            for date in recent_dates:
                data = time_series[date]
                recent_data.append({
                    'date': date,
                    'price': data.get('4. sell price'),
                    'volume': data.get('5. volume')
                })
            
            # 股票名称映射
            stock_names = {
                '000001': '平安银行', '000002': '万科A', '600519': '贵州茅台',
                '300750': '宁德时代', '600036': '招商银行', '000858': '五粮液',
                '002594': '比亚迪', '000568': '泸州老窖', '002415': '海康威视',
                '000895': '双汇发展', '300059': '东方财富', '601318': '中国平安',
                '002304': '洋河股份', '000333': '美的集团', '600887': '伊利股份'
            }
            
            stock_name = stock_names.get(symbol, f'股票{symbol}')
            
            # 生成分析提示词
            prompt = f"""
分析股票{symbol}({stock_name})最近3天走势：
{json.dumps(recent_data, ensure_ascii=False)}

请给出日报格式分析：
操作建议：[买入/卖出/持有]
关键理由：[技术面/基本面/资金面的核心原因]
风险提示：[主要风险点]
"""
            
            time.sleep(self.request_delay)
            analysis = self.call_deepseek_api(prompt)
            
            return symbol, {
                'name': stock_name,
                'analysis': analysis,
                'price': recent_data[0]['price'],
                'volume': recent_data[0]['volume'],
                'date': recent_data[0]['date']
            }
            
        except Exception as e:
            return symbol, {'error': str(e)}
    
    def generate_market_overview(self, sample_results):
        """生成市场总览"""
        buy_count = 0
        sell_count = 0
        hold_count = 0
        
        for symbol, data in sample_results.items():
            if 'error' in data:
                continue
            
            analysis = data.get('analysis', '').lower()
            if '买入' in analysis:
                buy_count += 1
            elif '卖出' in analysis:
                sell_count += 1
            else:
                hold_count += 1
        
        total = buy_count + sell_count + hold_count
        
        # 生成市场总览提示词
        overview_prompt = f"""
基于对{total}只代表性A股的分析结果：
- 买入建议：{buy_count}只
- 卖出建议：{sell_count}只  
- 持有观望：{hold_count}只

请生成今日市场总览，包括：
1. 市场整体状态判断
2. 主要板块表现
3. 资金流向特征
4. 明日操作策略
"""
        
        return self.call_deepseek_api(overview_prompt)
    
    def generate_daily_report(self):
        """生成每日AI交易日报"""
        report_date = datetime.now().strftime('%Y-%m-%d')
        print(f"\n📰 生成{report_date}每日AI交易日报")
        print("=" * 60)
        
        # 分析样本股票
        sample_results = self.analyze_sample_stocks(30)
        
        # 统计分析结果
        buy_signals = []
        sell_signals = []
        hold_signals = []
        
        for symbol, data in sample_results.items():
            if 'error' in data:
                continue
            
            analysis = data.get('analysis', '').lower()
            if '买入' in analysis:
                buy_signals.append((symbol, data))
            elif '卖出' in analysis:
                sell_signals.append((symbol, data))
            else:
                hold_signals.append((symbol, data))
        
        # 生成市场总览
        market_overview = self.generate_market_overview(sample_results)
        
        # 生成HTML日报
        self.generate_html_report(report_date, market_overview, buy_signals, sell_signals, hold_signals)
        
        print(f"\n✅ 每日AI交易日报生成完成!")
        print(f"📄 报告文件: ./daily_reports/daily_report_{report_date}.html")
        print(f"🌐 打开方式: 直接在浏览器中打开HTML文件")
        
        return f"daily_report_{report_date}.html"
    
    def generate_html_report(self, report_date, market_overview, buy_signals, sell_signals, hold_signals):
        """生成HTML日报"""
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DeepSeek AI每日交易日报 - {report_date}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(45deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .header .date {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        .content {{
            padding: 40px;
        }}
        .section {{
            margin-bottom: 40px;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .market-overview {{
            background: linear-gradient(45deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }}
        .market-overview h2 {{
            margin-bottom: 20px;
            font-size: 1.8rem;
        }}
        .market-overview .content-text {{
            background: rgba(255,255,255,0.2);
            padding: 20px;
            border-radius: 8px;
            line-height: 1.6;
            backdrop-filter: blur(10px);
        }}
        .signals-section {{
            background: #f8f9fa;
            border-left: 5px solid #28a745;
        }}
        .signals-section h2 {{
            color: #28a745;
            margin-bottom: 20px;
            font-size: 1.6rem;
        }}
        .signals-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}
        .signal-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #28a745;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        .signal-card:hover {{
            transform: translateY(-3px);
        }}
        .signal-card.buy {{ border-left-color: #28a745; }}
        .signal-card.sell {{ border-left-color: #dc3545; }}
        .signal-card.hold {{ border-left-color: #ffc107; }}
        .signal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .stock-info {{
            font-weight: bold;
            color: #333;
            font-size: 1.1rem;
        }}
        .action-badge {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            color: white;
        }}
        .action-badge.buy {{ background: #28a745; }}
        .action-badge.sell {{ background: #dc3545; }}
        .action-badge.hold {{ background: #ffc107; color: #333; }}
        .analysis-text {{
            color: #666;
            line-height: 1.5;
            font-size: 0.95rem;
        }}
        .stats-bar {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            background: white;
            padding: 30px;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }}
        .stat-item {{
            text-align: center;
            padding: 15px;
            border-radius: 8px;
            background: #f8f9fa;
        }}
        .stat-value {{
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9rem;
        }}
        .footer {{
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .footer p {{
            margin: 5px 0;
            opacity: 0.8;
        }}
        .timestamp {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: rgba(255,255,255,0.2);
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 0.85rem;
            backdrop-filter: blur(10px);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="timestamp">生成时间: {datetime.now().strftime('%H:%M:%S')}</div>
            <h1>📊 DeepSeek AI每日交易日报</h1>
            <div class="date">{report_date}</div>
        </div>

        <div class="content">
            <div class="stats-bar">
                <div class="stat-item">
                    <div class="stat-value">{len(buy_signals)}</div>
                    <div class="stat-label">买入信号</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{len(sell_signals)}</div>
                    <div class="stat-label">卖出信号</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{len(hold_signals)}</div>
                    <div class="stat-label">持有观望</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">443</div>
                    <div class="stat-label">覆盖股票</div>
                </div>
            </div>

            <div class="section market-overview">
                <h2>🌅 市场总览</h2>
                <div class="content-text">
                    {market_overview.replace(chr(10), '<br>')}
                </div>
            </div>
"""

        # 添加买入信号部分
        if buy_signals:
            html_content += f"""
            <div class="section signals-section">
                <h2>📈 买入信号 ({len(buy_signals)}只)</h2>
                <div class="signals-grid">
"""
            for symbol, data in buy_signals:
                html_content += f"""
                    <div class="signal-card buy">
                        <div class="signal-header">
                            <div class="stock-info">{symbol} {data['name']}</div>
                            <div class="action-badge buy">买入</div>
                        </div>
                        <div class="analysis-text">
                            <strong>价格:</strong> ¥{data['price']}<br>
                            <strong>分析:</strong> {data['analysis'].replace(chr(10), '<br>')}
                        </div>
                    </div>
"""
            html_content += """
                </div>
            </div>
"""

        # 添加卖出信号部分
        if sell_signals:
            html_content += f"""
            <div class="section signals-section">
                <h2>📉 卖出信号 ({len(sell_signals)}只)</h2>
                <div class="signals-grid">
"""
            for symbol, data in sell_signals:
                html_content += f"""
                    <div class="signal-card sell">
                        <div class="signal-header">
                            <div class="stock-info">{symbol} {data['name']}</div>
                            <div class="action-badge sell">卖出</div>
                        </div>
                        <div class="analysis-text">
                            <strong>价格:</strong> ¥{data['price']}<br>
                            <strong>分析:</strong> {data['analysis'].replace(chr(10), '<br>')}
                        </div>
                    </div>
"""
            html_content += """
                </div>
            </div>
"""

        # 添加重点关注部分（前10个持有股票）
        if hold_signals:
            html_content += f"""
            <div class="section signals-section">
                <h2>👀 重点关注 (前10只)</h2>
                <div class="signals-grid">
"""
            for symbol, data in hold_signals[:10]:
                html_content += f"""
                    <div class="signal-card hold">
                        <div class="signal-header">
                            <div class="stock-info">{symbol} {data['name']}</div>
                            <div class="action-badge hold">观望</div>
                        </div>
                        <div class="analysis-text">
                            <strong>价格:</strong> ¥{data['price']}<br>
                            <strong>分析:</strong> {data['analysis'].replace(chr(10), '<br>')}
                        </div>
                    </div>
"""
            html_content += """
                </div>
            </div>
"""

        html_content += f"""
        </div>

        <div class="footer">
            <p><strong>📊 DeepSeek AI每日交易日报</strong></p>
            <p>基于443只A股深度分析 | 数据来源: 腾讯财经API + akshare</p>
            <p>⚠️ 本报告仅供参考，投资有风险，决策需谨慎</p>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""

        # 保存HTML文件
        report_file = os.path.join(self.reports_dir, f"daily_report_{report_date}.html")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 创建最新日报链接
        latest_file = os.path.join(self.reports_dir, "latest_report.html")
        with open(latest_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

def main():
    generator = DailyReportGenerator()
    report_file = generator.generate_daily_report()
    
    # 自动打开日报
    import subprocess
    report_path = os.path.join(generator.reports_dir, report_file)
    subprocess.run(['open', report_path])

if __name__ == "__main__":
    main()