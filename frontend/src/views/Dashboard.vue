<template>
  <div class="dashboard">
    <!-- Date Range Controls -->
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

    <!-- Portfolio Overview Cards -->
    <el-row :gutter="20" class="overview-cards">
      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-header">
            <el-icon class="card-icon" color="#409EFF">
              <Money />
            </el-icon>
            <span class="card-title">Total Value</span>
          </div>
          <div class="card-value">
            {{ formatCurrency(totalPortfolioValue, { symbol: portfolioSummary?.primary_currency_symbol || '¥' }, 0) }}
          </div>
          <div class="card-change positive">
            <el-icon>
              <TrendCharts />
            </el-icon>
            {{ formatPercentage(totalReturn) }}
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-header">
            <el-icon class="card-icon" color="#67C23A">
              <Trophy />
            </el-icon>
            <span class="card-title">Total P&L</span>
          </div>
          <div class="card-value" :class="totalPnL >= 0 ? 'positive' : 'negative'">
            {{ formatCurrency(totalPnL, { symbol: portfolioSummary?.primary_currency_symbol || '¥' }, 0) }}
          </div>
          <div class="card-change">
            <el-icon>
              <TrendCharts />
            </el-icon>
            Today: {{ formatCurrency(todayChange, { symbol: portfolioSummary?.primary_currency_symbol || '¥' }) }}
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-header">
            <el-icon class="card-icon" color="#E6A23C">
              <Goods />
            </el-icon>
            <span class="card-title">NAV</span>
          </div>
          <div class="card-value">
            {{ formatNumber(store.portfolioStats?.ending_value, 4) }}
          </div>
          <div class="card-change">
            <el-icon>
              <TrendCharts />
            </el-icon>
            Net Asset Value
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-header">
            <el-icon class="card-icon" color="#F56C6C">
              <DataAnalysis />
            </el-icon>
            <span class="card-title">Performance</span>
          </div>
          <div class="card-value">
            {{ formatPercentage(annualizedReturn) }}
          </div>
          <div class="card-change">
            <el-icon>
              <TrendCharts />
            </el-icon>
            Annualized
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Charts and Tables Row -->
    <el-row :gutter="20" class="charts-row">
      <el-col :span="16">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>Portfolio Performance</span>

            </div>
          </template>

          <!-- Portfolio Performance Chart -->
          <div v-if="performanceHistory && performanceHistory.length > 0">
                <PerformanceChart 
                  :performance-history="performanceHistory" 
                  :currency-symbol="portfolioSummary?.primary_currency_symbol || '¥'"
                />
              </div>
              <div v-else class="no-data-message">
                <el-empty description="No performance history data available" :image-size="100"></el-empty>
              </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>Asset Allocation</span>
          </template>
          <AllocationChart 
            :asset-allocation="assetAllocation" 
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- Positions and Transactions Row -->
    <el-row :gutter="20" class="tables-row">
      <el-col :span="14">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>Top Positions</span>
              <el-button link @click="$router.push('/portfolio')">View All</el-button>
            </div>
          </template>

          <SharedDataTable 
            :data="topPositions" 
            :columns="topPositionsColumns" 
            :loading="loading"
          />
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card>
          <template #header>
            <div class="card-header">
              <span>Recent Transactions</span>
              <el-button link @click="$router.push('/transactions')">View All</el-button>
            </div>
          </template>

          <SharedDataTable 
            :data="recentTransactions" 
            :columns="recentTransactionsColumns" 
            :loading="loading"
          >
            <template #symbol="{ row }">
              {{ getAssetSymbol(row.asset_id) }}
            </template>
          </SharedDataTable>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useMainStore } from '../stores'
import { Chart, registerables } from 'chart.js'
import { formatCurrency, formatDate, formatPercentage, formatNumber } from '../utils/formatters.js'
import AllocationChart from '../components/AllocationChart.vue'
import PerformanceChart from '../components/PerformanceChart.vue'
import SharedDataTable from '../components/SharedDataTable.vue'
import { ElMessage } from 'element-plus'

Chart.register(...registerables)

// Store
const store = useMainStore()

// Reactive state
const startDate = ref(null)
const endDate = ref(null)
const timeRange = ref(365)

// Computed properties from store
const positions = computed(() => store.positions)
const loading = computed(() => store.loading)
const currentPortfolio = computed(() => store.currentPortfolio)
const assets = computed(() => store.assets)
const portfolioSummary = computed(() => store.portfolioSummary)
const assetAllocation = computed(() => store.assetAllocation)
const performanceHistory = computed(() => store.performanceHistory)
const recentTransactions = computed(() => store.recentTransactions)

// Derived computed properties
const totalPortfolioValue = computed(() => portfolioSummary.value?.total_market_value_primary || 0)
const totalPnL = computed(() => portfolioSummary.value?.total_pnl_primary || 0)
const todayChange = computed(() => 0) // Placeholder for future implementation
const totalReturn = computed(() => store.portfolioStats?.time_weighted_return || 0)
const annualizedReturn = computed(() => store.portfolioStats?.annualized_return || 0)

const topPositions = computed(() => 
  positions.value
    .sort((a, b) => (b.market_value || 0) - (a.market_value || 0))
    .slice(0, 8)
)

// Define table columns for Top Positions
const topPositionsColumns = computed(() => [
  { prop: 'symbol', label: 'Symbol' },
  { prop: 'name', label: 'Name' },
  { prop: 'quantity', label: 'Quantity', align: 'right', type: 'quantity' },
  { prop: 'current_price', label: 'Price', align: 'right', type: 'currency' },
  { prop: 'market_value', label: 'Market Value', align: 'right', type: 'currency', decimalPlaces: 0 },
  { prop: 'total_pnl', label: 'P&L', align: 'right', type: 'pnl', decimalPlaces: 0 }
])

