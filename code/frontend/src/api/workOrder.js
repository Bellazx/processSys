import request from '../utils/request'

export function getWorkOrders(params) {
  return request({
    url: '/work-orders',
    method: 'get',
    params
  })
}

export function getWorkOrderDetail(id) {
  return request({
    url: `/work-orders/${id}`,
    method: 'get'
  })
}

export function createWorkOrder(data) {
  return request({
    url: '/work-orders',
    method: 'post',
    data
  })
}

export function approveWorkOrder(id, data) {
  return request({
    url: `/work-orders/${id}/approve`,
    method: 'post',
    data
  })
}

export function transferWorkOrder(id, data) {
  return request({
    url: `/work-orders/${id}/transfer`,
    method: 'post',
    data
  })
}

export function externalWorkOrder(id, data) {
  return request({
    url: `/work-orders/${id}/external`,
    method: 'post',
    data
  })
}

export function submitExternalResult(id, data) {
  return request({
    url: `/work-orders/${id}/external/result`,
    method: 'post',
    data
  })
}

export function getDashboardStats(params) {
  return request({
    url: '/dashboard/stats',
    method: 'get',
    params
  })
}

export function getWorkOrdersManagement(params) {
  return request({
    url: '/work-orders/management',
    method: 'get',
    params
  })
}

export function exportWorkOrders(params) {
  return request({
    url: '/work-orders/export',
    method: 'get',
    params,
    responseType: 'blob',
    timeout: 120000 // Excel导出可能需要更长时间，设置120秒超时
  })
}

export function updateWorkOrder(id, data) {
  return request({
    url: `/work-orders/${id}`,
    method: 'put',
    data
  })
}

export function submitDraftWorkOrder(id, data) {
  return request({
    url: `/work-orders/${id}/submit`,
    method: 'post',
    data
  })
}

export function cancelWorkOrder(id) {
  return request({
    url: `/work-orders/${id}/cancel`,
    method: 'post'
  })
}

