#!/bin/bash

# MarketBrew 价格服务启动脚本

echo "🚀 启动 MarketBrew 价格服务..."
echo "📊 数据源：腾讯财经 API"
echo "🔗 服务地址：http://localhost:5000"
echo ""

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误：未找到 Python3，请先安装 Python3"
    exit 1
fi

# 检查并安装依赖
echo "📦 检查依赖..."
python3 -c "import flask, flask_cors, requests" 2>/dev/null || {
    echo "📦 安装依赖包..."
    pip3 install flask flask-cors requests
}

# 启动服务
echo "✅ 启动价格服务..."
python3 price_service.py