<template>
  <div class="analytics">
    <div class="page-header">
      <h2>Portfolio Analytics</h2>
    </div>

    <div class="date-controls-top">
      <div class="date-range-label">From:</div>
      <el-date-picker
        v-model="startDate"
        type="date"
        placeholder="Start date"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
        @change="onDateRangeChange"
      />
      <div class="date-range-label">To:</div>
      <el-date-picker
        v-model="endDate"
        type="date"
        placeholder="End date"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
        @change="onDateRangeChange"
      />
      <el-button-group>
        <el-button :type="timeRange === 30 ? 'primary' : 'default'" @click="setTimeRange(30)">1M</el-button>
        <el-button :type="timeRange === 90 ? 'primary' : 'default'" @click="setTimeRange(90)">3M</el-button>
        <el-button :type="timeRange === 180 ? 'primary' : 'default'" @click="setTimeRange(180)">6M</el-button>
        <el-button :type="timeRange === 365 ? 'primary' : 'default'" @click="setTimeRange(365)">1Y</el-button>
        <el-button :type="timeRange === 0 ? 'primary' : 'default'" @click="setTimeRange(0)">ALL</el-button>
      </el-button-group>
    </div>

    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>Performance History</span>
        </div>
      </template>
      <div v-loading="historyLoading">
        <PerformanceChart 
          :performance-history="performanceHistory" 
          currency-symbol="¥" 
        />
      </div>
      <div v-if="!historyLoading && performanceHistory.length === 0" class="empty-state">
        <p>No performance history data available. Please import some transactions first.</p>
      </div>
    </el-card>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>Performance Metrics</span>
            </div>
          </template>
          <el-descriptions :column="2" border v-loading="performanceLoading">
            <el-descriptions-item label="Total Return">{{ formatPercentage(performanceMetrics.total_return) }}</el-descriptions-item>
            <el-descriptions-item label="Annualized Return">{{ formatPercentage(performanceMetrics.annualized_return) }}</el-descriptions-item>
            <el-descriptions-item label="Volatility">{{ formatPercentage(performanceMetrics.volatility) }}</el-descriptions-item>
            <el-descriptions-item label="Sharpe Ratio">{{ formatNumber(performanceMetrics.sharpe_ratio) }}</el-descriptions-item>
            <el-descriptions-item label="Max Drawdown">{{ formatPercentage(performanceMetrics.max_drawdown) }}</el-descriptions-item>
            <el-descriptions-item label="Beta">{{ formatNumber(performanceMetrics.beta) }}</el-descriptions-item>
          </el-descriptions>
          <div v-if="!performanceLoading && performanceMetrics.message" class="empty-state">
            <p>{{ performanceMetrics.message }}</p>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>Asset Allocation</span>
            </div>
          </template>
          <div v-loading="performanceLoading">
            <AllocationChart :asset-allocation="assetAllocation" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="chart-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>Monthly Returns</span>
        </div>
      </template>
      <el-table :data="monthlyReturns" style="width: 100%" v-loading="loading">
        <el-table-column prop="month" label="Month" width="120" />
        <el-table-column prop="portfolio_return" label="Portfolio Return" align="right">
          <template #default="scope">
            <span :class="scope.row.portfolio_return >= 0 ? 'positive' : 'negative'">
              {{ formatPercentage(scope.row.portfolio_return) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="benchmark_return" label="Benchmark Return" align="right">
          <template #default="scope">
            <span :class="scope.row.benchmark_return >= 0 ? 'positive' : 'negative'">
              {{ formatPercentage(scope.row.benchmark_return) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="alpha" label="Alpha" align="right">
          <template #default="scope">
            <span :class="scope.row.alpha >= 0 ? 'positive' : 'negative'">
              {{ formatPercentage(scope.row.alpha) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
      <div v-if="!loading && monthlyReturns.length === 0" class="empty-state">
        <p>No monthly returns data available. Please import some transactions first.</p>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useMainStore } from '../stores'
import AllocationChart from '../components/AllocationChart.vue'
import PerformanceChart from '../components/PerformanceChart.vue'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'
import { formatPercentage, formatNumber, formatDate } from '../utils/formatters'

// Store
const store = useMainStore()

// Reactive state
const monthlyReturns = ref([])
const performanceMetrics = ref({
  total_return: 0,
  annualized_return: 0,
  volatility: 0,
  sharpe_ratio: 0,
  max_drawdown: 0,
  beta: 0,
  asset_allocation: {},
  message: null
})
const performanceHistory = ref([])
const loading = ref(false)
const performanceLoading = ref(false)
const historyLoading = ref(false)
const startDate = ref(null)
const endDate = ref(null)
const timeRange = ref(365)

// Computed properties
const assetAllocation = computed(() => store.assetAllocation || {})



// Methods converted to functions
const initializeAnalytics = async () => {
  // Set default date range (1 year)
  const endDateObj = new Date()
  const startDateObj = dayjs(endDateObj).subtract(1, 'year').toDate()
  startDate.value = formatDate(startDateObj)
  endDate.value = formatDate(endDateObj)
  
  try {
    // Ensure portfolios are loaded and current portfolio is set
    if (!store.currentPortfolio) {
      await store.fetchPortfolios()
    }
    
    // Check if we have a valid portfolio ID
    if (!store.currentPortfolioId) {
      ElMessage.warning('Please create or select a portfolio first')
      return
    }
    
    await Promise.all([
      store.fetchAssetAllocation(store.currentPortfolioId, endDate.value),
      fetchMonthlyReturns(),
      fetchPerformanceMetrics(),
      fetchPerformanceHistory()
    ])
  } catch (error) {
    ElMessage.error('Failed to load analytics data')
    console.error('Failed to load analytics data:', error)
  }
}

const fetchMonthlyReturns = async () => {
  // Check if we have a valid portfolio ID
  if (!store.currentPortfolioId) {
    monthlyReturns.value = []
    return
  }
  
  loading.value = true
  try {
    // Use the store method to fetch monthly returns
    monthlyReturns.value = await store.fetchMonthlyReturns(store.currentPortfolioId)
  } catch (error) {
    console.error('Error fetching monthly returns:', error)
    monthlyReturns.value = []
    ElMessage.error('Failed to load monthly returns data')
  } finally {
    loading.value = false
  }
}

const fetchPerformanceMetrics = async () => {
  // Check if we have a valid portfolio ID
  if (!store.currentPortfolioId) {
    performanceMetrics.value = {
      total_return: 0,
      annualized_return: 0,
      volatility: 0,
      sharpe_ratio: 0,
      max_drawdown: 0,
      beta: 0,
      asset_allocation: {},
      message: null
    }
    return
  }
  
  performanceLoading.value = true
  try {
    // Use the store method to fetch performance metrics
    performanceMetrics.value = await store.fetchPerformanceMetrics(store.currentPortfolioId)
  } catch (error) {
    console.error('Error fetching performance metrics:', error)
    ElMessage.error('Failed to load performance metrics data')
  } finally {
    performanceLoading.value = false
  }
}

const fetchPerformanceHistory = async (options = null) => {
  // Check if we have a valid portfolio ID
  if (!store.currentPortfolioId) {
    performanceHistory.value = []
    return
  }
  
  historyLoading.value = true
  try {
    // If options is an object with startDate and endDate, use those
    if (options && typeof options === 'object' && options.startDate && options.endDate) {
      performanceHistory.value = await store.fetchPerformanceHistory(store.currentPortfolioId, options)
    }
    // Default fallback - use current startDate and endDate
    else if (startDate.value && endDate.value) {
      performanceHistory.value = await store.fetchPerformanceHistory(store.currentPortfolioId, { 
        startDate: startDate.value, 
        endDate: endDate.value 
      })
    } else {
      // If no dates are set, use a default 1-year range
      const endDateObj = new Date()
      const startDateObj = new Date(endDateObj)
      startDateObj.setDate(startDateObj.getDate() - 365)
      
      // Format dates as YYYY-MM-DD
      const startDateStr = formatDate(startDateObj)
      const endDateStr = formatDate(endDateObj)
      
      performanceHistory.value = await store.fetchPerformanceHistory(store.currentPortfolioId, { 
        startDate: startDateStr, 
        endDate: endDateStr 
      })
    }
  } catch (error) {
    console.error('Error fetching performance history:', error)
    performanceHistory.value = []
    ElMessage.error('Failed to load performance history data')
  } finally {
    historyLoading.value = false
  }
}

const setTimeRange = async (days) => {
  timeRange.value = days
  // Calculate start and end dates based on days
  const endDateObj = new Date()
  let startDateObj
  
  if (days === 0) { // Set startDate to the first date of all transactions
    // Get the earliest transaction date from the store
    if (store.transactions && store.transactions.length > 0) {
      // Sort transactions by date and get the earliest one
      const sortedTransactions = [...store.transactions].sort((a, b) => 
        new Date(a.trade_date) - new Date(b.trade_date)
      )
      startDateObj = new Date(sortedTransactions[0].trade_date)
    } else {
      // Fallback to 365 days if no transactions
      startDateObj = new Date(endDateObj)
      startDateObj.setDate(startDateObj.getDate() - 365)
    }
  } else {
    startDateObj = new Date(endDateObj)
    startDateObj.setDate(startDateObj.getDate() - days)
  }
  
  // Format dates as YYYY-MM-DD
  startDate.value = formatDate(startDateObj)
  endDate.value = formatDate(endDateObj)
  
  await Promise.all([
    store.fetchAssetAllocation(store.currentPortfolioId, endDate.value),
    fetchPerformanceHistory({ startDate: startDate.value, endDate: endDate.value })
  ])
}

const onDateRangeChange = async () => {
  if (startDate.value && endDate.value) {
    await Promise.all([
      store.fetchAssetAllocation(store.currentPortfolioId, endDate.value),
      fetchPerformanceHistory({ startDate: startDate.value, endDate: endDate.value })
    ])
  }
}

// Lifecycle hooks
onMounted(() => {
  console.log('Analytics component mounted')
  initializeAnalytics()
})

// Watchers
watch(
  () => store.currentPortfolio,
  (newPortfolio, oldPortfolio) => {
    // Ignore initial assignment when oldPortfolio is undefined
    if (oldPortfolio && (newPortfolio?.id !== oldPortfolio.id)) {
      initializeAnalytics()
    }
  }
)
</script>

<style scoped>
.analytics {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

.chart-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 15px;
}

.date-controls-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.date-range-label {
  font-weight: 500;
  color: #606266;
}

.date-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.el-table {
  font-size: 12px;
}

.el-table th {
  background-color: #f8f9fa;
}
</style>