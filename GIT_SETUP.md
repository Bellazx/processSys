# Git仓库设置指南

## 服务器端已完成

✅ Git仓库已初始化
✅ 代码已提交到本地仓库
✅ 主分支已重命名为 `main`

## 下一步操作

### 方案1：使用GitHub/GitLab/Gitee等远程仓库（推荐）

#### 1. 创建远程仓库

在GitHub/GitLab/Gitee上创建一个新仓库（例如：`processSys`），**不要**初始化README、.gitignore或license。

#### 2. 在服务器上添加远程仓库

```bash
cd /opt/processSys
git remote add origin <你的远程仓库地址>
# 例如：git remote add origin https://github.com/yourusername/processSys.git
# 或：git remote add origin git@github.com:yourusername/processSys.git
```

#### 3. 推送代码到远程仓库

```bash
git push -u origin main
```

#### 4. 在本地克隆仓库

```bash
# 克隆到本地
git clone <你的远程仓库地址> processSys-local
cd processSys-local

# 或者如果本地已有代码，添加远程仓库并拉取
cd /path/to/your/local/processSys
git remote add origin <你的远程仓库地址>
git fetch origin
git branch --set-upstream-to=origin/main main
git pull origin main
```

### 方案2：使用SSH直接同步（适合内网环境）

#### 在服务器上设置SSH密钥

```bash
# 生成SSH密钥（如果还没有）
ssh-keygen -t rsa -b 4096 -C "server@processsys"

# 将公钥添加到本地机器的 ~/.ssh/authorized_keys
cat ~/.ssh/id_rsa.pub
```

#### 在本地添加服务器为远程仓库

```bash
# 在本地代码目录
cd /path/to/your/local/processSys
git init
git remote add server ssh://root@10.119.9.223/opt/processSys/.git
# 或使用其他用户：git remote add server ssh://user@10.119.9.223/opt/processSys/.git
```

## 日常使用流程

### 在本地开发

```bash
# 1. 拉取最新代码
git pull origin main  # 或 git pull server main

# 2. 创建功能分支（可选，推荐）
git checkout -b feature/your-feature-name

# 3. 修改代码...

# 4. 提交更改
git add .
git commit -m "描述你的更改"

# 5. 推送到远程
git push origin main  # 或 git push server main
```

### 在服务器上更新

```bash
# 1. 进入项目目录
cd /opt/processSys

# 2. 拉取最新代码
git pull origin main  # 或 git pull server main

# 3. 重新构建并重启服务
cd code
docker compose build
docker compose up -d

# 4. 查看日志确认
docker compose logs -f
```

## 常用Git命令

```bash
# 查看状态
git status

# 查看提交历史
git log --oneline -10

# 查看差异
git diff

# 撤销未提交的更改
git checkout -- <file>

# 创建并切换分支
git checkout -b feature/new-feature

# 合并分支
git checkout main
git merge feature/new-feature

# 删除分支
git branch -d feature/new-feature
```

## 注意事项

⚠️ **重要提示**：

1. **不要提交敏感信息**：
   - 密码、密钥、API密钥
   - 数据库连接字符串（包含密码）
   - 使用环境变量管理敏感配置

2. **检查.gitignore**：
   - 确保 `venv/`、`node_modules/`、`flask_session/` 等目录已被忽略
   - 不要提交 `dist/`、`*.pyc` 等编译文件

3. **提交前检查**：
   ```bash
   git status  # 查看将要提交的文件
   git diff    # 查看更改内容
   ```

4. **服务器更新后**：
   - 记得重新构建Docker镜像
   - 检查服务是否正常运行

## 故障排除

### 如果推送失败

```bash
# 先拉取远程更改
git pull origin main --rebase

# 解决冲突后再次推送
git push origin main
```

### 如果本地有未提交的更改

```bash
# 暂存更改
git stash

# 拉取最新代码
git pull origin main

# 恢复更改
git stash pop
```

### 查看远程仓库配置

```bash
git remote -v
```

