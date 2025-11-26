#!/bin/bash

echo "🎯 启动MarketBrew进场信号分析服务..."
echo "========================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装，请先安装Python3"
    exit 1
fi

# 检查依赖服务
echo "📋 检查依赖服务..."

# 检查市场指数服务 (5008)
if ! curl -s http://localhost:5008/health > /dev/null; then
    echo "⚠️ 市场指数服务(5008)未运行，启动中..."
    nohup python3 market_index_service.py > market_index.log 2>&1 &
    sleep 3
fi

# 检查价格服务 (5002)
if ! curl -s http://localhost:5002/health > /dev/null; then
    echo "⚠️ 价格服务(5002)未运行，启动中..."
    nohup python3 price_service.py > price.log 2>&1 &
    sleep 3
fi

echo "✅ 依赖服务检查完成"

# 创建日志目录
mkdir -p logs

echo "🚀 启动进场信号分析服务..."
echo "📊 服务端口: 5009"
echo "🔗 访问地址: http://localhost:5009"
echo "📝 日志文件: entry_signal.log"
echo "========================================"

# 启动服务
python3 entry_signal_service.py