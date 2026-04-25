@echo off
echo 启动QtServer MQTT服务器...

REM 检查Node.js是否安装
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Node.js，请先安装Node.js
    pause
    exit /b 1
)

REM 检查是否已安装依赖
if not exist "node_modules" (
    echo 安装依赖包...
    npm install
) else (
    echo 依赖包已存在，跳过安装
)

REM 启动MQTT服务器
echo 启动MQTT服务器...
node mqtt-server.js

pause