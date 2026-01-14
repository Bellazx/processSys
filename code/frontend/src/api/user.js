import request from '../utils/request'

export function login() {
  return request({
    url: '/auth/login',
    method: 'get'
  })
}

export function getUserInfo() {
  return request({
    url: '/auth/user/info',
    method: 'get'
  })
}

export function logout() {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

