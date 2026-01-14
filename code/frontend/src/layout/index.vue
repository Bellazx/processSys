<template>
  <div class="layout-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <div class="logo">
            <h2>图书馆审批系统</h2>
          </div>
          <div class="user-info">
            <el-dropdown @command="handleCommand">
              <span class="user-name">
                {{ userInfo.user_name || userInfo.user_id }}
                <i class="el-icon-arrow-down el-icon--right"></i>
              </span>
              <el-dropdown-menu slot="dropdown">
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </el-dropdown>
          </div>
        </div>
      </el-header>
      <el-container>
        <el-aside width="200px">
          <el-menu
            :default-active="activeMenu"
            router
            background-color="#545c64"
            text-color="#fff"
            active-text-color="#ffd04b"
          >
            <el-menu-item index="/dashboard">
              <i class="el-icon-s-home"></i>
              <span>首页</span>
            </el-menu-item>
            <el-menu-item index="/work-orders">
              <i class="el-icon-document"></i>
              <span>我的工单</span>
            </el-menu-item>
            <el-menu-item index="/work-orders/create">
              <i class="el-icon-plus"></i>
              <span>新建工单</span>
            </el-menu-item>
            <el-menu-item 
              v-if="isAdmin"
              index="/work-orders/management"
            >
              <i class="el-icon-s-order"></i>
              <span>工单管理</span>
            </el-menu-item>
            <el-menu-item 
              v-if="canManageForm"
              index="/form-configs"
            >
              <i class="el-icon-setting"></i>
              <span>表单配置</span>
            </el-menu-item>
            <el-menu-item 
              v-if="isSuperAdmin"
              index="/admin"
            >
              <i class="el-icon-user-solid"></i>
              <span>系统管理</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script>
import { mapState } from 'vuex'
import { logout } from '@/api/user'

export default {
  name: 'Layout',
  computed: {
    ...mapState('user', ['user_id', 'user_name', 'user_dept']),
    userInfo() {
      return {
        user_id: this.user_id,
        user_name: this.user_name,
        user_dept: this.user_dept
      }
    },
    activeMenu() {
      return this.$route.path
    },
    canManageForm() {
      return this.$store.state.user.can_manage_form || this.$store.state.user.is_super_admin
    },
    isSuperAdmin() {
      return this.$store.state.user.is_super_admin
    },
    isAdmin() {
      return this.$store.state.user.is_super_admin || this.$store.state.user.is_category_admin
    }
  },
  methods: {
    async handleCommand(command) {
      if (command === 'logout') {
        try {
          const res = await logout()
          if (res.success && res.logoutUrl) {
            // 跳转到jAccount登出页面
            window.location.href = res.logoutUrl
          } else {
            this.$store.dispatch('user/logout')
            this.$router.push('/login')
          }
        } catch (error) {
          this.$store.dispatch('user/logout')
          this.$router.push('/login')
        }
      }
    }
  }
}
</script>

<style lang="scss" scoped>
.layout-container {
  width: 100%;
  height: 100%;
  
  .el-container {
    height: 100%;
  }
  
  .el-header {
    background-color: #409EFF;
    color: #fff;
    line-height: 60px;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .logo h2 {
        margin: 0;
        font-size: 20px;
      }
      
      .user-info {
        .user-name {
          cursor: pointer;
          color: #fff;
        }
      }
    }
  }
  
  .el-aside {
    background-color: #545c64;
    
    .el-menu {
      border-right: none;
    }
  }
  
  .el-main {
    background-color: #f0f2f5;
    padding: 20px;
  }
}
</style>

