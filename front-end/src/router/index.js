import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue'),
    meta: { guest: true }
  },
  {
    path: '/home',
    name: 'home',
    component: () => import('@/views/HomeView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/system',
    name: 'system',
    component: () => import('@/views/SystemView.vue'),
    meta: { requiresAuth: true, requiresAdmin: true }
  },
  {
    path: '/data-fetch',
    name: 'dataFetch',
    component: () => import('@/views/DataFetchView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/assistant',
    name: 'assistant',
    component: () => import('@/views/AssistantView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/model-predict',
    name: 'modelPredict',
    component: () => import('@/views/ModelPredictView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/risk-center',
    name: 'riskCenter',
    component: () => import('@/views/RiskCenterView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Token验证状态缓存
let tokenValidationCache = null
let lastValidatedToken = null  // 记录上次验证的token
let validationInProgress = false

// 验证Token有效性
async function validateToken() {
  const token = localStorage.getItem('token')
  if (!token) {
    return false
  }

  // 如果token发生变化，清除缓存重新验证
  if (lastValidatedToken !== token) {
    tokenValidationCache = null
    lastValidatedToken = token
  }

  // 如果正在验证中，等待结果
  if (validationInProgress) {
    // 简单等待机制
    await new Promise(resolve => setTimeout(resolve, 100))
    return tokenValidationCache
  }

  // 如果已有缓存结果，直接返回
  if (tokenValidationCache !== null) {
    return tokenValidationCache
  }

  validationInProgress = true

  try {
    const response = await axios.get('/api/auth/validate', {
      headers: {
        Authorization: `Bearer ${token}`
      },
      timeout: 5000
    })

    if (response.data && response.data.code === 200) {
      // 更新userInfo（可能用户信息有变化）
      if (response.data.data) {
        localStorage.setItem('userInfo', JSON.stringify(response.data.data))
      }
      tokenValidationCache = true
      return true
    }

    // Token无效，清除本地存储和缓存
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    tokenValidationCache = false
    lastValidatedToken = null
    return false
  } catch (error) {
    // 验证失败（401或网络错误），清除本地存储和缓存
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    tokenValidationCache = false
    lastValidatedToken = null
    return false
  } finally {
    validationInProgress = false
  }
}

// 路由守卫
router.beforeEach(async (to, from, next) => {
  const token = localStorage.getItem('token')
  const userInfo = localStorage.getItem('userInfo')

  // 如果没有token或userInfo，直接视为未登录
  if (!token || !userInfo) {
    // 清除可能存在的无效数据
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    tokenValidationCache = false
    lastValidatedToken = null

    if (to.meta.requiresAuth) {
      next({ name: 'login' })
      return
    }
    next()
    return
  }

  // 验证Token有效性（仅在有token时执行）
  const isValid = await validateToken()

  // 已登录用户访问登录页，重定向到主页
  if (to.meta.guest && isValid) {
    next({ name: 'home' })
    return
  }

  // 需要登录的页面
  if (to.meta.requiresAuth) {
    if (!isValid) {
      next({ name: 'login' })
      return
    }

    // 需要管理员权限
    if (to.meta.requiresAdmin) {
      try {
        const user = JSON.parse(userInfo)
        if (user.role !== 'ADMIN') {
          next({ name: 'home' })
          return
        }
      } catch (e) {
        next({ name: 'login' })
        return
      }
    }
  }

  next()
})

export default router
