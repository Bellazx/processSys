import request from '../utils/request'

// 系统管理员
export function getAdminConfigs() {
  return request({
    url: '/admin-configs',
    method: 'get'
  })
}

export function createAdminConfig(data) {
  return request({
    url: '/admin-configs',
    method: 'post',
    data
  })
}

export function updateAdminConfig(id, data) {
  return request({
    url: `/admin-configs/${id}`,
    method: 'put',
    data
  })
}

export function deleteAdminConfig(id) {
  return request({
    url: `/admin-configs/${id}`,
    method: 'delete'
  })
}

// 部门管理员
export function getDepartmentAdmins() {
  return request({
    url: '/department-admins',
    method: 'get'
  })
}

export function createDepartmentAdmin(data) {
  return request({
    url: '/department-admins',
    method: 'post',
    data
  })
}

export function deleteDepartmentAdmin(id) {
  return request({
    url: `/department-admins/${id}`,
    method: 'delete'
  })
}

// 工单类别
export function getCategories(params) {
  return request({
    url: '/categories',
    method: 'get',
    params
  })
}

export function createCategory(data) {
  return request({
    url: '/categories',
    method: 'post',
    data
  })
}

export function updateCategory(id, data) {
  return request({
    url: `/categories/${id}`,
    method: 'put',
    data
  })
}

export function deleteCategory(id) {
  return request({
    url: `/categories/${id}`,
    method: 'delete'
  })
}

// 类别管理员
export function getCategoryAdmins(params) {
  return request({
    url: '/category-admins',
    method: 'get',
    params
  })
}

export function createCategoryAdmin(data) {
  return request({
    url: '/category-admins',
    method: 'post',
    data
  })
}

export function deleteCategoryAdmin(id) {
  return request({
    url: `/category-admins/${id}`,
    method: 'delete'
  })
}

// 员工搜索
export function searchStaff(params) {
  return request({
    url: '/staff/search',
    method: 'get',
    params
  })
}

// 部门列表
export function getDepartments() {
  return request({
    url: '/departments',
    method: 'get'
  })
}

