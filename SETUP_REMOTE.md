# 设置Git远程仓库指南

## 方式选择

### 方式1：HTTPS（需要用户名密码或Token）

适合：GitHub、GitLab、Gitee等平台

**GitHub设置步骤：**

1. **创建GitHub仓库**
   - 访问 https://github.com/new
   - 仓库名：`processSys`
   - 选择 Private（私有）或 Public（公开）
   - **不要**勾选初始化README、.gitignore、license

2. **获取Personal Access Token（推荐）**
   - GitHub已不支持密码认证，需要使用Token
   - 访问：https://github.com/settings/tokens
   - 点击 "Generate new token (classic)"
   - 勾选 `repo` 权限
   - 复制生成的Token（只显示一次，请保存）

3. **在服务器上添加远程仓库**
   ```bash
   cd /opt/processSys
   git remote add origin https://github.com/你的用户名/processSys.git
   ```

4. **推送代码（会提示输入用户名和Token）**
   ```bash
   git push -u origin main
   # 用户名：你的GitHub用户名
   # 密码：使用刚才生成的Personal Access Token
   ```

**Gitee设置步骤（类似）：**

1. 访问 https://gitee.com/projects/new 创建仓库
2. 在服务器上：
   ```bash
   cd /opt/processSys
   git remote add origin https://gitee.com/你的用户名/processSys.git
   git push -u origin main
   # 用户名：你的Gitee用户名
   # 密码：你的Gitee密码（或使用Token）
   ```

### 方式2：SSH（无需密码，推荐）

适合：GitHub、GitLab、Gitee等平台

**设置步骤：**

1. **在服务器上生成SSH密钥**
   ```bash
   ssh-keygen -t ed25519 -C "server@processsys"
   # 按回车使用默认路径，可以设置密码或直接回车
   ```

2. **查看公钥**
   ```bash
   cat ~/.ssh/id_ed25519.pub
   # 复制输出的内容
   ```

3. **添加到Git平台**
   - **GitHub**: https://github.com/settings/ssh/new
   - **GitLab**: https://gitlab.com/-/profile/keys
   - **Gitee**: https://gitee.com/profile/sshkeys
   - 粘贴公钥内容，保存

4. **测试SSH连接**
   ```bash
   # GitHub
   ssh -T git@github.com
   
   # GitLab
   ssh -T git@gitlab.com
   
   # Gitee
   ssh -T git@gitee.com
   ```

5. **添加远程仓库（使用SSH地址）**
   ```bash
   cd /opt/processSys
   git remote add origin git@github.com:你的用户名/processSys.git
   # 或 git@gitlab.com:你的用户名/processSys.git
   # 或 git@gitee.com:你的用户名/processSys.git
   ```

6. **推送代码**
   ```bash
   git push -u origin main
   # 无需输入密码
   ```

## 快速设置脚本

### 对于GitHub（HTTPS方式）

```bash
cd /opt/processSys

# 设置你的GitHub信息
GITHUB_USERNAME="你的GitHub用户名"
GITHUB_REPO="processSys"

# 添加远程仓库
git remote add origin https://github.com/${GITHUB_USERNAME}/${GITHUB_REPO}.git

# 查看远程仓库
git remote -v

# 推送代码（会提示输入Token）
git push -u origin main
```

### 对于GitHub（SSH方式）

```bash
cd /opt/processSys

# 设置你的GitHub信息
GITHUB_USERNAME="你的GitHub用户名"
GITHUB_REPO="processSys"

# 添加远程仓库
git remote add origin git@github.com:${GITHUB_USERNAME}/${GITHUB_REPO}.git

# 查看远程仓库
git remote -v

# 推送代码
git push -u origin main
```

## 常见问题

### 1. 如果已经添加了远程仓库，想更换

```bash
# 删除现有远程仓库
git remote remove origin

# 添加新的远程仓库
git remote add origin <新的仓库地址>
```

### 2. 查看当前远程仓库配置

```bash
git remote -v
```

### 3. 推送时提示认证失败

**HTTPS方式：**
- GitHub需要使用Personal Access Token，不是密码
- 确保Token有`repo`权限

**SSH方式：**
- 检查SSH密钥是否已添加到Git平台
- 测试SSH连接：`ssh -T git@github.com`

### 4. 保存凭据（避免每次输入）

**HTTPS方式：**
```bash
# 使用Git凭据存储
git config --global credential.helper store
# 第一次输入后会自动保存
```

**SSH方式：**
- 如果设置了SSH密钥密码，可以使用ssh-agent：
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

## 下一步

设置完远程仓库后：

1. **在本地克隆或连接**
   ```bash
   git clone <远程仓库地址> processSys-local
   ```

2. **日常使用**
   - 本地开发 → `git push`
   - 服务器更新 → `git pull`

