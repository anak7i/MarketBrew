@echo off
chcp 65001 >nul
echo ========================================
echo 🌡️ MarketBrew 市场温度计
echo ========================================
echo.

echo [1/3] 启动增强版价格服务...
start "MarketBrew Enhanced Service" python price_service_enhanced.py

echo.
echo [2/3] 等待服务启动...
timeout /t 5 /nobreak > nul

echo.
echo [3/3] 打开市场温度计...
start market_temperature.html

echo.
echo ========================================
echo ✅ 市场温度计已启动！
echo ========================================
echo.
echo 🌡️ 市场温度计: market_temperature.html
echo 📊 服务地址: http://localhost:5000
echo 🔍 API文档: http://localhost:5000
echo.
echo 提示: 关闭服务窗口将停止后端服务
echo.
pause
