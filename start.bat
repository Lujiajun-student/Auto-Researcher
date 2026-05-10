@echo off
chcp 65001 >nul
cls

echo =====================================
echo   AutoResearcher 开发环境启动脚本
echo =====================================
echo.

:: 检查 AI Agent 系统端口是否被占用
netstat -ano | findstr :8000 >nul 2>&1
if %errorlevel% equ 0 (
    echo [√] AI Agent 系统已在运行 (端口 8000)
) else (
    echo [!] 启动 AI Agent 系统...
    start "AutoResearcher AI Agents" cmd /k "cd /d %~dp0ai-agents && python app.py"
    timeout /t 3 /nobreak >nul
)

:: 检查后端端口是否被占用
netstat -ano | findstr :8080 >nul 2>&1
if %errorlevel% equ 0 (
    echo [√] 后端服务已在运行 (端口 8080)
) else (
    echo [!] 启动后端服务...
    start "AutoResearcher Backend" cmd /k "cd /d %~dp0backend && go run main.go"
    timeout /t 3 /nobreak >nul
)

:: 检查前端端口是否被占用
netstat -ano | findstr :3000 >nul 2>&1
if %errorlevel% equ 0 (
    echo [√] 前端服务已在运行 (端口 3000)
) else (
    echo [!] 启动前端服务...
    start "AutoResearcher Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
    timeout /t 5 /nobreak >nul
)

echo.
echo =====================================
echo   服务已启动！
echo =====================================
echo.
echo AI Agent 系统：http://localhost:8000
echo 后端地址：http://localhost:8080
echo 前端地址：http://localhost:3000
echo.
echo 提示:
echo   - 前端开发服务器支持热更新
echo   - 关闭此窗口不会停止服务
echo   - 在各自命令行窗口按 Ctrl+C 停止服务
echo   - 查看进程：tasklist ^| findstr "vite go python"
echo.
echo 按任意键退出...
pause >nul
