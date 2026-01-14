import { getUserInfo, logout } from '@/api/user'

const state = {
  user_id: '',
  user_name: '',
  user_dept: '',
  user_phone: '',
  user_email: '',
  user_type_code: '',  // 用户类型代码：faculty, student, external_teacher等
  user_type: 'normal',  // 用户身份类型：normal, category_admin, super_admin
  // 权限信息
  is_super_admin: false,
  can_manage_form: false,
  can_manage_external: false,
  is_category_admin: false,
  managed_category_ids: []
}

const mutations = {
  SET_USER_INFO(state, userInfo) {
    state.user_id = userInfo.user_id || ''
    state.user_name = userInfo.user_name || ''
    state.user_dept = userInfo.user_dept || ''
    state.user_phone = userInfo.user_phone || ''
    state.user_email = userInfo.user_email || ''
    state.user_type_code = userInfo.user_type_code || ''  // 用户类型代码（faculty, student等）
    state.user_type = userInfo.user_type || 'normal'  // 用户身份类型（normal/category_admin/super_admin）
    // 权限信息
    state.is_super_admin = userInfo.is_super_admin || false
    state.can_manage_form = userInfo.can_manage_form || false
    state.can_manage_external = userInfo.can_manage_external || false
    state.is_category_admin = userInfo.is_category_admin || false
    state.managed_category_ids = userInfo.managed_category_ids || []
  },
  CLEAR_USER_INFO(state) {
    state.user_id = ''
    state.user_name = ''
    state.user_dept = ''
    state.user_phone = ''
    state.user_email = ''
    state.user_type_code = ''
    state.user_type = 'normal'
    // 清除权限信息
    state.is_super_admin = false
    state.can_manage_form = false
    state.can_manage_external = false
    state.is_category_admin = false
    state.managed_category_ids = []
  }
}

const actions = {
  // 获取用户信息
  async getUserInfo({ commit }) {
    try {
      console.log('Store: 开始获取用户信息...')
      const res = await getUserInfo()
      console.log('Store: 获取用户信息响应:', res)
      if (res.success && res.data) {
        commit('SET_USER_INFO', res.data)
        console.log('Store: 用户信息已设置:', res.data.user_id)
        return res.data
      } else {
        // 如果返回不成功，抛出错误
        console.error('Store: 获取用户信息失败，响应:', res)
        throw new Error(res.message || '获取用户信息失败')
      }
    } catch (error) {
      console.error('Store: 获取用户信息异常:', error)
      // 重新抛出错误，让调用者知道失败
      throw error
    }
  },
  
  // 登出
  async logout({ commit }) {
    try {
      await logout()
    } catch (error) {
      console.error('登出失败:', error)
    } finally {
      commit('CLEAR_USER_INFO')
    }
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions
}

