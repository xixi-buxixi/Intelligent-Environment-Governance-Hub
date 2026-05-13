<template>
  <div class="permission-application-view">
    <AppHeader title="权限申请" show-back />

    <main class="main-content">
      <section class="apply-panel">
        <div class="panel-title">
          <h2>申请监测员权限</h2>
          <el-tag :type="currentUserRole === 'USER' ? 'success' : 'info'">
            当前角色：{{ getRoleName(currentUserRole) }}
          </el-tag>
        </div>
        <el-alert
          v-if="currentUserRole !== 'USER'"
          title="当前账号无需提交普通用户权限申请，只有普通用户可以申请升级为监测员。"
          type="info"
          :closable="false"
          show-icon
        />
        <el-form :model="applyForm" label-width="90px" class="apply-form">
          <el-form-item label="申请权限">
            <el-select v-model="applyForm.targetRole" disabled style="width: 220px;">
              <el-option label="监测员" value="MONITOR" />
            </el-select>
          </el-form-item>
          <el-form-item label="申请原因">
            <el-input
              v-model="applyForm.reason"
              type="textarea"
              :rows="5"
              maxlength="500"
              show-word-limit
              placeholder="请说明申请监测员权限的工作场景、职责或使用原因"
              :disabled="currentUserRole !== 'USER'"
            />
          </el-form-item>
          <el-form-item>
            <el-button
              type="success"
              :loading="submitLoading"
              :disabled="currentUserRole !== 'USER'"
              @click="submitApplication"
            >
              提交申请
            </el-button>
          </el-form-item>
        </el-form>
      </section>

      <section class="records-panel">
        <div class="panel-title">
          <h2>处理情况</h2>
          <el-button @click="loadMyApplications">刷新</el-button>
        </div>
        <el-table :data="applicationRecords" stripe v-loading="recordsLoading" style="width: 100%;">
          <el-table-column prop="targetRole" label="申请权限" width="120">
            <template #default="scope">{{ getRoleName(scope.row.targetRole) }}</template>
          </el-table-column>
          <el-table-column prop="reason" label="申请原因" min-width="220" />
          <el-table-column label="状态" width="110">
            <template #default="scope">
              <el-tag :type="getStatusType(scope.row.status)">
                {{ getStatusName(scope.row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="reviewComment" label="处理意见" min-width="180">
            <template #default="scope">{{ scope.row.reviewComment || '-' }}</template>
          </el-table-column>
          <el-table-column prop="reviewerName" label="处理人" width="120">
            <template #default="scope">{{ scope.row.reviewerName || '-' }}</template>
          </el-table-column>
          <el-table-column label="提交时间" width="180">
            <template #default="scope">{{ formatTime(scope.row.createTime) }}</template>
          </el-table-column>
        </el-table>
        <div class="pagination-area">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :total="pagination.total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @size-change="handleSizeChange"
            @current-change="loadMyApplications"
          />
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppHeader from '@/components/AppHeader.vue'
import request from '@/utils/request'

const submitLoading = ref(false)
const recordsLoading = ref(false)
const applicationRecords = ref([])

const applyForm = reactive({
  targetRole: 'MONITOR',
  reason: ''
})

const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

const currentUserRole = computed(() => {
  const userInfo = localStorage.getItem('userInfo')
  if (!userInfo) return ''
  return JSON.parse(userInfo).role || ''
})

const submitApplication = async () => {
  if (!applyForm.reason.trim()) {
    ElMessage.warning('请填写申请原因')
    return
  }

  submitLoading.value = true
  try {
    const response = await request.post('/permission-applications', {
      targetRole: applyForm.targetRole,
      reason: applyForm.reason
    })
    if (response.code === 200) {
      ElMessage.success(response.message || '申请已提交')
      applyForm.reason = ''
      pagination.page = 1
      await loadMyApplications()
    } else {
      ElMessage.error(response.message || '提交失败')
    }
  } catch (error) {
    console.error('提交权限申请失败:', error)
  } finally {
    submitLoading.value = false
  }
}

const loadMyApplications = async () => {
  recordsLoading.value = true
  try {
    const response = await request.get('/permission-applications/my', {
      params: {
        page: pagination.page,
        size: pagination.size
      }
    })
    if (response.code === 200 && response.data) {
      applicationRecords.value = response.data.records || []
      pagination.total = response.data.total || 0
    }
  } catch (error) {
    console.error('读取权限申请记录失败:', error)
  } finally {
    recordsLoading.value = false
  }
}

const handleSizeChange = () => {
  pagination.page = 1
  loadMyApplications()
}

const getRoleName = (role) => {
  const map = {
    ADMIN: '管理员',
    USER: '普通用户',
    MONITOR: '监测员'
  }
  return map[role] || role || '未知'
}

const getStatusName = (status) => {
  const map = {
    PENDING: '待处理',
    APPROVED: '已同意',
    REJECTED: '已拒绝'
  }
  return map[status] || status
}

const getStatusType = (status) => {
  const map = {
    PENDING: 'warning',
    APPROVED: 'success',
    REJECTED: 'danger'
  }
  return map[status] || 'info'
}

const formatTime = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString('zh-CN')
}

onMounted(() => {
  loadMyApplications()
})
</script>

<style scoped>
.permission-application-view {
  min-height: 100vh;
  background-color: var(--bg-color);
}

.apply-panel,
.records-panel {
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 20px;
}

.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.panel-title h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.apply-form {
  max-width: 760px;
}

.pagination-area {
  margin-top: 18px;
  display: flex;
  justify-content: flex-end;
}
</style>
