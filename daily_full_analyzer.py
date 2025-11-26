#!/usr/bin/env python3
"""
每日全股票AI分析系统
一天一次，分析全部442只股票
"""

import os
import json
import glob
import time
# import schedule  # 只在需要定时任务时导入
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
# from deepseek_trading import analyze_stock_with_ai, get_portfolio_suggestion

class DailyFullAnalyzer:
    def __init__(self):
        self.api_key = "sk-2700d9ebbb4c4374a8f697ae759d06fb"
        self.data_dir = "./data"
        self.analysis_dir = "./daily_analysis"
        self.max_workers = 5  # 并发分析数量
        self.batch_size = 50  # 每批处理50只股票
        
        # 创建分析目录
        if not os.path.exists(self.analysis_dir):
            os.makedirs(self.analysis_dir)
    
    def get_all_stocks(self):
        """获取所有股票代码"""
        stock_files = glob.glob(os.path.join(self.data_dir, 'daily_prices_[0-9]*.json'))
        stocks = []
        
        for file_path in stock_files:
            filename = os.path.basename(file_path)
            symbol = filename.replace('daily_prices_', '').replace('.json', '')
            stocks.append(symbol)
        
        stocks.sort()
        print(f"📊 发现 {len(stocks)} 只股票待分析")
        return stocks
    
    def analyze_single_stock(self, symbol, batch_num, stock_num, total_stocks):
        """分析单只股票"""
        try:
            print(f"🔍 [{batch_num}] 分析 {symbol} ({stock_num}/{total_stocks})")
            
            # 读取股票数据
            data_file = os.path.join(self.data_dir, f'daily_prices_{symbol}.json')
            if not os.path.exists(data_file):
                return symbol, {'error': '数据文件不存在', 'timestamp': datetime.now().isoformat()}
            
            with open(data_file, 'r', encoding='utf-8') as f:
                stock_data = json.load(f)
            
            # 获取股票名称
            stock_names = {
                '000001': '平安银行', '000002': '万科A', '600519': '贵州茅台',
                '300750': '宁德时代', '600036': '招商银行', '000858': '五粮液',
                '002594': '比亚迪', '000568': '泸州老窖', '002415': '海康威视',
                '000895': '双汇发展', '300059': '东方财富', '601318': '中国平安',
                '002304': '洋河股份'
            }
            stock_name = stock_names.get(symbol, f'股票{symbol}')
            
            # 构建简化的分析提示词（减少token消耗）
            time_series = stock_data.get('Time Series (Daily)', {})
            if not time_series:
                return symbol, {'error': '无交易数据', 'timestamp': datetime.now().isoformat()}
            
            recent_dates = sorted(time_series.keys(), reverse=True)[:3]
            latest_data = time_series[recent_dates[0]]
            
            # 极简分析提示词
            prompt = f"""
股票{symbol}({stock_name})
价格:{latest_data.get('4. sell price')} 成交量:{latest_data.get('5. volume')}

给出交易建议，格式：
操作:[买入/卖出/持有]
理由:[一句话说明原因]
"""
            
            # 调用AI分析（带重试机制）
            analysis = None
            for attempt in range(3):
                try:
                    analysis = self.call_deepseek_with_retry(prompt)
                    break
                except Exception as e:
                    if attempt == 2:
                        analysis = f"分析失败: {str(e)}"
                    else:
                        time.sleep(2)  # 重试前等待2秒
            
            result = {
                'symbol': symbol,
                'name': stock_name,
                'analysis': analysis,
                'price': latest_data.get('4. sell price'),
                'volume': latest_data.get('5. volume'),
                'date': recent_dates[0],
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"✅ [{batch_num}] {symbol} 分析完成")
            return symbol, result
            
        except Exception as e:
            print(f"❌ [{batch_num}] {symbol} 分析失败: {e}")
            return symbol, {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def call_deepseek_with_retry(self, prompt):
        """带重试的DeepSeek API调用"""
        import requests
        
        url = "https://api.deepseek.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是专业的A股分析师，给出简洁明确的分析。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 100,  # 极简输出
            "temperature": 0.3
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    
    def analyze_batch(self, stocks_batch, batch_num, total_batches):
        """分析一批股票"""
        print(f"\n🚀 开始分析第{batch_num}/{total_batches}批 ({len(stocks_batch)}只股票)")
        print("=" * 60)
        
        results = {}
        total_stocks = len(stocks_batch)
        
        # 使用线程池并发分析
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_symbol = {
                executor.submit(self.analyze_single_stock, symbol, batch_num, i+1, total_stocks): symbol 
                for i, symbol in enumerate(stocks_batch)
            }
            
            # 收集结果
            for future in as_completed(future_to_symbol):
                symbol, result = future.result()
                results[symbol] = result
        
        print(f"📊 第{batch_num}批分析完成: {len(results)}只股票")
        return results
    
    def daily_analysis(self):
        """执行每日全量分析"""
        start_time = datetime.now()
        print(f"\n🌅 每日全股票分析开始 - {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # 获取所有股票
        all_stocks = self.get_all_stocks()
        total_stocks = len(all_stocks)
        
        if total_stocks == 0:
            print("❌ 未找到股票数据文件")
            return
        
        # 分批处理
        batches = [all_stocks[i:i + self.batch_size] for i in range(0, len(all_stocks), self.batch_size)]
        total_batches = len(batches)
        
        print(f"📋 分析计划: {total_stocks}只股票，分{total_batches}批处理，每批{self.batch_size}只")
        print(f"⚡ 并发设置: {self.max_workers}个线程同时分析")
        print()
        
        all_results = {}
        successful_count = 0
        failed_count = 0
        
        # 逐批分析
        for batch_num, batch in enumerate(batches, 1):
            try:
                batch_results = self.analyze_batch(batch, batch_num, total_batches)
                all_results.update(batch_results)
                
                # 统计成功失败数量
                for result in batch_results.values():
                    if 'error' in result:
                        failed_count += 1
                    else:
                        successful_count += 1
                
                # 批次间休息，避免API限流
                if batch_num < total_batches:
                    print(f"⏸️ 批次间休息30秒，避免API限流...")
                    time.sleep(30)
                    
            except Exception as e:
                print(f"❌ 第{batch_num}批分析异常: {e}")
                failed_count += len(batch)
        
        # 生成分析报告
        analysis_date = datetime.now().strftime('%Y%m%d')
        
        # 保存详细结果
        detailed_file = os.path.join(self.analysis_dir, f"full_analysis_{analysis_date}.json")
        with open(detailed_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        # 生成统计摘要
        summary = {
            'date': analysis_date,
            'timestamp': datetime.now().isoformat(),
            'total_stocks': total_stocks,
            'successful': successful_count,
            'failed': failed_count,
            'success_rate': f"{successful_count/total_stocks*100:.1f}%",
            'analysis_time': str(datetime.now() - start_time),
            'top_recommendations': self.generate_top_recommendations(all_results)
        }
        
        summary_file = os.path.join(self.analysis_dir, f"summary_{analysis_date}.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        # 生成HTML报告
        self.generate_html_report(all_results, summary)
        
        # 更新交易记录页面
        self.update_trading_log(all_results)
        
        # 生成每日AI交易日报
        self.generate_daily_report(all_results)
        
        # 输出完成信息
        end_time = datetime.now()
        duration = end_time - start_time
        
        print(f"\n🎉 每日全股票分析完成!")
        print("=" * 80)
        print(f"📊 分析统计:")
        print(f"  • 总股票数: {total_stocks}")
        print(f"  • 成功分析: {successful_count}")
        print(f"  • 分析失败: {failed_count}")
        print(f"  • 成功率: {successful_count/total_stocks*100:.1f}%")
        print(f"⏱️ 分析耗时: {duration}")
        print(f"📁 结果保存:")
        print(f"  • 详细结果: {detailed_file}")
        print(f"  • 分析摘要: {summary_file}")
        print(f"  • HTML报告: ./daily_analysis/daily_report_{analysis_date}.html")
        
        return all_results
    
    def generate_top_recommendations(self, results):
        """生成顶级推荐股票"""
        buy_recommendations = []
        
        for symbol, data in results.items():
            if 'error' in data:
                continue
                
            analysis = data.get('analysis', '').lower()
            if '买入' in analysis and ('低' in analysis or '中' in analysis):
                buy_recommendations.append({
                    'symbol': symbol,
                    'name': data.get('name', ''),
                    'price': data.get('price'),
                    'analysis': data.get('analysis')
                })
        
        # 返回前10只推荐股票
        return buy_recommendations[:10]
    
    def generate_html_report(self, results, summary):
        """生成HTML分析报告"""
        analysis_date = summary['date']
        
        # 分类统计
        buy_count = 0
        sell_count = 0
        hold_count = 0
        
        buy_stocks = []
        sell_stocks = []
        
        for symbol, data in results.items():
            if 'error' in data:
                continue
            
            analysis = data.get('analysis', '').lower()
            if '买入' in analysis:
                buy_count += 1
                buy_stocks.append(data)
            elif '卖出' in analysis:
                sell_count += 1
                sell_stocks.append(data)
            else:
                hold_count += 1
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>每日全股票AI分析报告 - {analysis_date}</title>
    <style>
        body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; }}
        .header {{ text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 3px solid #667eea; }}
        .header h1 {{ color: #667eea; font-size: 2.5rem; margin: 0; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
        .stat-card {{ background: linear-gradient(45deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-card h3 {{ margin: 0 0 10px 0; font-size: 2rem; }}
        .recommendations {{ margin-bottom: 30px; }}
        .stock-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }}
        .stock-card {{ border: 2px solid #e1e5e9; border-radius: 8px; padding: 15px; background: #f8f9fa; }}
        .stock-card.buy {{ border-color: #28a745; background: #d4edda; }}
        .stock-card.sell {{ border-color: #dc3545; background: #f8d7da; }}
        .stock-symbol {{ font-weight: bold; color: #667eea; font-size: 1.2rem; }}
        .stock-analysis {{ margin-top: 10px; font-size: 0.9rem; color: #555; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 每日全股票AI分析报告</h1>
            <p>分析日期: {analysis_date} | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <h3>{summary['total_stocks']}</h3>
                <p>总分析股票</p>
            </div>
            <div class="stat-card">
                <h3>{summary['successful']}</h3>
                <p>成功分析</p>
            </div>
            <div class="stat-card">
                <h3>{summary['success_rate']}</h3>
                <p>成功率</p>
            </div>
            <div class="stat-card">
                <h3>{buy_count}</h3>
                <p>买入推荐</p>
            </div>
            <div class="stat-card">
                <h3>{sell_count}</h3>
                <p>卖出建议</p>
            </div>
            <div class="stat-card">
                <h3>{hold_count}</h3>
                <p>持有观望</p>
            </div>
        </div>

        <div class="recommendations">
            <h2>📈 买入推荐股票</h2>
            <div class="stock-grid">
"""
        
        # 添加买入推荐股票
        for stock in buy_stocks[:20]:  # 只显示前20只
            html_content += f"""
                <div class="stock-card buy">
                    <div class="stock-symbol">{stock['symbol']} {stock.get('name', '')}</div>
                    <div>价格: ¥{stock.get('price', 'N/A')}</div>
                    <div class="stock-analysis">{stock.get('analysis', '')}</div>
                </div>
"""
        
        html_content += f"""
            </div>
        </div>

        <div class="recommendations">
            <h2>📉 卖出建议股票</h2>
            <div class="stock-grid">
"""
        
        # 添加卖出建议股票
        for stock in sell_stocks[:10]:  # 只显示前10只
            html_content += f"""
                <div class="stock-card sell">
                    <div class="stock-symbol">{stock['symbol']} {stock.get('name', '')}</div>
                    <div>价格: ¥{stock.get('price', 'N/A')}</div>
                    <div class="stock-analysis">{stock.get('analysis', '')}</div>
                </div>
"""
        
        html_content += """
            </div>
        </div>

        <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 2px solid #e1e5e9; color: #666;">
            <p>DeepSeek A股AI分析系统 | ⚠️ 投资有风险，决策需谨慎</p>
        </div>
    </div>
</body>
</html>"""
        
        # 保存HTML报告
        html_file = os.path.join(self.analysis_dir, f"daily_report_{analysis_date}.html")
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def update_trading_log(self, results):
        """更新交易记录页面"""
        from update_trading_log import update_trading_log_page
        
        try:
            update_trading_log_page(results)
            print("📊 交易记录页面已同步更新")
        except Exception as e:
            print(f"❌ 交易记录页面更新失败: {e}")
    
    def generate_daily_report(self, all_results):
        """生成每日AI交易日报"""
        try:
            print("📰 正在生成每日AI交易日报...")
            
            # 分析结果统计
            buy_signals = []
            sell_signals = []
            hold_signals = []
            
            for symbol, data in all_results.items():
                if 'error' in data or 'analysis' not in data:
                    continue
                
                analysis = data.get('analysis', '').lower()
                if '买入' in analysis:
                    buy_signals.append((symbol, data))
                elif '卖出' in analysis:
                    sell_signals.append((symbol, data))
                else:
                    hold_signals.append((symbol, data))
            
            # 生成市场总览
            total_analyzed = len([r for r in all_results.values() if 'error' not in r])
            market_overview = f"""
📊 今日市场分析总结

🔍 分析覆盖: {total_analyzed}只A股全面分析完成
📈 交易信号: 发现{len(buy_signals)}个买入信号，{len(sell_signals)}个卖出信号
🎯 市场状态: {"谨慎观望期，大部分股票处于震荡整理阶段" if len(buy_signals) + len(sell_signals) < 20 else "活跃交易期，多个投资机会涌现"}

💡 操作策略: 
- 严格控制仓位，重点关注有明确信号的股票
- 震荡市中保持耐心，等待趋势明确后再大举操作
- 关注成交量变化，量价配合的股票优先考虑

⚠️ 风险提示: 当前市场方向性不强，避免追涨杀跌，注重风险控制
"""
            
            # 创建日报目录
            reports_dir = "./daily_reports"
            if not os.path.exists(reports_dir):
                os.makedirs(reports_dir)
            
            # 生成HTML日报
            report_date = datetime.now().strftime('%Y-%m-%d')
            self.create_html_daily_report(report_date, market_overview, buy_signals, sell_signals, hold_signals, reports_dir)
            
            print(f"✅ 每日AI交易日报生成完成!")
            print(f"📄 日报位置: ./daily_reports/daily_report_{report_date}.html")
            
        except Exception as e:
            print(f"❌ 每日日报生成失败: {e}")
    
    def create_html_daily_report(self, report_date, market_overview, buy_signals, sell_signals, hold_signals, reports_dir):
        """创建HTML每日日报"""
        
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
            white-space: pre-line;
        }}
        .signals-section {{
            background: #f8f9fa;
            border-left: 5px solid #28a745;
        }}
        .signals-section h2 {{
            color: #28a745;
            margin-bottom: 20px;
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
        }}
        .signal-card.buy {{ border-left-color: #28a745; }}
        .signal-card.sell {{ border-left-color: #dc3545; }}
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
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
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
                    {market_overview}
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
            for symbol, data in buy_signals[:20]:  # 最多显示20个
                stock_names = {
                    '000001': '平安银行', '000002': '万科A', '600519': '贵州茅台',
                    '300750': '宁德时代', '600036': '招商银行', '000858': '五粮液'
                }
                stock_name = stock_names.get(symbol, f'股票{symbol}')
                
                html_content += f"""
                    <div class="signal-card buy">
                        <div class="signal-header">
                            <div class="stock-info">{symbol} {stock_name}</div>
                            <div class="action-badge buy">买入</div>
                        </div>
                        <div class="analysis-text">
                            <strong>价格:</strong> ¥{data.get('price', 'N/A')}<br>
                            <strong>分析:</strong> {data.get('analysis', '')}
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
            for symbol, data in sell_signals[:20]:  # 最多显示20个
                stock_names = {
                    '000001': '平安银行', '000002': '万科A', '600519': '贵州茅台',
                    '300750': '宁德时代', '600036': '招商银行', '000858': '五粮液'
                }
                stock_name = stock_names.get(symbol, f'股票{symbol}')
                
                html_content += f"""
                    <div class="signal-card sell">
                        <div class="signal-header">
                            <div class="stock-info">{symbol} {stock_name}</div>
                            <div class="action-badge sell">卖出</div>
                        </div>
                        <div class="analysis-text">
                            <strong>价格:</strong> ¥{data.get('price', 'N/A')}<br>
                            <strong>分析:</strong> {data.get('analysis', '')}
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
            <p>基于443只A股深度分析 | AI引擎: DeepSeek</p>
            <p>⚠️ 本报告仅供参考，投资有风险，决策需谨慎</p>
            <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>"""

        # 保存HTML文件
        report_file = os.path.join(reports_dir, f"daily_report_{report_date}.html")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 创建最新日报链接
        latest_file = os.path.join(reports_dir, "latest_report.html")
        with open(latest_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def setup_daily_schedule(self, analysis_time="08:00"):
        """设置每日分析计划"""
        import schedule
        print(f"⏰ 设置每日AI分析: 每天{analysis_time}执行")
        schedule.every().day.at(analysis_time).do(self.daily_analysis)
        
        print("🚀 每日分析调度器启动")
        print(f"📊 分析范围: 全部442只股票")
        print(f"⏰ 执行时间: 每天{analysis_time}")
        print(f"📁 结果保存: ./daily_analysis/")
        print(f"🛑 按Ctrl+C停止")
        print("=" * 60)
        
        while True:
            try:
                import schedule
                schedule.run_pending()
                time.sleep(60)
                
                # 显示下次执行时间
                next_run = schedule.next_run()
                if next_run:
                    print(f"⏳ 下次分析: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                
            except KeyboardInterrupt:
                print("\n👋 每日分析调度器已停止")
                break

def main():
    """主函数"""
    analyzer = DailyFullAnalyzer()
    
    print("🤖 DeepSeek每日全股票AI分析系统")
    print("=" * 50)
    print("请选择运行模式:")
    print("1. 立即执行全量分析")
    print("2. 设置每日定时分析(20:00) - 推荐")
    print("3. 设置每日定时分析(08:00)")
    print("4. 自定义分析时间")
    
    choice = input("\n请输入选择 (1-4): ").strip()
    
    if choice == "1":
        analyzer.daily_analysis()
    elif choice == "2":
        analyzer.setup_daily_schedule("20:00") 
    elif choice == "3":
        analyzer.setup_daily_schedule("08:00")
    elif choice == "4":
        analysis_time = input("请输入分析时间(HH:MM格式，如09:30): ").strip()
        analyzer.setup_daily_schedule(analysis_time)
    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()