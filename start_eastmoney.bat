@echo off
echo ========================================
echo MarketBrew - 东方财富API版本
echo ========================================
echo.

echo [1/3] 测试东方财富API...
python test_eastmoney.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo 测试失败，请检查网络连接和依赖安装
    pause
    exit /b 1
)

echo.
echo [2/3] 启动价格服务...
start "MarketBrew Price Service" python price_service.py

echo.
echo [3/3] 等待服务启动...
timeout /t 3 /nobreak > nul

echo.
echo ========================================
echo ✅ MarketBrew 已启动！
echo ========================================
echo.
echo 📊 价格服务: http://localhost:5000
echo 🌐 前端页面: stock_subscription.html
echo.
echo 按任意键打开前端页面...
pause > nul

start stock_subscription.html

echo.
echo 提示: 关闭此窗口将停止价格服务
pause
