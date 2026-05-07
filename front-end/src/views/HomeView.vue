<template>
  <div class="home-view">
    <!-- 头部导航 -->
    <AppHeader title="智能环境治理中枢平台" />

    <!-- 主内容 -->
    <main class="main-content">
      <!-- 欢迎区域 -->
      <div class="welcome-section">
        <h1 class="welcome-title">欢迎使用智能环境治理中枢平台</h1>
        <p class="welcome-desc">Intelligent Environment Governance Hub</p>
      </div>

      <!-- 功能模块 -->
      <div class="module-grid">
        <!-- 环保数据获取 -->
        <div class="module-card" @click="enterModule('data')">
          <div class="card-header">
            <div class="card-icon">
              <el-icon><DataCollection /></el-icon>
            </div>
            <span class="card-title">环保数据获取</span>
          </div>
          <div class="card-desc">
            实时数据采集<br>
            多源数据整合
          </div>
          <div class="card-status">
            <span class="status-dot"></span>
            <span class="status-text">点击进入</span>
          </div>
        </div>

        <!-- 模型预测与获取 -->
        <div class="module-card" @click="enterModule('predict')">
          <div class="card-header">
            <div class="card-icon">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <span class="card-title">模型预测与获取</span>
          </div>
          <div class="card-desc">
            未来7天空气因子预测<br>
            支持多因子联合查看
          </div>
          <div class="card-status">
            <span class="status-dot"></span>
            <span class="status-text">点击进入</span>
          </div>
        </div>

        <!-- 环保小助手（RAG,Tool） -->
        <div class="module-card" @click="enterModule('assistant')">
          <div class="card-header">
            <div class="card-icon">
              <el-icon><Service /></el-icon>
            </div>
            <span class="card-title">环保小助手（RAG,Tool）</span>
          </div>
          <div class="card-desc">
            RAG知识检索<br>
            智能问答服务
          </div>
          <div class="card-status">
            <span class="status-dot"></span>
            <span class="status-text">点击进入</span>
          </div>
        </div>

        <!-- 环境风险智能研判中心 -->
        <div class="module-card" @click="enterModule('risk')">
          <div class="card-header">
            <div class="card-icon blue">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <span class="card-title">环境风险智能研判中心</span>
          </div>
          <div class="card-desc">
            趋势预测与风险评分<br>
            AI成因解释与治理建议
          </div>
          <div class="card-status">
            <span class="status-dot"></span>
            <span class="status-text">点击进入</span>
          </div>
        </div>

        <!-- 待开发模块 -->
        <div class="module-card disabled" v-for="i in 1" :key="i">
          <div class="card-header">
            <div class="card-icon gray">
              <el-icon><Lock /></el-icon>
            </div>
            <span class="card-title">待开发</span>
          </div>
          <div class="card-desc">
            功能开发中<br>
            敬请期待
          </div>
          <div class="card-status">
            <span class="status-dot pending"></span>
            <span class="status-text">暂未开放</span>
          </div>
        </div>

        <!-- 系统管理 - 仅管理员可见 -->
        <div class="module-card" v-if="userRole === 'ADMIN'" @click="enterModule('system')">
          <div class="card-header">
            <div class="card-icon blue">
              <el-icon><Setting /></el-icon>
            </div>
            <span class="card-title">系统管理</span>
          </div>
          <div class="card-desc">
            用户管理<br>
            权限配置
          </div>
          <div class="card-status">
            <span class="status-dot"></span>
            <span class="status-text">点击进入</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppHeader from '@/components/AppHeader.vue'

const router = useRouter()

const userRole = computed(() => {
  const userInfo = localStorage.getItem('userInfo')
  if (userInfo) {
    const user = JSON.parse(userInfo)
    return user.role || ''
  }
  return ''
})

// 进入模块
const enterModule = (module) => {
  if (module === 'data') {
    router.push('/data-fetch')
  } else if (module === 'predict') {
    router.push('/model-predict')
  } else if (module === 'assistant') {
    router.push('/assistant')
  } else if (module === 'risk') {
    router.push('/risk-center')
  } else if (module === 'system') {
    if (userRole.value !== 'ADMIN') {
      ElMessage.error('权限不足')
      return
    }
    router.push('/system')
  }
}
</script>

<style scoped>
.home-view {
  min-height: 100vh;
}

.welcome-section {
  background-color: #fff;
  border-radius: 8px;
  padding: 24px 32px;
  margin-bottom: 24px;
}

.welcome-title {
  font-size: 24px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 8px;
}

.welcome-desc {
  font-size: 14px;
  color: #909399;
}
</style>
