@echo off
chcp 65001 > nul
title 修复并重启决策API服务
color 0A

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║        决策API服务 - 自动修复和重启工具               ║
echo ╚════════════════════════════════════════════════════════╝
echo.

cd /d C:\Users\86158\marketbrew

echo [步骤 1/5] 停止所有旧的Python服务进程...
echo.
taskkill /F /IM python.exe /FI "WINDOWTITLE eq 决策API服务器*" 2>nul
timeout /t 2 /nobreak > nul
echo ✅ 已清理旧进程
echo.

echo [步骤 2/5] 检查Python环境和依赖...
echo.
python --version || (
    echo ❌ Python未安装或未添加到PATH！
    echo 请先安装Python 3.7+
    pause
    exit /b 1
)

python -c "import flask, flask_cors, requests" 2>nul || (
    echo ⚠️  检测到缺少依赖包，正在安装...
    pip install flask flask-cors requests -i https://pypi.tuna.tsinghua.edu.cn/simple
)
echo ✅ 依赖环境正常
echo.

echo [步骤 3/5] 启动决策API服务器...
echo.
echo 服务将在新窗口启动，请保持该窗口打开
start "决策API服务器" /MIN cmd /c "python decision_api_server.py"
timeout /t 3 /nobreak > nul
echo ✅ 服务已启动
echo.

echo [步骤 4/5] 等待服务初始化...
echo.
for /L %%i in (1,1,5) do (
    echo 正在等待... %%i/5
    timeout /t 1 /nobreak > nul
)
echo ✅ 初始化完成
echo.

echo [步骤 5/5] 测试API端点...
echo.

REM 创建临时PowerShell测试脚本
echo $ErrorActionPreference = 'SilentlyContinue' > test_temp.ps1
echo try { >> test_temp.ps1
echo     Write-Host "[测试 1/3] 市场统计 API..." -ForegroundColor Yellow >> test_temp.ps1
echo     $r1 = Invoke-RestMethod -Uri 'http://localhost:8526/api/market-stats' -TimeoutSec 5 >> test_temp.ps1
echo     if ($r1.success) { Write-Host "  ✅ 市场统计 API 正常" -ForegroundColor Green } >> test_temp.ps1
echo     else { Write-Host "  ❌ 市场统计 API 失败" -ForegroundColor Red } >> test_temp.ps1
echo     Write-Host "" >> test_temp.ps1
echo. >> test_temp.ps1
echo     Write-Host "[测试 2/3] 资金流向 API..." -ForegroundColor Yellow >> test_temp.ps1
echo     $r2 = Invoke-RestMethod -Uri 'http://localhost:8526/api/capital-timing' -TimeoutSec 5 >> test_temp.ps1
echo     if ($r2.success) { Write-Host "  ✅ 资金流向 API 正常" -ForegroundColor Green } >> test_temp.ps1
echo     else { Write-Host "  ❌ 资金流向 API 失败: $($r2.error)" -ForegroundColor Red } >> test_temp.ps1
echo     Write-Host "" >> test_temp.ps1
echo. >> test_temp.ps1
echo     Write-Host "[测试 3/3] 服务诊断端点..." -ForegroundColor Yellow >> test_temp.ps1
echo     $r3 = Invoke-RestMethod -Uri 'http://localhost:8526/api/test-capital' -TimeoutSec 5 >> test_temp.ps1
echo     if ($r3.success) { >> test_temp.ps1
echo         Write-Host "  ✅ 服务诊断正常" -ForegroundColor Green >> test_temp.ps1
echo         Write-Host "  服务实例: $($r3.test_result.service_exists)" -ForegroundColor Cyan >> test_temp.ps1
echo         Write-Host "  数据条数: $($r3.test_result.north_data_count)" -ForegroundColor Cyan >> test_temp.ps1
echo     } else { Write-Host "  ❌ 服务诊断失败" -ForegroundColor Red } >> test_temp.ps1
echo. >> test_temp.ps1
echo } catch { >> test_temp.ps1
echo     Write-Host "❌ 连接服务器失败: $_" -ForegroundColor Red >> test_temp.ps1
echo     Write-Host "" >> test_temp.ps1
echo     Write-Host "可能原因:" -ForegroundColor Yellow >> test_temp.ps1
echo     Write-Host "  1. 服务未启动成功，请查看'决策API服务器'窗口" -ForegroundColor Yellow >> test_temp.ps1
echo     Write-Host "  2. 端口8526被占用" -ForegroundColor Yellow >> test_temp.ps1
echo     Write-Host "  3. 防火墙拦截" -ForegroundColor Yellow >> test_temp.ps1
echo } >> test_temp.ps1

powershell -ExecutionPolicy Bypass -File test_temp.ps1
del test_temp.ps1

echo.
echo ════════════════════════════════════════════════════════
echo.
echo 🎯 接下来的步骤:
echo.
echo 1️⃣  如果所有测试都通过 (✅):
echo    - 打开浏览器访问: ai_decision_center.html
echo    - 按 F12 查看控制台，应该看到数据加载成功
echo.
echo 2️⃣  如果测试失败 (❌):
echo    - 查看任务栏中"决策API服务器"窗口的错误信息
echo    - 检查是否有Python错误或导入失败
echo.
echo 3️⃣  打开测试页面验证:
echo    - 双击 api_test.html 进行可视化测试
echo.
echo ════════════════════════════════════════════════════════
echo.

choice /C YN /M "是否现在打开AI决策中心页面"
if errorlevel 2 goto :END
if errorlevel 1 (
    start ai_decision_center.html
    start api_test.html
)

:END
echo.
echo 服务已在后台运行，窗口可以关闭
pause
