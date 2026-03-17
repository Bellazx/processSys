# GitHub仓库设置完成

## 已完成的配置

✅ Git用户信息已设置：
- 用户名：Bellazx
- 邮箱：dingbella@foxmail.com

✅ 远程仓库已添加：
- 地址：https://github.com/Bellazx/processSys.git

## 下一步操作

### 1. 在GitHub上创建仓库

1. 访问：https://github.com/new
2. 仓库名称：`processSys`
3. 描述（可选）：图书馆审批系统
4. 选择 Public（公开）或 Private（私有）
5. **重要**：不要勾选以下选项：
   - ❌ Add a README file
   - ❌ Add .gitignore
   - ❌ Choose a license
6. 点击 "Create repository"

### 2. 推送代码到GitHub

#### 方式A：使用HTTPS（需要Token）

**获取GitHub Personal Access Token：**

1. 访问：https://github.com/settings/tokens
2. 点击 "Generate new token (classic)"
3. Note（备注）：`processSys-server`
4. 过期时间：选择 "No expiration" 或自定义
5. 勾选权限：`repo`（全部勾选）
6. 点击 "Generate token"
7. **重要**：复制Token（只显示一次，请保存）

**推送代码：**

```bash
cd /opt/processSys
git push -u origin main
```

当提示输入时：
- Username: `Bellazx`
- Password: **粘贴刚才复制的Token**（不是GitHub密码）

#### 方式B：使用SSH（推荐，无需密码）

**生成SSH密钥：**

```bash
# 生成SSH密钥
ssh-keygen -t ed25519 -C "dingbella@foxmail.com"
# 按回车使用默认路径
# 可以设置密码或直接回车（推荐设置密码）

# 查看公钥
cat ~/.ssh/id_ed25519.pub
# 复制输出的全部内容
```

**添加SSH密钥到GitHub：**

1. 访问：https://github.com/settings/ssh/new
2. Title（标题）：`processSys-server`
3. Key（密钥）：粘贴刚才复制的公钥
4. 点击 "Add SSH key"

**测试SSH连接：**

```bash
ssh -T git@github.com
# 输入 yes，应该看到：Hi Bellazx! You've successfully authenticated...
```

**切换到SSH地址并推送：**

```bash
cd /opt/processSys
# 删除HTTPS远程仓库
git remote remove origin

# 添加SSH远程仓库
git remote add origin git@github.com:Bellazx/processSys.git

# 推送代码
git push -u origin main
```

### 3. 在本地连接仓库

#### 如果本地没有代码：

```bash
# 克隆仓库
git clone https://github.com/Bellazx/processSys.git
# 或使用SSH：git clone git@github.com:Bellazx/processSys.git
cd processSys
```

#### 如果本地已有代码：

```bash
cd /path/to/your/local/processSys

# 添加远程仓库
git remote add origin https://github.com/Bellazx/processSys.git
# 或使用SSH：git remote add origin git@github.com:Bellazx/processSys.git

# 拉取代码（如果有冲突需要解决）
git pull origin main --allow-unrelated-histories
```

## 日常使用流程

### 在本地开发：

```bash
# 1. 拉取最新代码
git pull origin main

# 2. 修改代码...

# 3. 提交更改
git add .
git commit -m "描述你的更改"

# 4. 推送到GitHub
git push origin main
```

### 在服务器上更新：

```bash
# 1. 进入项目目录
cd /opt/processSys

# 2. 拉取最新代码
git pull origin main

# 3. 重新构建并重启服务
cd code
docker compose build
docker compose up -d

# 4. 查看日志
docker compose logs -f
```

## 常用命令

```bash
# 查看远程仓库
git remote -v

# 查看提交历史
git log --oneline -10

# 查看状态
git status

# 查看差异
git diff
```

## 注意事项

⚠️ **重要提示**：

1. **不要提交敏感信息**：
   - 密码、密钥、API密钥
   - 数据库连接字符串（包含密码）
   - 使用环境变量管理敏感配置

2. **检查.gitignore**：
   - 确保 `venv/`、`node_modules/`、`flask_session/` 等已被忽略

3. **GitHub Token安全**：
   - Token只显示一次，请妥善保存
   - 如果丢失，需要重新生成
   - 不要分享Token给他人

4. **SSH密钥安全**：
   - 私钥（`~/.ssh/id_ed25519`）不要分享
   - 公钥（`~/.ssh/id_ed25519.pub`）可以添加到GitHub

## 故障排除

### 推送时提示认证失败

**HTTPS方式：**
- 确保使用Personal Access Token，不是GitHub密码
- Token需要有`repo`权限

**SSH方式：**
- 检查SSH密钥是否已添加到GitHub
- 测试连接：`ssh -T git@github.com`

### 保存凭据（避免每次输入）

```bash
# HTTPS方式：使用Git凭据存储
git config --global credential.helper store
```

