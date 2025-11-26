#!/bin/bash

echo "==================================="
echo "🚀 DeepSeek A股交易系统启动脚本"
echo "==================================="

# 检查.env文件
if [ ! -f .env ]; then
    echo "❌ 未找到.env文件，请先配置API密钥"
    echo "📝 请复制.env.example为.env并填入你的DeepSeek API密钥"
    echo "cp .env.example .env"
    exit 1
fi

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
MCP_PID=$!
cd ..

echo "⏳ 等待服务启动..."
sleep 5

echo "🤖 正在启动DeepSeek A股交易（2025年数据）..."
python main.py configs/deepseek_2025_config.json

echo "✅ DeepSeek A股交易系统启动完成！"

# 清理后台进程
echo "🧹 清理后台服务..."
kill $MCP_PID 2>/dev/null || true