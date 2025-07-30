<template>
  <div class="analytics">
    <div class="page-header">
      <h2>Portfolio Analytics</h2>
    </div>

    <el-row :gutter="20">
      <el-col :span="12">
        <el-card>
          <template #header>
            <span>Performance Metrics</span>
          </template>
          <el-descriptions :column="2" border v-loading="performanceLoading">
            <el-descriptions-item label="Total Return">{{ formatPercentage(performanceMetrics.total_return)
              }}</el-descriptions-item>
            <el-descriptions-item label="Annualized Return">{{ formatPercentage(performanceMetrics.annualized_return)
              }}</el-descriptions-item>
            <el-descriptions-item label="Volatility">{{ formatPercentage(performanceMetrics.volatility)
              }}</el-descriptions-item>
            <el-descriptions-item label="Sharpe Ratio">{{ formatNumber(performanceMetrics.sharpe_ratio)
              }}</el-descriptions-item>
            <el-descriptions-item label="Max Drawdown">{{ formatPercentage(performanceMetrics.max_drawdown)
              }}</el-descriptions-item>
            <el-descriptions-item label="Beta">{{ formatNumber(performanceMetrics.beta) }}</el-descriptions-item>
          </el-descriptions>
          <div v-if="!performanceLoading && performanceMetrics.message" class="empty-state">
            <p>{{ performanceMetrics.message }}</p>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <template #header>
            <span>Asset Allocation</span>
          </template>
          <div v-loading="performanceLoading">
            <AllocationChart :asset-allocation="assetAllocation" />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>Monthly Returns</span>
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

<script>
import { ref, onMounted, computed } from 'vue'
import { useMainStore } from '../stores'
import AllocationChart from '../components/AllocationChart.vue'

export default {
  name: 'Analytics',

  components: {
    AllocationChart
  },

  setup() {
    const store = useMainStore()
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
    const loading = ref(false)
    const performanceLoading = ref(false)

    const fetchMonthlyReturns = async () => {
      loading.value = true
      try {
        // Fetch monthly returns from backend API
        const response = await fetch('http://localhost:8000/portfolios/1/monthly-returns')
        if (response.ok) {
          monthlyReturns.value = await response.json()
        } else {
          console.error('Failed to fetch monthly returns')
          // Fallback to empty array if API fails
          monthlyReturns.value = []
        }
      } catch (error) {
        console.error('Error fetching monthly returns:', error)
        monthlyReturns.value = []
      } finally {
        loading.value = false
      }
    }

    const fetchPerformanceMetrics = async () => {
      performanceLoading.value = true
      try {
        const response = await fetch('http://localhost:8000/portfolios/1/performance-metrics')
        if (response.ok) {
          performanceMetrics.value = await response.json()
        } else {
          console.error('Failed to fetch performance metrics')
          performanceMetrics.value.message = 'Failed to load performance metrics'
        }
      } catch (error) {
        console.error('Error fetching performance metrics:', error)
        performanceMetrics.value.message = 'Error loading performance metrics'
      } finally {
        performanceLoading.value = false
      }
    }

    const fetchAssetAllocation = async () => {
      try {
        await store.fetchAssetAllocation(1)
      } catch (error) {
        console.error('Error fetching asset allocation:', error)
      }
    }

    const assetAllocation = computed(() => {
      return store.assetAllocation || {}
    })

    const formatPercentage = (value) => {
      if (value == null || value === undefined) return '0.00%'
      return Number(value).toFixed(2) + '%'
    }

    const formatNumber = (value) => {
      if (value == null || value === undefined) return '0.00'
      return Number(value).toFixed(2)
    }

    const formatAssetType = (type) => {
      const typeMap = {
        'stock': 'Stocks',
        'bond': 'Bonds',
        'fund': 'Funds',
        'etf': 'ETFs',
        'cash': 'Cash',
        'crypto': 'Crypto',
        'commodity': 'Commodities'
      }
      return typeMap[type] || type.charAt(0).toUpperCase() + type.slice(1)
    }

    const getProgressStatus = (type) => {
      const statusMap = {
        'stock': 'success',
        'bond': 'warning',
        'fund': 'info',
        'etf': 'info',
        'cash': 'danger',
        'crypto': 'exception',
        'commodity': 'warning'
      }
      return statusMap[type] || 'info'
    }

    onMounted(() => {
      fetchMonthlyReturns()
      fetchPerformanceMetrics()
      fetchAssetAllocation()
    })

    return {
      monthlyReturns,
      performanceMetrics,
      loading,
      performanceLoading,
      assetAllocation,
      formatPercentage,
      formatNumber,
      formatAssetType,
      getProgressStatus
    }
  }
}
</script>

<style scoped>
.analytics {
  padding: 0;
}

.page-header {
  margin-bottom: 20px;
}

.allocation-chart {
  display: flex;
  justify-content: space-around;
  align-items: center;
  flex-wrap: wrap;
  gap: 20px;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

.el-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: #909399;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}
</style>