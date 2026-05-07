<template>
  <div class="risk-center-view">
    <AppHeader title="环境风险智能研判中心" show-back />

    <main class="main-content risk-main">
      <div class="section-card control-section">
        <div class="section-title">风险研判条件</div>
        <el-form :model="form" label-width="96px">
          <el-row :gutter="20">
            <el-col :xs="24" :sm="8">
              <el-form-item label="城市">
                <el-select v-model="form.city" style="width: 100%" @change="loadOverview">
                  <el-option v-for="city in cities" :key="city" :label="city" :value="city" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="16">
              <el-form-item label="关注因子">
                <el-checkbox-group v-model="form.factors" class="factor-checks" @change="loadOverview">
                  <el-checkbox-button v-for="factor in factorOptions" :key="factor.value" :label="factor.value">
                    {{ factor.label }}
                  </el-checkbox-button>
                </el-checkbox-group>
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :xs="24" :sm="10">
              <el-form-item label="研判模式">
                <el-radio-group v-model="form.analysisMode">
                  <el-radio-button label="FAST">快速</el-radio-button>
                  <el-radio-button label="STANDARD">标准</el-radio-button>
                  <el-radio-button label="DEEP">深度</el-radio-button>
                </el-radio-group>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="8">
              <el-form-item label="生成报告">
                <el-switch v-model="form.generateReport" active-text="生成" inactive-text="不生成" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :sm="6">
              <div class="action-row">
                <el-button type="success" :loading="analyzeLoading" :disabled="!canAnalyze" @click="runAnalysis">
                  <el-icon><MagicStick /></el-icon>
                  一键智能研判
                </el-button>
              </div>
            </el-col>
          </el-row>
        </el-form>
      </div>

      <div class="risk-grid">
        <div class="section-card risk-summary">
          <div class="section-title">风险概览</div>
          <div v-if="summary" class="summary-body">
            <div class="risk-level-block" :class="`level-${summaryLevel.toLowerCase()}`">
              <span class="level-label">{{ formatRiskLevel(summaryLevel) }}</span>
              <strong>{{ summary.riskScore ?? '-' }}</strong>
            </div>
            <div class="summary-items">
              <div>
                <span>重点因子</span>
                <strong>{{ summary.keyFactor || '-' }}</strong>
              </div>
              <div>
                <span>置信度</span>
                <strong>{{ formatConfidence(summary.confidence) }}</strong>
              </div>
              <div>
                <span>预警状态</span>
                <strong>{{ summary.alertCreated ? '已触发' : '未触发' }}</strong>
              </div>
            </div>
            <p class="summary-text">{{ summary.trendSummary }}</p>
          </div>
          <el-skeleton v-else :rows="5" animated />
        </div>

        <div class="section-card ai-section">
          <div class="section-title">AI 研判结论</div>
          <template v-if="analysisResult">
            <div class="ai-text">{{ analysisResult.causeExplanation }}</div>
            <div class="suggestion-list">
              <div v-for="item in analysisResult.governanceSuggestions" :key="item" class="suggestion-item">
                {{ item }}
              </div>
            </div>
            <div class="public-advice">{{ analysisResult.publicAdvice }}</div>
          </template>
          <div v-else class="empty-text">点击一键智能研判后生成成因解释和治理建议</div>
        </div>
      </div>

      <div class="section-card">
        <div class="section-title trend-title">
          <span>未来7天趋势</span>
          <span class="trend-subtitle">按日期查看每日环境因子</span>
        </div>
        <div v-loading="overviewLoading" class="trend-days">
          <div v-for="day in trendDays" :key="day.date" class="trend-day-card">
            <div class="trend-day-head">
              <div>
                <strong>{{ formatDateLabel(day.date) }}</strong>
                <span>{{ day.date }}</span>
              </div>
              <el-tag :type="riskTagType(day.riskLevel)" effect="light">
                {{ formatRiskLevel(day.riskLevel) }}
              </el-tag>
            </div>
            <div class="trend-day-meta">
              <span>主因子：{{ formatFactor(day.mainFactor) }}</span>
              <span>评分：{{ day.riskScore }}</span>
              <span :class="{ danger: day.exceedThreshold }">
                {{ day.exceedThreshold ? '存在超限' : '未超限' }}
              </span>
            </div>
            <div class="factor-trend-list">
              <div v-for="item in day.items" :key="`${day.date}-${item.factor}`" class="factor-trend-item">
                <div class="factor-main">
                  <div class="factor-name">{{ formatFactor(item.factor) }}</div>
                  <div class="factor-value">{{ item.predictedValue }}</div>
                  <el-tag :type="riskTagType(item.riskLevel)" effect="plain" size="small">
                    {{ formatRiskLevel(item.riskLevel) }}
                  </el-tag>
                </div>
                <div class="mini-score">
                  <el-progress :percentage="item.riskScore" :stroke-width="7" :show-text="false" />
                  <span>{{ item.riskScore }}%</span>
                </div>
              </div>
            </div>
          </div>
          <div v-if="!overviewLoading && trendDays.length === 0" class="empty-text">暂无趋势数据</div>
        </div>
      </div>

      <div class="section-card" v-if="analysisResult">
        <div class="section-title">风险明细</div>
        <div class="result-meta">
          <span>城市：{{ analysisResult.city }}</span>
          <span>风险日期：{{ analysisResult.riskDates.length ? analysisResult.riskDates.join('、') : '暂无高风险日期' }}</span>
          <span>记录ID：{{ analysisResult.analysisId || '-' }}</span>
        </div>
        <el-table :data="analysisResult.predictions" stripe style="width: 100%">
          <el-table-column prop="date" label="日期" width="130" />
          <el-table-column
            v-for="factor in analysisResult.factors"
            :key="factor"
            :label="formatFactor(factor)"
            min-width="90"
          >
            <template #default="scope">{{ scope.row.values?.[factor] ?? '-' }}</template>
          </el-table-column>
          <el-table-column prop="mainFactor" label="主因子" width="100" />
          <el-table-column label="当日风险" width="110">
            <template #default="scope">
              <el-tag :type="riskTagType(scope.row.dailyRiskLevel)" effect="light">
                {{ formatRiskLevel(scope.row.dailyRiskLevel) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="dailyRiskScore" label="评分" width="90" />
        </el-table>
      </div>

      <div class="section-card">
        <div class="section-title">最近研判记录</div>
        <el-table :data="records" stripe style="width: 100%" v-loading="recordsLoading">
          <el-table-column prop="city" label="城市" width="90" />
          <el-table-column label="风险等级" width="110">
            <template #default="scope">
              <el-tag :type="riskTagType(scope.row.riskLevel)" effect="light">
                {{ formatRiskLevel(scope.row.riskLevel) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="riskScore" label="评分" width="80" />
          <el-table-column prop="keyFactor" label="重点因子" width="100" />
          <el-table-column prop="trendSummary" label="趋势摘要" min-width="260" show-overflow-tooltip />
          <el-table-column prop="createTime" label="研判时间" width="170" />
        </el-table>
        <div v-if="!recordsLoading && records.length === 0" class="empty-text">暂无研判记录</div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
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
  factors: ['AQI', 'PM25', 'PM10', 'O3'],
  analysisMode: 'STANDARD',
  generateReport: true
})

const overview = ref(null)
const analysisResult = ref(null)
const records = ref([])
const overviewLoading = ref(false)
const analyzeLoading = ref(false)
const recordsLoading = ref(false)

const canAnalyze = computed(() => form.value.city && form.value.factors.length > 0)
const summary = computed(() => analysisResult.value || overview.value)
const summaryLevel = computed(() => summary.value?.riskLevel || summary.value?.highestRiskLevel || 'LOW')
const trendRows = computed(() => {
  if (analysisResult.value?.trendItems?.length) {
    return analysisResult.value.trendItems
  }
  if (analysisResult.value?.predictions?.length) {
    return analysisResult.value.predictions.flatMap(day => {
      return analysisResult.value.factors.map(factor => ({
        date: day.date,
        factor,
        predictedValue: day.values?.[factor] ?? '-',
        riskLevel: day.mainFactor === factor ? day.dailyRiskLevel : 'LOW',
        riskScore: day.mainFactor === factor ? day.dailyRiskScore : 0,
        exceedThreshold: day.mainFactor === factor && day.exceedThreshold
      }))
    })
  }
  return overview.value?.trendItems || []
})
const trendDays = computed(() => {
  const byDate = new Map()
  trendRows.value.forEach(row => {
    const date = row.date || '-'
    if (!byDate.has(date)) {
      byDate.set(date, {
        date,
        riskLevel: 'LOW',
        riskScore: 0,
        mainFactor: '-',
        exceedThreshold: false,
        items: []
      })
    }
    const day = byDate.get(date)
    const item = {
      factor: row.factor,
      predictedValue: row.predictedValue ?? '-',
      riskLevel: row.riskLevel || 'LOW',
      riskScore: Number(row.riskScore || 0),
      exceedThreshold: Boolean(row.exceedThreshold)
    }
    day.items.push(item)
    if (item.riskScore >= day.riskScore) {
      day.riskLevel = item.riskLevel
      day.riskScore = item.riskScore
      day.mainFactor = item.factor
    }
    day.exceedThreshold = day.exceedThreshold || item.exceedThreshold
  })
  return Array.from(byDate.values()).map(day => ({
    ...day,
    items: day.items.sort((a, b) => factorOrder(a.factor) - factorOrder(b.factor))
  }))
})

const loadOverview = async () => {
  if (!canAnalyze.value) return
  overviewLoading.value = true
  try {
    const response = await request.get('/risk/overview', {
      params: {
        city: form.value.city,
        factors: form.value.factors.join(','),
        horizonDays: 7
      },
      timeout: 180000
    })
    if (response.code === 200) {
      overview.value = response.data
    } else {
      ElMessage.error(response.message || '风险概览加载失败')
    }
  } catch (error) {
    console.error('风险概览加载失败:', error)
  } finally {
    overviewLoading.value = false
  }
}

const runAnalysis = async () => {
  if (!canAnalyze.value) {
    ElMessage.warning('请选择城市和至少一个空气因子')
    return
  }
  analyzeLoading.value = true
  try {
    const response = await request.post('/risk/analyze', {
      city: form.value.city,
      factors: form.value.factors,
      horizonDays: 7,
      analysisMode: form.value.analysisMode,
      generateReport: form.value.generateReport,
      saveRecord: true
    }, {
      timeout: 240000
    })
    if (response.code === 200) {
      analysisResult.value = response.data
      ElMessage.success('智能研判完成')
      loadRecords()
    } else {
      ElMessage.error(response.message || '智能研判失败')
    }
  } catch (error) {
    console.error('智能研判失败:', error)
  } finally {
    analyzeLoading.value = false
  }
}

const loadRecords = async () => {
  recordsLoading.value = true
  try {
    const response = await request.get('/risk/records', {
      params: { page: 1, size: 5 }
    })
    if (response.code === 200) {
      records.value = response.data?.records || []
    }
  } catch (error) {
    console.error('研判记录加载失败:', error)
  } finally {
    recordsLoading.value = false
  }
}

const formatRiskLevel = (level) => {
  const map = {
    LOW: '低风险',
    MEDIUM: '中风险',
    HIGH: '高风险',
    SEVERE: '严重风险'
  }
  return map[level] || level || '-'
}

const riskTagType = (level) => {
  const map = {
    LOW: 'success',
    MEDIUM: 'warning',
    HIGH: 'danger',
    SEVERE: 'danger'
  }
  return map[level] || 'info'
}

const formatFactor = (factor) => {
  const map = { PM25: 'PM2.5' }
  return map[factor] || factor
}

const factorOrder = (factor) => {
  const order = ['AQI', 'PM25', 'PM10', 'SO2', 'NO2', 'CO', 'O3']
  const index = order.indexOf(factor)
  return index === -1 ? order.length : index
}

const formatDateLabel = (date) => {
  if (!date || date === '-') return '-'
  const parsed = new Date(`${date}T00:00:00`)
  if (Number.isNaN(parsed.getTime())) return date
  const weekday = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][parsed.getDay()]
  return `${parsed.getMonth() + 1}月${parsed.getDate()}日 ${weekday}`
}

const formatConfidence = (value) => {
  if (value === null || value === undefined) return '-'
  return `${Math.round(value * 100)}%`
}

onMounted(() => {
  loadOverview()
  loadRecords()
})
</script>

<style scoped>
.risk-center-view {
  min-height: 100vh;
}

.risk-main {
  max-width: 1280px;
}

.control-section :deep(.el-form-item) {
  margin-bottom: 16px;
}

.factor-checks {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.factor-checks :deep(.el-checkbox-button__inner) {
  border-radius: 6px;
  border-left: 1px solid var(--border-light);
}

.action-row {
  display: flex;
  justify-content: flex-end;
}

.risk-grid {
  display: grid;
  grid-template-columns: minmax(320px, 0.9fr) minmax(360px, 1.1fr);
  gap: 20px;
}

.summary-body {
  display: grid;
  gap: 18px;
}

.risk-level-block {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px;
  border-radius: 8px;
  background-color: #f0f9eb;
  border: 1px solid #d9ecff;
}

.risk-level-block strong {
  font-size: 34px;
  color: var(--text-primary);
}

.level-label {
  font-size: 18px;
  font-weight: 600;
}

.level-low {
  background-color: #f0f9eb;
}

.level-medium {
  background-color: #fdf6ec;
}

.level-high,
.level-severe {
  background-color: #fef0f0;
}

.summary-items {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.summary-items div {
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background-color: #fafafa;
}

.summary-items span {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.summary-items strong {
  font-size: 16px;
  color: var(--text-primary);
}

.summary-text,
.ai-text,
.public-advice {
  line-height: 1.7;
  color: var(--text-regular);
}

.suggestion-list {
  display: grid;
  gap: 10px;
  margin: 14px 0;
}

.suggestion-item {
  padding: 12px 14px;
  border-left: 4px solid var(--primary-color);
  background-color: #f8fbf6;
  border-radius: 6px;
  color: var(--text-regular);
}

.public-advice {
  padding: 12px 14px;
  background-color: #ecf5ff;
  border-radius: 6px;
}

.score-cell {
  display: grid;
  grid-template-columns: 1fr 36px;
  gap: 10px;
  align-items: center;
}

.trend-title {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
}

.trend-subtitle {
  font-size: 13px;
  font-weight: 400;
  color: var(--text-secondary);
}

.trend-days {
  min-height: 120px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 16px;
  align-items: start;
}

.trend-day-card {
  min-width: 0;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background-color: #fff;
  padding: 14px;
  display: grid;
  gap: 12px;
}

.trend-day-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  min-width: 0;
}

.trend-day-head > div {
  min-width: 0;
}

.trend-day-head strong {
  display: block;
  font-size: 17px;
  color: var(--text-primary);
  margin-bottom: 4px;
  overflow-wrap: anywhere;
}

.trend-day-head span {
  font-size: 12px;
  color: var(--text-secondary);
}

.trend-day-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  padding: 8px 10px;
  border-radius: 6px;
  background-color: #f8faf7;
  color: var(--text-secondary);
  font-size: 12px;
}

.factor-trend-list {
  display: grid;
  gap: 8px;
}

.factor-trend-item {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 7px;
  padding: 7px 8px;
  border-radius: 6px;
  background-color: #fafafa;
}

.factor-main {
  min-width: 0;
  display: grid;
  grid-template-columns: minmax(52px, 0.8fr) minmax(56px, 0.8fr) minmax(72px, auto);
  gap: 8px;
  align-items: center;
}

.factor-name {
  font-weight: 600;
  color: var(--text-primary);
  overflow-wrap: anywhere;
}

.factor-value {
  color: var(--text-regular);
  font-variant-numeric: tabular-nums;
  overflow-wrap: anywhere;
}

.mini-score {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 42px;
  gap: 8px;
  align-items: center;
  color: var(--text-secondary);
  font-size: 12px;
  min-width: 0;
}

.danger {
  color: var(--danger-color);
  font-weight: 600;
}

.result-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 12px;
  color: var(--text-secondary);
  font-size: 13px;
}

.empty-text {
  color: var(--text-secondary);
  text-align: center;
  padding: 28px 0;
}

@media (max-width: 900px) {
  .risk-grid {
    grid-template-columns: 1fr;
  }

  .summary-items {
    grid-template-columns: 1fr;
  }

  .action-row {
    justify-content: flex-start;
  }

  .trend-title {
    align-items: flex-start;
    flex-direction: column;
  }

  .factor-trend-item {
    gap: 8px;
  }

  .trend-days {
    grid-template-columns: 1fr;
  }

  .factor-main {
    grid-template-columns: minmax(52px, 0.8fr) minmax(54px, 0.8fr) minmax(70px, auto);
  }
}
</style>
