<template>
  <div class="predict-view">
    <AppHeader title="空气质量因子预测" show-back />

    <main class="main-content">
      <div class="section-card">
        <div class="section-title">🔮 预测参数</div>
        <el-form :model="form" label-width="100px">
          <el-row :gutter="20">
            <el-col :xs="24" :sm="12">
              <el-form-item label="城市" required>
                <el-select v-model="form.city" placeholder="请选择城市" style="width: 100%">
                  <el-option v-for="city in cities" :key="city" :label="city" :value="city" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="12">
              <el-form-item label="空气因子" required>
                <el-select
                  v-model="form.factors"
                  multiple
                  collapse-tags
                  collapse-tags-tooltip
                  placeholder="请选择一个或多个因子"
                  style="width: 100%"
                >
                  <el-option
                    v-for="factor in factorOptions"
                    :key="factor.value"
                    :label="factor.label"
                    :value="factor.value"
                  />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
          <div class="form-actions">
            <el-button type="success" :loading="predicting" :disabled="!canPredict" @click="modelPredict">
              {{ predicting ? '模型预测中...' : '模型预测' }}
            </el-button>
            <el-button @click="resetForm">重置</el-button>
          </div>
        </el-form>
      </div>

      <div v-if="progressVisible" class="section-card progress-card">
        <div class="progress-head">
          <div>
            <div class="progress-title">{{ progressTitle }}</div>
            <div class="progress-desc">{{ progressDescription }}</div>
          </div>
          <span class="progress-value">{{ progressPercent }}%</span>
        </div>
        <el-progress :percentage="progressPercent" :status="progressStatus" />
      </div>

      <div v-if="resultRows.length > 0" class="section-card">
        <div class="section-title">📈 预测结果</div>
        <div class="result-meta">
          <span>城市：{{ resultMeta.city }}</span>
          <span>起始日期：{{ resultMeta.startDate }}</span>
          <span>预测天数：{{ resultMeta.horizonDays }}</span>
          <span v-if="resultMeta.source">{{ formatSource(resultMeta.source) }}</span>
          <span v-if="resultMeta.historyDaysUsed">历史样本：{{ resultMeta.historyDaysUsed }} 天</span>
        </div>
        <div v-if="resultMeta.statusMessage" class="status-message">
          {{ resultMeta.statusMessage }}
        </div>
        <div v-if="resultFiles.length > 0" class="result-files">
          <span v-for="file in resultFiles" :key="file.factor" class="result-file">
            {{ formatFactor(file.factor) }}：{{ file.fileName }}（{{ file.predictionTime || file.lastModified }}）
          </span>
        </div>

        <el-table :data="resultRows" stripe style="width: 100%">
          <el-table-column prop="date" label="日期" width="130" />
          <el-table-column
            v-for="factor in resultMeta.factors"
            :key="factor"
            :prop="factor"
            :label="formatFactor(factor)"
            min-width="120"
          />
        </el-table>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'
import AppHeader from '@/components/AppHeader.vue'
import request from '@/utils/request'

const cities = ['宜春', '南昌', '九江', '赣州', '吉安', '上饶', '抚州', '景德镇', '萍乡', '新余', '鹰潭']
const factorOptions = [
  { label: 'AQI', value: 'AQI' },
  { label: 'PM2.5', value: 'PM25' },
  { label: 'PM10', value: 'PM10' },
  { label: 'SO2', value: 'SO2' },
  { label: 'NO2', value: 'NO2' },
  { label: 'CO', value: 'CO' },
  { label: 'O3', value: 'O3' }
]

const form = ref({
  city: '宜春',
  factors: ['AQI']
})

const predicting = ref(false)
const progressVisible = ref(false)
const progressPercent = ref(0)
const progressTitle = ref('')
const progressDescription = ref('')
const progressStatus = ref('')
let progressTimers = []
const resultMeta = ref({
  city: '',
  factors: [],
  startDate: '',
  horizonDays: 7,
  historyDaysUsed: 0,
  source: '',
  statusMessage: ''
})
const resultRows = ref([])
const resultFiles = ref([])

const canPredict = computed(() => form.value.city && form.value.factors.length > 0)

const factorLabelMap = {
  AQI: 'AQI',
  PM25: 'PM2.5',
  PM10: 'PM10',
  SO2: 'SO2',
  NO2: 'NO2',
  CO: 'CO',
  O3: 'O3'
}

const formatFactor = (factor) => factorLabelMap[factor] || factor
const formatSource = (source) => source === 'result-files' ? '来源：现有结果文件' : '来源：模型预测'

