<template>
  <div class="analytics">
    <div class="page-header">
      <h2>Portfolio Analytics</h2>
    </div>

    <el-row :gutter="20">
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

<script>
import { useMainStore } from '../stores'
import AllocationChart from '../components/AllocationChart.vue'
import formatMixin from '../mixins/formatMixin'

export default {
  name: 'Analytics',

  components: {
    AllocationChart
  },

  mixins: [formatMixin],

  data() {
    return {
      monthlyReturns: [],
      performanceMetrics: {
        total_return: 0,
        annualized_return: 0,
        volatility: 0,
        sharpe_ratio: 0,
        max_drawdown: 0,
        beta: 0,
        asset_allocation: {},
        message: null
      },
      loading: false,
      performanceLoading: false
    }
  },

  computed: {
    store() {
      return useMainStore()
    },

    assetAllocation() {
      return this.store.assetAllocation || {}
    }
  },

  async created() {
    await this.initializeAnalytics()
  },

  methods: {
    async initializeAnalytics() {
      try {
        await this.store.fetchAssetAllocation(1)
        await Promise.all([
          this.fetchMonthlyReturns(),
          this.fetchPerformanceMetrics()
        ])
      } catch (error) {
        this.$message.error('Failed to load analytics data')
        console.error('Failed to load analytics data:', error)
      }
    },

    async fetchMonthlyReturns() {
      this.loading = true
      try {
        // Fetch monthly returns from backend API
        const response = await fetch('http://localhost:8000/portfolios/1/monthly-returns')
        if (response.ok) {
          this.monthlyReturns = await response.json()
        } else {
          console.error('Failed to fetch monthly returns')
          // Fallback to empty array if API fails
          this.monthlyReturns = []
        }
      } catch (error) {
        console.error('Error fetching monthly returns:', error)
        this.monthlyReturns = []
      } finally {
        this.loading = false
      }
    },

    async fetchPerformanceMetrics() {
      this.performanceLoading = true
      try {
        const response = await fetch('http://localhost:8000/portfolios/1/performance-metrics')
        if (response.ok) {
          this.performanceMetrics = await response.json()
        } else {
          console.error('Failed to fetch performance metrics')
          this.performanceMetrics.message = 'Failed to load performance metrics'
        }
      } catch (error) {
        console.error('Error fetching performance metrics:', error)
        this.performanceMetrics.message = 'Error loading performance metrics'
      } finally {
        this.performanceLoading = false
      }
    },

    formatNumber(value) {
      if (value == null || value === undefined) return '0.00'
      return Number(value).toFixed(2)
    },


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

.el-table {
  font-size: 12px;
}

.el-table th {
  background-color: #f8f9fa;
}
</style>