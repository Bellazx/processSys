@echo off
echo 启动图书馆审批系统后端服务...
echo.

REM 检查虚拟环境
if not exist "venv\Scripts\activate.bat" (
    echo 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo 检查依赖...
pip install -r requirements.txt

REM 运行应用
echo.
echo 启动Flask应用...
python app.py

