# 图书馆审批系统

## 项目结构

```
processSys/
├── code/
│   ├── backend/          # Flask后端
│   └── frontend/          # Vue.js前端
├── docker-compose.yml     # Docker Compose配置
└── README.md
```

## 环境要求

- Python 3.8+
- Node.js 14+
- Docker & Docker Compose
- SQL Server数据库

## 快速开始

### 服务器部署

```bash
# 启动服务
cd /opt/processSys/code
docker compose up -d

# 查看日志
docker compose logs -f

# 停止服务
docker compose down
```

### 本地开发

#### 后端开发

```bash
cd code/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

#### 前端开发

```bash
cd code/frontend
npm install
npm run serve
```

## Git工作流程

### 首次设置（本地）

```bash
# 克隆仓库（如果使用远程仓库）
git clone <远程仓库地址> processSys
cd processSys

# 或者如果已有代码，添加远程仓库
git remote add origin <远程仓库地址>
git branch -M main
git push -u origin main
```

### 日常开发流程

#### 在本地开发

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 创建功能分支（可选）
git checkout -b feature/your-feature-name

# 3. 修改代码...

# 4. 提交更改
git add .
git commit -m "描述你的更改"

# 5. 推送到远程仓库
git push origin main  # 或 git push origin feature/your-feature-name
```

#### 在服务器上更新

```bash
# 1. 进入项目目录
cd /opt/processSys

# 2. 拉取最新代码
git pull origin main

# 3. 重新构建并重启服务
cd code
docker compose build
docker compose up -d
```

## 注意事项

- 不要提交敏感信息（密码、密钥等）到Git仓库
- 使用环境变量管理配置
- 提交前检查.gitignore是否正确排除不需要的文件

