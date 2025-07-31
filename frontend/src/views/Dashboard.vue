<template>
  <div class="dashboard">
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
            Today: {{ formatCurrency(todayChange) }}
          </div>
        </el-card>
      </el-col>

      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-header">
            <el-icon class="card-icon" color="#E6A23C">
              <Goods />
            </el-icon>
            <span class="card-title">Assets</span>
          </div>
          <div class="card-value">
            {{ positions.length }}
          </div>
          <div class="card-change">
            <el-icon>
              <List />
            </el-icon>
            Positions
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
              <el-button-group>
                <el-button size="small" @click="setTimeRange(30)" :type="timeRange === 30 ? 'primary' : ''">1M</el-button>
                <el-button size="small" @click="setTimeRange(90)" :type="timeRange === 90 ? 'primary' : ''">3M</el-button>
                <el-button size="small" @click="setTimeRange(180)" :type="timeRange === 180 ? 'primary' : ''">6M</el-button>
                <el-button size="small" @click="setTimeRange(365)" :type="timeRange === 365 ? 'primary' : ''">1Y</el-button>
                <el-button size="small" @click="setTimeRange(0)" :type="timeRange === 0 ? 'primary' : ''">ALL</el-button>
              </el-button-group>
            </div>
          </template>

          <!-- Portfolio Performance Chart -->
          <PerformanceChart 
            :performance-history="performanceHistory" 
            :currency-symbol="portfolioSummary?.primary_currency_symbol || '¥'"
          />
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

          <el-table :data="topPositions" style="width: 100%">
            <el-table-column prop="symbol" label="Symbol" width="100" />
            <el-table-column prop="name" label="Name" />
            <el-table-column prop="quantity" label="Quantity" align="right" />
            <el-table-column prop="current_price" label="Price" align="right">
              <template #default="scope">
                {{ formatCurrency(scope.row.current_price, scope.row.currency) }}
              </template>
            </el-table-column>
            <el-table-column prop="market_value" label="Market Value" align="right">
              <template #default="scope">
                {{ formatCurrency(scope.row.market_value, scope.row.currency, 0) }}
              </template>
            </el-table-column>
            <el-table-column prop="total_pnl" label="P&L" align="right">
              <template #default="scope">
                <span :class="scope.row.total_pnl >= 0 ? 'positive' : 'negative'">
                  {{ formatCurrency(scope.row.total_pnl, scope.row.currency) }}
                </span>
              </template>
            </el-table-column>
          </el-table>
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

          <el-table :data="recentTransactions" style="width: 100%">
            <el-table-column prop="trade_date" label="Date" width="80">
              <template #default="scope">
                {{ formatDate(scope.row.trade_date) }}
              </template>
            </el-table-column>
            <el-table-column prop="action" label="Action" width="60">
              <template #default="scope">
                <el-tag :type="getActionTagType(scope.row.action)" size="small">
                  {{ scope.row.action }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="symbol" label="Symbol" width="80">
              <template #default="scope">
                {{ getAssetSymbol(scope.row.asset_id) }}
              </template>
            </el-table-column>
            <el-table-column prop="amount" label="Amount" align="right">
              <template #default="scope">
                {{ formatCurrency(scope.row.amount, scope.row.currency) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { useMainStore } from '../stores'
import { Chart, registerables } from 'chart.js'
import dayjs from 'dayjs'
import formatMixin from '../mixins/formatMixin'
import AllocationChart from '../components/AllocationChart.vue'
import PerformanceChart from '../components/PerformanceChart.vue'

Chart.register(...registerables)

export default {
  name: 'Dashboard',

  components: {
    AllocationChart,
    PerformanceChart
  },

  mixins: [formatMixin],

  data() {
    return {
      timeRange: 365
    }
  },

  computed: {
    store() {
      return useMainStore()
    },

    // State from store
    positions() {
      return this.store.positions
    },

    loading() {
      return this.store.loading
    },

    currentPortfolio() {
      return this.store.currentPortfolio
    },

    assets() {
      return this.store.assets
    },

    portfolioSummary() {
      return this.store.portfolioSummary
    },

    assetAllocation() {
      return this.store.assetAllocation
    },

    performanceHistory() {
      return this.store.performanceHistory
    },

    // Getters from store - updated to use portfolioSummary
    totalPortfolioValue() {
      return this.portfolioSummary?.total_market_value_primary || 0
    },

    totalPnL() {
      return this.portfolioSummary?.total_pnl_primary || 0
    },

    todayChange() {
      // This would need to be implemented based on actual data
      return 0
    },

    totalReturn() {
      // This would need to be implemented based on actual data
      return 0
    },

    annualizedReturn() {
      // This would need to be implemented based on actual data
      return 0
    },

    recentTransactions() {
      return this.store.recentTransactions
    },

    topPositions() {
      return this.positions
        .sort((a, b) => (b.market_value || 0) - (a.market_value || 0))
        .slice(0, 8)
    },

    // Check if there's valid allocation data for the chart
    hasAllocationData() {
      const allocation = this.store.assetAllocation || {}
      const hasData = Object.values(allocation).some(percentage => percentage > 0)
      return hasData
    }
  },

  watch: {
    currentPortfolio: {
      handler(newPortfolio, oldPortfolio) {
        // Ignore initial assignment when oldPortfolio is undefined
        if (oldPortfolio && (newPortfolio?.id !== oldPortfolio.id)) {
          this.initializeDashboard()
        }
      }
    }
  },

  async created() {
    await this.initializeDashboard()
  },

  methods: {
    async initializeDashboard() {
      try {
        await this.store.fetchPortfolios()
        if (this.currentPortfolio) {
          const portfolioId = this.currentPortfolio.id
          await Promise.all([
            this.store.fetchPositions(portfolioId),
            this.store.fetchPortfolioSummary({portfolioId}),
            this.store.fetchTransactions(),
            this.store.fetchAssets(),
            this.store.fetchPerformanceMetrics(portfolioId),
            this.store.fetchAssetAllocation(portfolioId),
            this.store.fetchPerformanceHistory(portfolioId, 365)
          ])
        }
      } catch (error) {
        this.$message.error('Failed to load dashboard data')
        console.error('Failed to load dashboard data:', error)
      }
    },



    async setTimeRange(days) {
      this.timeRange = days
      console.log('Time range changed to:', days)
      
      const portfolioId = this.currentPortfolio?.id
      if (!portfolioId) {
        console.warn('No portfolio selected')
        return
      }

      try {
        console.log('Fetching performance history for days:', days)
        await this.store.fetchPerformanceHistory(portfolioId, days)
      } catch (error) {
        console.error('Error fetching performance history:', error)
        this.$message.error('Failed to load performance data')
      }
    },



    getAssetSymbol(assetId) {
      if (!assetId || !this.assets) return 'N/A'
      const asset = this.assets.find(a => a.id === assetId)
      return asset ? asset.symbol : 'Unknown'
    },

    getActionTagType(action) {
      const typeMap = {
        'buy': 'success',
        'sell': 'danger',
        'dividends': 'info',
        'cash_in': 'success',
        'cash_out': 'warning'
      }
      return typeMap[action] || 'info'
    }
  }
}
</script>

<style scoped>
.dashboard {
  padding: 0;
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