// Define table columns for Recent Transactions
const recentTransactionsColumns = computed(() => [
  { prop: 'trade_date', label: 'Date', type: 'date' },
  { prop: 'action', label: 'Action', type: 'tag', tagTypeMap: {
      'buy': 'success',
      'sell': 'danger',
      'dividends': 'info',
      'cash_in': 'success',
      'cash_out': 'warning'
    } 
  },
  { prop: 'symbol', label: 'Symbol', type: 'custom' },
  { prop: 'amount', label: 'Amount', align: 'right', type: 'currency' }
])

const hasAllocationData = computed(() => {
  const allocation = store.assetAllocation || {}
  return Object.values(allocation).some(percentage => percentage > 0)
})

// Methods
const getAssetSymbol = (assetId) => {
  if (!assetId || !assets.value) return 'N/A'
  const asset = assets.value.find(a => a.id === assetId)
  return asset ? asset.symbol : 'Unknown'
}

const getActionTagType = (action) => {
  const typeMap = {
    'buy': 'success',
    'sell': 'danger',
    'dividends': 'info',
    'cash_in': 'success',
    'cash_out': 'warning'
  }
  return typeMap[action] || 'info'
}

const initializeDashboard = async () => {
  try {
    await store.fetchPortfolios()
    if (currentPortfolio.value) {
      const portfolioId = currentPortfolio.value.id
      
      // Calculate date range for 1 year (default)
      const today = new Date()
      const oneYearAgo = new Date(today)
      oneYearAgo.setDate(oneYearAgo.getDate() - 365)
      
      // Set default date values
      startDate.value = formatDate(oneYearAgo)
      endDate.value = formatDate(today)
      
      await Promise.all([
        store.fetchPositions(portfolioId),
        store.fetchPortfolioSummary({portfolioId}),
        store.fetchTransactions(),
        store.fetchAssets(),
        store.fetchPerformanceMetrics(portfolioId),
        store.fetchAssetAllocation(portfolioId),
        store.fetchPerformanceHistory(portfolioId, { startDate: startDate.value, endDate: endDate.value })
      ])
    }
  } catch (error) {
    ElMessage.error('Failed to load dashboard data')
    console.error('Failed to load dashboard data:', error)
  }
}

const setTimeRange = async (days) => {
  timeRange.value = days
  console.log('Time range changed to:', days)
  
  const portfolioId = currentPortfolio.value?.id
  if (!portfolioId) {
    console.warn('No portfolio selected')
    return
  }

  // Calculate start and end dates based on days
  const today = new Date()
  let startDateCalc
  
  if (days === 0) {
    // For "ALL" time, use 1 year ago as default
    startDateCalc = new Date(today)
    startDateCalc.setFullYear(startDateCalc.getFullYear() - 1)
  } else {
    startDateCalc = new Date(today)
    startDateCalc.setDate(startDateCalc.getDate() - days)
  }
  
  // Update the reactive date values
  startDate.value = formatDate(startDateCalc)
  endDate.value = formatDate(today)
  
  try {
    console.log('Fetching data for date range:', startDate.value, 'to', endDate.value)
    await Promise.all([
        store.fetchPortfolioSummary({portfolioId, asOfDate: endDate.value}),
        store.fetchAssetAllocation(portfolioId, endDate.value),
        store.fetchPerformanceHistory(portfolioId, { startDate: startDate.value, endDate: endDate.value }),
        store.fetchPerformanceMetrics(portfolioId)
      ])
  } catch (error) {
    console.error('Error fetching dashboard data:', error)
    ElMessage.error('Failed to load dashboard data')
  }
}

const onDateRangeChange = async () => {
  if (startDate.value && endDate.value) {
    const portfolioId = currentPortfolio.value?.id
    if (!portfolioId) {
      console.warn('No portfolio selected')
      return
    }
    
    try {
      console.log('Fetching data for date range:', startDate.value, 'to', endDate.value)
      await Promise.all([
        store.fetchPortfolioSummary({portfolioId, asOfDate: endDate.value}),
        store.fetchAssetAllocation(portfolioId, endDate.value),
        store.fetchPerformanceHistory(portfolioId, { startDate: startDate.value, endDate: endDate.value }),
        store.fetchPerformanceMetrics(portfolioId)
      ])
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
      ElMessage.error('Failed to load dashboard data')
    }
  }
}

// Watchers
watch(currentPortfolio, (newPortfolio, oldPortfolio) => {
  // Ignore initial assignment when oldPortfolio is undefined
  if (oldPortfolio && (newPortfolio?.id !== oldPortfolio.id)) {
    initializeDashboard()
  }
})

// Lifecycle
onMounted(async () => {
  await initializeDashboard()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.date-controls-top {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.date-range-label {
  font-weight: 500;
  color: #606266;
}

.overview-cards {
  margin-bottom: 20px;
}

.overview-card {
  text-align: center;
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 15px;
}

.card-icon {
  font-size: 24px;
  margin-right: 8px;
}

.card-title {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
  margin-bottom: 10px;
}

.card-change {
  font-size: 12px;
  color: #999;
  display: flex;
  align-items: center;
  justify-content: center;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.no-data-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}


.tables-row {
  margin-bottom: 20px;
}

.el-table {
  font-size: 12px;
}

.el-table th {
  background-color: #f8f9fa;
}

.allocation-details {
  margin-top: 15px;
}

.allocation-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 13px;
}

.allocation-label {
  color: #606266;
  font-weight: 500;
}

.allocation-value {
  color: #303133;
  font-weight: 600;
}

.no-data-message {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 200px;
}
</style>