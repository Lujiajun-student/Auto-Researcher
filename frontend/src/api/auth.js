import request from '@/utils/request'

// 用户注册
export function register(username, password) {
  return request({
    url: '/auth/register',
    method: 'post',
    data: {
      username,
      password
    }
  })
}

// 用户登录
export function login(username, password) {
  return request({
    url: '/auth/login',
    method: 'post',
    data: {
      username,
      password
    }
  })
}

// 退出登录
export function logout() {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

// 获取用户信息
export function getUserInfo(userId) {
  return request({
    url: `/auth/${userId}`,
    method: 'get'
  })
}
