@echo off
echo 启动图书馆审批系统前端服务...
echo.

REM 检查node_modules
if not exist "node_modules" (
    echo 安装依赖...
    call npm install
)

REM 运行开发服务器
echo.
echo 启动Vue开发服务器...
call npm run serve

