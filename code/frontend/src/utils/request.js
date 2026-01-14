import axios from 'axios'
import { Message } from 'element-ui'
import router from '../router'
import store from '../store'

// 创建axios实例
const service = axios.create({
  baseURL: '/process',
  timeout: 60000, // 增加超时时间到60秒，Excel导出可能需要更长时间
  withCredentials: true
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 可以在这里添加token等
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  response => {
    // 如果是blob响应（Excel导出等），直接返回response
    if (response.config.responseType === 'blob' || response.data instanceof Blob) {
      return response
    }
    
    const res = response.data
    
    // 登录接口特殊处理：直接返回，不进行错误拦截
    const isLoginRequest = response.config && response.config.url && response.config.url.includes('/auth/login')
    if (isLoginRequest) {
      return res
    }
    
    // 如果返回的状态码不是200，说明有错误
    if (res.success === false) {
      // 检查当前路由是否是登录页
      const isLoginPage = router.currentRoute && router.currentRoute.path === '/login'
      
      // 检查是否是getUserInfo接口
      const isUserInfoRequest = response.config && response.config.url && response.config.url.includes('/auth/user/info')
      
      // 如果是401未登录错误，且（当前在登录页 或 是getUserInfo接口），则不显示错误提示（这是正常情况）
      if ((response.status === 401 || res.message === '未登录') && (isLoginPage || isUserInfoRequest)) {
        // 静默处理，不显示错误提示
        // 清除store中的用户信息（确保状态一致）
        if (store.state.user.user_id) {
          store.commit('user/CLEAR_USER_INFO')
        }
        return Promise.reject(new Error(res.message || '未登录'))
      }
      
      // 其他错误或不在登录页的401错误，显示错误提示
      Message.error(res.message || '请求失败')
      
      // 401未登录，跳转到登录页（但不在登录页时）
      if ((response.status === 401 || res.message === '未登录') && !isLoginPage) {
        store.dispatch('user/logout')
        // 使用replace避免导航冲突
        router.replace('/login').catch(err => {
          // 忽略导航重复的错误
          if (err.name !== 'NavigationDuplicated') {
            console.error('路由导航错误:', err)
          }
        })
      }
      
      return Promise.reject(new Error(res.message || '请求失败'))
    } else {
      return res
    }
  },
  error => {
    // 检查当前路由是否是登录页
    const isLoginPage = router.currentRoute && router.currentRoute.path === '/login'
    
    // 如果是401错误且当前在登录页，则不显示错误提示（这是正常情况）
    if (error.response && error.response.status === 401 && isLoginPage) {
      // 静默处理，不显示错误提示
      // 清除store中的用户信息（确保状态一致）
      if (store.state.user.user_id) {
        store.commit('user/CLEAR_USER_INFO')
      }
      return Promise.reject(error)
    }
    
    // 检查是否是getUserInfo接口的401错误（未登录时的正常情况）
    const isUserInfoRequest = error.config && error.config.url && error.config.url.includes('/auth/user/info')
    if (error.response && error.response.status === 401 && isUserInfoRequest) {
      // getUserInfo接口的401错误，通常是未登录的正常情况，不显示错误提示
      // 清除store中的用户信息（确保状态一致）
      if (store.state.user.user_id) {
        store.commit('user/CLEAR_USER_INFO')
      }
      return Promise.reject(error)
    }
    
    // 其他错误或不在登录页的401错误，显示错误提示
    console.error('响应错误:', error)
    Message.error(error.message || '网络错误')
    
    if (error.response && error.response.status === 401 && !isLoginPage) {
      store.dispatch('user/logout')
      // 使用replace避免导航冲突
      router.replace('/login').catch(err => {
        // 忽略导航重复的错误
        if (err.name !== 'NavigationDuplicated') {
          console.error('路由导航错误:', err)
        }
      })
    }
    
    return Promise.reject(error)
  }
)

export default service

