<template>
  <div class="analytics">
    <div class="page-header">
      <h2>Portfolio Analytics</h2>
    </div>

    <el-card class="chart-card">
      <template #header>
        <div class="card-header">
          <span>Performance History</span>
          <el-button-group>
            <el-button size="small" @click="setTimeRange(30)" :type="timeRange === 30 ? 'primary' : ''">1M</el-button>
            <el-button size="small" @click="setTimeRange(90)" :type="timeRange === 90 ? 'primary' : ''">3M</el-button>
            <el-button size="small" @click="setTimeRange(180)" :type="timeRange === 180 ? 'primary' : ''">6M</el-button>
            <el-button size="small" @click="setTimeRange(365)" :type="timeRange === 365 ? 'primary' : ''">1Y</el-button>
            <el-button size="small" @click="setTimeRange(0)" :type="timeRange === 0 ? 'primary' : ''">ALL</el-button>
          </el-button-group>
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

<script>
import { useMainStore } from '../stores'
import AllocationChart from '../components/AllocationChart.vue'
import PerformanceChart from '../components/PerformanceChart.vue'
import formatMixin from '../mixins/formatMixin'

export default {
  name: 'Analytics',

  components: {
    AllocationChart,
    PerformanceChart
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
      performanceHistory: [],
      loading: false,
      performanceLoading: false,
      historyLoading: false,
      timeRange: 365 // Default to 1 year
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

  watch: {
    'store.currentPortfolio': {
      handler(newPortfolio, oldPortfolio) {
        // Ignore initial assignment when oldPortfolio is undefined
        if (oldPortfolio && (newPortfolio?.id !== oldPortfolio.id)) {
          this.initializeAnalytics()
        }
      }
    }
  },

  methods: {
    async initializeAnalytics() {
      try {
        // Ensure portfolios are loaded and current portfolio is set
        if (!this.store.currentPortfolio) {
          await this.store.fetchPortfolios()
        }
        
        // Check if we have a valid portfolio ID
        if (!this.store.currentPortfolioId) {
          this.$message.warning('Please create or select a portfolio first')
          return
        }
        
        await this.store.fetchAssetAllocation(this.store.currentPortfolioId)
        await Promise.all([
          this.fetchMonthlyReturns(),
          this.fetchPerformanceMetrics(),
          this.fetchPerformanceHistory(this.timeRange)
        ])
      } catch (error) {
        this.$message.error('Failed to load analytics data')
        console.error('Failed to load analytics data:', error)
      }
    },

    async fetchMonthlyReturns() {
      // Check if we have a valid portfolio ID
      if (!this.store.currentPortfolioId) {
        this.monthlyReturns = []
        return
      }
      
      this.loading = true
      try {
        // Use the store method to fetch monthly returns
        this.monthlyReturns = await this.store.fetchMonthlyReturns(this.store.currentPortfolioId)
      } catch (error) {
        console.error('Error fetching monthly returns:', error)
        this.monthlyReturns = []
        this.$message.error('Failed to load monthly returns data')
      } finally {
        this.loading = false
      }
    },

    async fetchPerformanceMetrics() {
      // Check if we have a valid portfolio ID
      if (!this.store.currentPortfolioId) {
        this.performanceMetrics = {
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
      
      this.performanceLoading = true
      try {
        // Use the store method to fetch performance metrics
        this.performanceMetrics = await this.store.fetchPerformanceMetrics(this.store.currentPortfolioId)
      } catch (error) {
        console.error('Error fetching performance metrics:', error)
        this.$message.error('Failed to load performance metrics data')
      } finally {
        this.performanceLoading = false
      }
    },

    formatNumber(value) {
      if (value == null || value === undefined) return '0.00'
      return Number(value).toFixed(2)
    },

    async fetchPerformanceHistory(days = null) {
      // Check if we have a valid portfolio ID
      if (!this.store.currentPortfolioId) {
        this.performanceHistory = []
        return
      }
      
      this.historyLoading = true
      try {
        const daysToFetch = days !== null ? days : this.timeRange
        this.performanceHistory = await this.store.fetchPerformanceHistory(this.store.currentPortfolioId, daysToFetch)
      } catch (error) {
        console.error('Error fetching performance history:', error)
        this.performanceHistory = []
        this.$message.error('Failed to load performance history data')
      } finally {
        this.historyLoading = false
      }
    },

    async setTimeRange(days) {
      this.timeRange = days
      console.log('Time range changed to:', days)
      
      const portfolioId = this.store.currentPortfolioId
      if (!portfolioId) {
        console.warn('No portfolio selected')
        return
      }

      try {
        console.log('Fetching performance history for days:', days)
        await this.fetchPerformanceHistory(days)
      } catch (error) {
        console.error('Error fetching performance history:', error)
        this.$message.error('Failed to load performance data')
      }
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