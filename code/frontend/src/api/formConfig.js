import request from '../utils/request'

export function getFormConfigs(params) {
  return request({
    url: '/form-configs',
    method: 'get',
    params
  })
}

export function getFormConfig(id) {
  return request({
    url: `/form-configs/${id}`,
    method: 'get'
  })
}

export function createFormConfig(data) {
  return request({
    url: '/form-configs',
    method: 'post',
    data
  })
}

export function updateFormConfig(id, data) {
  return request({
    url: `/form-configs/${id}`,
    method: 'put',
    data
  })
}

export function publishFormConfig(id) {
  return request({
    url: `/form-configs/${id}/publish`,
    method: 'post'
  })
}

export function archiveFormConfig(id) {
  return request({
    url: `/form-configs/${id}/archive`,
    method: 'post'
  })
}

export function deleteFormConfig(id) {
  return request({
    url: `/form-configs/${id}`,
    method: 'delete'
  })
}

