<template>
  <div class="login-container">
    <div class="login-box">
      <h2>图书馆审批系统</h2>
      <p>请使用jAccount账号登录</p>
      <el-button 
        type="primary" 
        size="large" 
        @click="handleLogin"
        :loading="loading"
      >
        登录
      </el-button>
    </div>
  </div>
</template>

<script>
import { login } from '@/api/user'

export default {
  name: 'Login',
  data() {
    return {
      loading: false
    }
  },
  mounted() {
    // 检查URL中是否有登出成功参数
    // 处理URL格式错误的情况：/login&state=... 应该是 /login?state=...
    const fullUrl = window.location.href
    const currentPath = window.location.pathname
    
    // 如果URL中包含&state=或&logout=，说明URL格式有问题
    // 需要修复URL格式并重定向
    if (fullUrl.includes('&state=') || fullUrl.includes('&logout=')) {
      // 提取参数
      const urlMatch = fullUrl.match(/[&?](logout|state)=([^&]*)/g)
      if (urlMatch) {
        // 构建正确的URL格式
        const params = new URLSearchParams()
        urlMatch.forEach(param => {
          const [key, value] = param.replace(/^[&?]/, '').split('=')
          params.set(key, decodeURIComponent(value))
        })
        
        // 检查是否有logout=success
        if (params.get('logout') === 'success') {
          // 登出成功，清除本地用户信息
          this.$store.commit('user/CLEAR_USER_INFO')
          this.$message.success('已成功登出')
          // 重定向到干净的登录页
          this.$router.replace('/login')
          return
        }
        
        // 如果有state参数但没有logout，可能是jAccount直接重定向
        // 重定向到正确的URL格式
        const correctUrl = `${currentPath}?${params.toString()}`
        window.history.replaceState({}, '', correctUrl)
      }
    }
    
    // 正常处理URL参数
    const urlParams = new URLSearchParams(window.location.search)
    const logoutSuccess = urlParams.get('logout')
    
    if (logoutSuccess === 'success') {
      // 登出成功，清除本地用户信息（确保清除）
      this.$store.commit('user/CLEAR_USER_INFO')
      this.$message.success('已成功登出')
      // 清除URL参数
      const newUrl = window.location.pathname
      window.history.replaceState({}, '', newUrl)
      return
    }
    
    // 如果已经登录，直接跳转到首页（但不在登出后检查，避免触发API）
    // 注意：这里不调用getUserInfo，只检查store中是否有user_id
    // 如果store中有user_id但实际未登录，路由守卫会处理
    if (this.$store.state.user.user_id) {
      // 延迟检查，避免在登出后立即跳转
      this.$nextTick(() => {
        if (this.$store.state.user.user_id) {
          this.$router.push('/dashboard')
        }
      })
      return
    }
    
    // 检查URL中是否有OAuth回调参数
    const code = urlParams.get('code')
    const state = urlParams.get('state')
    
    if (code) {
      // 处理OAuth回调
      this.handleCallback(code, state)
    }
  },
  methods: {
    async handleLogin() {
      this.loading = true
      try {
        const res = await login()
        if (res.success && res.loginUrl) {
          // 跳转到jAccount登录页面
          window.location.href = res.loginUrl
        }
      } catch (error) {
        this.$message.error('登录失败，请重试')
      } finally {
        this.loading = false
      }
    },
    async handleCallback(code, state) {
      // 调用后端回调接口处理OAuth回调
      this.loading = true
      try {
        // 调用后端回调接口
        const response = await fetch(`/process/auth/callback?code=${code}&state=${state || ''}`, {
          method: 'GET',
          credentials: 'include' // 重要：包含cookie，用于设置session
        })
        
        const result = await response.json()
        
        if (result.success) {
          // 登录成功，更新用户信息
          await this.$store.dispatch('user/getUserInfo')
          // 清除URL中的code参数
          const newUrl = window.location.pathname
          window.history.replaceState({}, '', newUrl)
          // 跳转到首页
          this.$router.push('/dashboard')
        } else {
          this.$message.error(result.message || '登录失败，请重试')
        }
      } catch (error) {
        console.error('登录回调处理失败:', error)
        this.$message.error('登录失败，请重试')
      } finally {
        this.loading = false
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.login-container {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  
  .login-box {
    background: #fff;
    padding: 40px;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    text-align: center;
    min-width: 400px;
    
    h2 {
      margin-bottom: 10px;
      color: #333;
    }
    
    p {
      margin-bottom: 30px;
      color: #666;
    }
    
    .el-button {
      width: 100%;
    }
  }
}
</style>

