<template>
  <div class="error-test">
    <h1>系统诊断</h1>
    <el-card>
      <h2>前端状态</h2>
      <p>前端服务运行正常 ✓</p>
      
      <h2>后端连接测试</h2>
      <el-button @click="testBackend">测试后端连接</el-button>
      <div v-if="backendStatus">
        <p :style="{ color: backendStatus.success ? 'green' : 'red' }">
          {{ backendStatus.message }}
        </p>
      </div>
      
      <h2>路由测试</h2>
      <el-button @click="$router.push('/login')">跳转到登录页</el-button>
      <el-button @click="$router.push('/dashboard')">跳转到首页</el-button>
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'ErrorTest',
  data() {
    return {
      backendStatus: null
    }
  },
  methods: {
    async testBackend() {
      try {
        const response = await fetch('/process/health', {
          method: 'GET',
          credentials: 'include'
        })
        const data = await response.json()
        this.backendStatus = {
          success: response.ok,
          message: data.message || '连接成功'
        }
      } catch (error) {
        this.backendStatus = {
          success: false,
          message: `连接失败: ${error.message}`
        }
      }
    }
  }
}
</script>

<style scoped>
.error-test {
  padding: 20px;
}
h1, h2 {
  margin: 20px 0 10px 0;
}
</style>

