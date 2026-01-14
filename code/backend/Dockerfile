# 使用Python 3.11作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（包括ODBC驱动所需的依赖）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    unixodbc-dev \
    unixodbc \
    odbcinst \
    curl \
    gnupg \
    ca-certificates \
    apt-transport-https \
    libkrb5-3 \
    libgssapi-krb5-2 \
    tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 设置时区为上海（中国标准时间）
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 复制ODBC Driver 17安装包（如果存在）
# 优先使用本地文件，避免网络问题
COPY drivers/msodbcsql17.deb /tmp/msodbcsql17.deb

# 安装ODBC Driver 17
# 如果本地文件存在则使用本地文件，否则尝试从网络下载
RUN if [ -f /tmp/msodbcsql17.deb ]; then \
        echo "使用本地ODBC驱动包安装..." && \
        ACCEPT_EULA=Y DEBIAN_FRONTEND=noninteractive dpkg -i /tmp/msodbcsql17.deb || (apt-get update && apt-get install -f -y && ACCEPT_EULA=Y DEBIAN_FRONTEND=noninteractive dpkg -i /tmp/msodbcsql17.deb) && \
        apt-get clean && \
        rm -f /tmp/msodbcsql17.deb && \
        odbcinst -q -d; \
    else \
        echo "本地驱动包不存在，尝试从网络下载..." && \
        apt-get update && apt-get install -y curl gnupg ca-certificates apt-transport-https && \
        curl -fsSL --connect-timeout 30 --max-time 120 https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg && \
        echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main' > /etc/apt/sources.list.d/mssql-release.list && \
        apt-get update && \
        ACCEPT_EULA=Y DEBIAN_FRONTEND=noninteractive apt-get install -y msodbcsql17 && \
        apt-get clean && rm -rf /var/lib/apt/lists/* && \
        odbcinst -q -d; \
    fi

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p uploads logs flask_session

# 设置环境变量
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 8081

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8081/process/health').read()" || exit 1

# 启动应用
CMD ["python", "app.py"]

