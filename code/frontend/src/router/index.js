import Vue from 'vue'
import VueRouter from 'vue-router'
import store from '../store'

Vue.use(VueRouter)

const routes = [
  {
    path: '/test',
    name: 'ErrorTest',
    component: () => import('@/views/ErrorTest.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/layout/index.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: false }, // 首页不强制要求认证，由组件内部处理
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'work-orders',
        name: 'WorkOrders',
        component: () => import('@/views/workOrder/List.vue'),
        meta: { title: '我的工单' }
      },
      {
        path: 'work-orders/management',
        name: 'WorkOrderManagement',
        component: () => import('@/views/workOrder/Management.vue').catch(err => {
          console.error('加载Management组件失败:', err)
          return import('@/views/ErrorTest.vue')
        }),
        meta: { title: '工单管理', requiresPermission: 'admin' }
      },
      {
        path: 'work-orders/create',
        name: 'CreateWorkOrder',
        component: () => import('@/views/workOrder/Create.vue'),
        meta: { title: '新建工单' }
      },
      {
        path: 'work-orders/:id',
        name: 'WorkOrderDetail',
        component: () => import('@/views/workOrder/Detail.vue'),
        meta: { title: '工单详情' }
      },
      {
        path: 'form-configs',
        name: 'FormConfigs',
        component: () => import('@/views/formConfig/List.vue'),
        meta: { title: '表单配置', requiresPermission: 'manage_form' }
      },
      {
        path: 'form-configs/:id',
        name: 'FormConfigDetail',
        component: () => import('@/views/formConfig/Detail.vue'),
        meta: { title: '表单配置详情', requiresPermission: 'manage_form' }
      },
      {
        path: 'admin',
        name: 'Admin',
        component: () => import('@/views/admin/Index.vue'),
        meta: { title: '系统管理', requiresPermission: 'super_admin' }
      }
    ]
  }
]

// 获取基础路径
// 统一使用 /libProcess/ 作为基础路径
// 可通过环境变量 BASE_URL 覆盖
const basePath = process.env.BASE_URL || '/libProcess/'

const router = new VueRouter({
  mode: 'history',
  base: basePath,
  routes
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 如果访问登录页，不需要检查用户信息
  if (to.path === '/login') {
    next()
    return
  }
  
  // 检查是否需要认证
  if (to.meta.requiresAuth !== false) {
    // 尝试获取用户信息
    if (!store.state.user.user_id) {
      try {
        await store.dispatch('user/getUserInfo')
      } catch (error) {
        // 获取失败，跳转到登录页
        // 使用replace避免在历史记录中留下记录
        next({ path: '/login', replace: true })
        return
      }
    }
  }
  
  // 检查权限
  if (to.meta.requiresPermission) {
    const permission = to.meta.requiresPermission
    const user = store.state.user
    
    // 确保用户信息已加载
    if (!user.user_id) {
      try {
        await store.dispatch('user/getUserInfo')
      } catch (error) {
        next({ path: '/login', replace: true })
        return
      }
    }
    
    if (permission === 'super_admin') {
      if (!user.is_super_admin) {
        next({ path: '/dashboard', replace: true })
        return
      }
    } else if (permission === 'manage_form') {
      // 超级管理员或can_manage_form权限可以管理表单
      // 类别管理员也可以管理表单（但只能管理自己管理的类别）
      if (!user.is_super_admin && !user.can_manage_form && !user.is_category_admin) {
        next({ path: '/dashboard', replace: true })
        return
      }
    } else if (permission === 'admin') {
      // 管理员权限（超级管理员或类别管理员）
      if (!user.is_super_admin && !user.is_category_admin) {
        next({ path: '/dashboard', replace: true })
        return
      }
    }
  }
  
  // 如果访问首页，检查是否有登录成功参数
  if (to.path === '/' || to.path === '/dashboard') {
    const urlParams = new URLSearchParams(window.location.search)
    const loginSuccess = urlParams.get('login')
    if (loginSuccess === 'success') {
      // 登录成功，刷新用户信息并清除URL参数
      try {
        await store.dispatch('user/getUserInfo')
        const newUrl = window.location.pathname
        window.history.replaceState({}, '', newUrl)
      } catch (error) {
        // 获取用户信息失败，跳转到登录页
        // 使用replace避免在历史记录中留下记录
        next({ path: '/login', replace: true })
        return
      }
    }
  }
  
  next()
})

export default router

