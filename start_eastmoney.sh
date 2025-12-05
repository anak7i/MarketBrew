#!/bin/bash

echo "========================================"
echo "MarketBrew - 东方财富API版本"
echo "========================================"
echo ""

echo "[1/3] 测试东方财富API..."
python3 test_eastmoney.py
if [ $? -ne 0 ]; then
    echo ""
    echo "测试失败，请检查网络连接和依赖安装"
    exit 1
fi

echo ""
echo "[2/3] 启动价格服务..."
python3 price_service.py &
SERVICE_PID=$!

echo ""
echo "[3/3] 等待服务启动..."
sleep 3

echo ""
echo "========================================"
echo "✅ MarketBrew 已启动！"
echo "========================================"
echo ""
echo "📊 价格服务: http://localhost:5000"
echo "🌐 前端页面: stock_subscription.html"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

# 等待用户中断
trap "kill $SERVICE_PID; echo ''; echo '服务已停止'; exit" INT
wait $SERVICE_PID
