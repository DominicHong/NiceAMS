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
        <el-button @click="setTimeRange(30)">1M</el-button>
        <el-button @click="setTimeRange(90)">3M</el-button>
        <el-button @click="setTimeRange(180)">6M</el-button>
        <el-button @click="setTimeRange(365)">1Y</el-button>
        <el-button @click="setTimeRange(0)">ALL</el-button>
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

<script>
import { useMainStore } from '../stores'
import AllocationChart from '../components/AllocationChart.vue'
import PerformanceChart from '../components/PerformanceChart.vue'
import formatMixin from '../mixins/formatMixin'
import dayjs from 'dayjs'

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
      startDate: null,
      endDate: null
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

  async mounted() {
    console.log('Analytics component mounted')
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
      // Set default date range (1 year)
      const endDate = new Date()
      const startDate = dayjs(endDate).subtract(1, 'year').toDate()
      this.startDate = this.formatDate(startDate)
      this.endDate = this.formatDate(endDate)
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
          this.fetchPerformanceHistory()
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

    async fetchPerformanceHistory(options = null) {
      // Check if we have a valid portfolio ID
      if (!this.store.currentPortfolioId) {
        this.performanceHistory = []
        return
      }
      
      this.historyLoading = true
      try {
        // If options is an object with startDate and endDate, use those
        if (options && typeof options === 'object' && options.startDate && options.endDate) {
          this.performanceHistory = await this.store.fetchPerformanceHistory(this.store.currentPortfolioId, options)
        }
        // Default fallback - use current startDate and endDate
        else if (this.startDate && this.endDate) {
          this.performanceHistory = await this.store.fetchPerformanceHistory(this.store.currentPortfolioId, { 
            startDate: this.startDate, 
            endDate: this.endDate 
          })
        } else {
          // If no dates are set, use a default 1-year range
          const endDate = new Date()
          const startDate = new Date(endDate)
          startDate.setDate(startDate.getDate() - 365)
          
          // Format dates as YYYY-MM-DD using formatMixin
          const startDateStr = this.formatDate(startDate)
          const endDateStr = this.formatDate(endDate)
          
          this.performanceHistory = await this.store.fetchPerformanceHistory(this.store.currentPortfolioId, { 
            startDate: startDateStr, 
            endDate: endDateStr 
          })
        }
      } catch (error) {
        console.error('Error fetching performance history:', error)
        this.performanceHistory = []
        this.$message.error('Failed to load performance history data')
      } finally {
        this.historyLoading = false
      }
    },

    async setTimeRange(days) {
      // Calculate start and end dates based on days
      const endDate = new Date()
      let startDate
      
      if (days === 0) { // Set startDate to the first date of all transactions
        // Get the earliest transaction date from the store
        if (this.store.transactions && this.store.transactions.length > 0) {
          // Sort transactions by date and get the earliest one
          const sortedTransactions = [...this.store.transactions].sort((a, b) => 
            new Date(a.trade_date) - new Date(b.trade_date)
          )
          startDate = new Date(sortedTransactions[0].trade_date)
        } else {
          // Fallback to 365 days if no transactions
          startDate = new Date(endDate)
          startDate.setDate(startDate.getDate() - 365)
        }
      } else {
        startDate = new Date(endDate)
        startDate.setDate(startDate.getDate() - days)
      }
      
      // Format dates as YYYY-MM-DD
      this.startDate = this.formatDate(startDate)
      this.endDate = this.formatDate(endDate)
      
      await this.fetchPerformanceHistory({ startDate: this.startDate, endDate: this.endDate })
    },
    
    async onDateRangeChange() {
      if (this.startDate && this.endDate) {
        await this.fetchPerformanceHistory({ startDate: this.startDate, endDate: this.endDate })
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