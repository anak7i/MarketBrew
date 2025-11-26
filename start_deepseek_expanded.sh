#!/bin/bash

echo "==================================="
echo "🚀 DeepSeek A股扩展交易系统启动"
echo "📊 股票池: 450只 (沪深300+创业板+科创板)"
echo "==================================="

# 检查.env文件
if [ ! -f .env ]; then
    echo "❌ 未找到.env文件，请先配置API密钥"
    echo "📝 请复制.env.example为.env并填入你的DeepSeek API密钥"
    echo "cp .env.example .env"
    exit 1
fi

echo "📦 正在安装依赖..."
pip3 install -r requirements.txt

echo "📊 正在获取A股扩展数据（450只股票）..."
cd data
python3 get_daily_price.py
echo "📊 正在合并数据..."
python3 merge_jsonl.py
cd ..

echo "🛠️ 正在启动MCP服务..."
cd agent_tools
python3 start_mcp_services.py &
MCP_PID=$!
cd ..

echo "⏳ 等待服务启动..."
sleep 5

echo "🤖 正在启动DeepSeek扩展A股交易（450只股票）..."
echo "📈 包含: 沪深300核心股(200只) + 创业板成长股(150只) + 科创板科技股(100只)"
python3 main.py configs/deepseek_expanded_config.json

echo "✅ DeepSeek扩展A股交易系统启动完成！"

# 清理后台进程
echo "🧹 清理后台服务..."
kill $MCP_PID 2>/dev/null || true