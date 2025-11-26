#!/bin/bash

echo "==================================="
echo "🚀 AI-Trader A股版本启动脚本"
echo "==================================="

echo "📦 正在安装依赖..."
pip install -r requirements.txt

echo "📊 正在获取A股数据..."
cd data
python get_daily_price.py
echo "📊 正在合并数据..."
python merge_jsonl.py
cd ..

echo "🛠️ 正在启动MCP服务..."
cd agent_tools
python start_mcp_services.py &
cd ..

echo "⏳ 等待服务启动..."
sleep 5

echo "🤖 正在启动AI交易竞技场..."
python main.py configs/a_stock_config.json

echo "✅ A股AI交易竞技场已启动！"