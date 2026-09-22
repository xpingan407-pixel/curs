import { API_BASE } from './config.js'

const TOKEN_KEY = 'dice_game_token'

export function getToken() {
  return uni.getStorageSync(TOKEN_KEY) || ''
}

export function setToken(token) {
  uni.setStorageSync(TOKEN_KEY, token)
}

function request(action, { method = 'GET', data = null } = {}) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE}?action=${action}`,
      method,
      data,
      header: {
        'Content-Type': 'application/json',
        'X-Game-Token': getToken(),
      },
      success: (res) => {
        const body = res.data
        if (!body || body.ok === false) {
          reject(new Error(body?.message || '请求失败'))
          return
        }
        resolve(body)
      },
      fail: (err) => reject(new Error(err.errMsg || '网络错误')),
    })
  })
}

export function initGame() {
  return request('init')
}

export function fetchStatus() {
  return request('status')
}

export function playRound(betType, amount) {
  return request('play', {
    method: 'POST',
    data: { betType, amount },
  })
}