const clearProgressTimers = () => {
  progressTimers.forEach(timer => clearTimeout(timer))
  progressTimers = []
}

const setProgress = (percent, title, description, status = '') => {
  progressPercent.value = percent
  progressTitle.value = title
  progressDescription.value = description
  progressStatus.value = status
}

const startProgress = () => {
  clearProgressTimers()
  progressVisible.value = true
  setProgress(8, '检查预测结果文件', '正在判断所选因子是否已有完整 7 天预测结果')
  progressTimers.push(setTimeout(() => {
    setProgress(32, '判断模型有效期', '正在检查结果文件中的模型训练时间和预测日期')
  }, 600))
  progressTimers.push(setTimeout(() => {
    setProgress(58, '调用模型预测接口', '结果不足或模型过期时，系统会调用 Python 模型服务')
  }, 1400))
  progressTimers.push(setTimeout(() => {
    setProgress(76, '模型已过期，正在重新训练中', '如所选模型超过有效期，系统会先重新训练，再生成预测结果')
  }, 3200))
}

const finishProgress = (data) => {
  clearProgressTimers()
  const retrained = data.retrainedFactors?.length > 0
  if (retrained) {
    setProgress(100, '模型已过期，重新训练完成', `${data.retrainedFactors.map(formatFactor).join('、')} 已完成训练并生成预测结果`, 'success')
  } else if (data.source === 'result-files') {
    setProgress(100, '已有完整预测结果', '已直接读取现有 7 天预测结果文件', 'success')
  } else {
    setProgress(100, '模型预测完成', '已生成并读取最新预测结果', 'success')
  }
}

const applyPredictData = (data) => {
  resultMeta.value = {
    city: data.city || form.value.city,
    factors: data.factors || form.value.factors,
    startDate: data.startDate || '',
    horizonDays: data.horizonDays || 7,
    historyDaysUsed: data.historyDaysUsed || 0,
    source: data.source || '',
    statusMessage: data.statusMessage || ''
  }
  resultRows.value = data.predictions || []
  resultFiles.value = data.resultFiles || []

  if (data.missingFactors?.length) {
    ElMessage.warning(`部分因子暂无结果文件：${data.missingFactors.map(formatFactor).join('、')}`)
  }
}

const modelPredict = async () => {
  if (!canPredict.value) {
    ElMessage.warning('请选择城市和空气因子')
    return
  }

  predicting.value = true
  startProgress()
  try {
    const response = await request.post('/predict/air-quality', {
      city: form.value.city,
      factors: form.value.factors
    }, {
      timeout: 120000
    })

    if (response.code !== 200 || !response.data) {
      clearProgressTimers()
      setProgress(100, '模型预测失败', response.message || '预测失败', 'exception')
      ElMessage.error(response.message || '预测失败')
      return
    }

    finishProgress(response.data)
    applyPredictData(response.data)
    ElMessage.success(response.data.statusMessage || '模型预测完成')
  } catch (error) {
    console.error('预测失败:', error)
    clearProgressTimers()
    setProgress(100, '模型预测失败', '请确认 Java 后端和 Python 模型服务是否正常启动', 'exception')
  } finally {
    predicting.value = false
  }
}

const resetForm = () => {
  form.value = {
    city: '宜春',
    factors: ['AQI']
  }
  resultRows.value = []
  resultMeta.value = {
    city: '',
    factors: [],
    startDate: '',
    horizonDays: 7,
    historyDaysUsed: 0,
    source: '',
    statusMessage: ''
  }
  resultFiles.value = []
  progressVisible.value = false
  progressPercent.value = 0
  clearProgressTimers()
}
</script>

<style scoped>
.predict-view {
  min-height: 100vh;
}

.result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 12px;
  font-size: 13px;
  color: #606266;
}

.progress-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.progress-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.progress-desc {
  margin-top: 4px;
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.progress-value {
  flex: 0 0 auto;
  font-size: 18px;
  font-weight: 700;
  color: #409eff;
}

.status-message {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-left: 3px solid #67c23a;
  background: #f0f9eb;
  color: #3f6b2a;
  font-size: 13px;
  line-height: 1.5;
}

.result-files {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.result-file {
  max-width: 100%;
  padding: 6px 10px;
  border: 1px solid #dcdfe6;
  border-radius: 6px;
  background: #f8fafc;
  color: #606266;
  font-size: 12px;
  overflow-wrap: anywhere;
}
</style>
