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
          <div class="chart-container">
            <canvas ref="performanceChart"></canvas>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card class="chart-card">
          <template #header>
            <span>Asset Allocation</span>
          </template>

          <!-- Asset Allocation Chart -->
          <div class="chart-container">
            <canvas ref="allocationChart" v-show="hasAllocationData"></canvas>
            <div v-show="!hasAllocationData" class="no-data-message">
              <el-empty description="No Position" :image-size="100"></el-empty>
            </div>
          </div>

          <!-- Allocation Details -->
          <div class="allocation-details" v-if="Object.keys(assetAllocation).length > 0">
            <el-divider></el-divider>
            <div class="allocation-item" v-for="(percentage, type) in sortedAllocation" :key="type">
              <span class="allocation-label">{{ formatAllocationType(type) }}:</span>
              <span class="allocation-value">{{ formatPercentage(percentage) }}</span>
            </div>
          </div>
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

Chart.register(...registerables)

export default {
  name: 'Dashboard',

  mixins: [formatMixin],

  data() {
    return {
      performanceChart: null,
      allocationChart: null,
      timeRange: 365,
      todayChange: 0,
      totalReturn: 0,
      annualizedReturn: 0,
      performanceHistory: []
    }
  },

  computed: {
    // Pinia store
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

    // Getters from store - updated to use portfolioSummary
    totalPortfolioValue() {
      return this.portfolioSummary?.total_market_value_primary || 0
    },

    totalPnL() {
      return this.portfolioSummary?.total_pnl_primary || 0
    },

    recentTransactions() {
      return this.store.recentTransactions
    },

    topPositions() {
      return this.positions
        .sort((a, b) => (b.market_value || 0) - (a.market_value || 0))
        .slice(0, 8)
    },

    sortedAllocation() {
      const allocation = this.store.assetAllocation || {}
      return Object.entries(allocation)
        .filter(([_, percentage]) => percentage > 0)
        .sort(([, a], [, b]) => b - a)
        .reduce((obj, [type, percentage]) => {
          obj[type] = percentage
          return obj
        }, {})
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

  beforeUnmount() {
    // Clean up chart instances to prevent memory leaks
    if (this.performanceChart) {
      try {
        this.performanceChart.destroy()
      } catch (e) {
        console.warn('Error destroying performance chart on unmount:', e)
      }
      this.performanceChart = null
    }
    if (this.allocationChart) {
      try {
        this.allocationChart.destroy()
      } catch (e) {
        console.warn('Error destroying allocation chart on unmount:', e)
      }
      this.allocationChart = null
    }
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
            this.store.fetchAssetAllocation(portfolioId)
          ])
          // Fetch initial performance history
          this.performanceHistory = await this.store.fetchPerformanceHistory(portfolioId, 365)
          this.$nextTick(() => {
            this.initializeCharts()
          })
        }
      } catch (error) {
        this.$message.error('Failed to load dashboard data')
      }
    },

    initializeCharts() {
      this.createPerformanceChart()
      this.createAllocationChart()
    },

    createPerformanceChart() {
      const canvas = this.$refs.performanceChart
      if (!canvas) {
        console.warn('Performance chart canvas not found')
        return
      }
      
      const ctx = canvas.getContext('2d')
      if (!ctx) {
        console.warn('Could not get 2D context from performance chart canvas')
        return
      }

      // Real data from performance history
      const { labels, data } = this.preparePerformanceData()
      
      // Don't create chart if no data
      if (labels.length === 0 || data.length === 0) {
        console.warn('No performance data available for chart')
        return
      }

      try {
        // Safely destroy existing chart
        if (this.performanceChart) {
          try {
            this.performanceChart.destroy()
          } catch (e) {
            console.warn('Error destroying previous chart:', e)
          }
          this.performanceChart = null
        }
        this.performanceChart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: labels,
            datasets: [{
              label: 'Portfolio Value',
              data: data,
              borderColor: '#409EFF',
              backgroundColor: 'rgba(64, 158, 255, 0.1)',
              fill: true,
              tension: 0.4,
              pointRadius: 0, // Disable points for better performance
              pointHoverRadius: 0 // Disable hover points for better performance
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false, // Disable animations for better performance
            scales: {
              y: {
                beginAtZero: false,
                ticks: {
                  callback: function (value) {
                    return '¥' + value.toLocaleString()
                  }
                }
              },
              x: {
                ticks: {
                  maxRotation: 0, // Prevent label rotation for better performance
                  autoSkip: true, // Automatically skip labels for better performance
                  maxTicksLimit: 10 // Limit number of x-axis labels
                }
              }
            },
            plugins: {
              legend: {
                display: false
              },
              tooltip: {
                mode: 'index',
                intersect: false
              }
            }
          }
        })
      } catch (error) {
        console.error('Error creating performance chart:', error)
        this.performanceChart = null
      }
    },

    createAllocationChart() {
      const ctx = this.$refs.allocationChart?.getContext('2d')
      if (!ctx) return

      // Destroy existing chart if it exists
      if (this.allocationChart) {
          this.allocationChart.destroy()
      }

      const allocationData = this.getAllocationData()

      // Check if we have valid data
      if (!allocationData.data || allocationData.data.length === 0 ||
        allocationData.data.every(val => val === 0)) {
        return
      }

      try {
        this.allocationChart = new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: allocationData.labels,
            datasets: [{
              data: allocationData.data,
              backgroundColor: [
                '#409EFF',
                '#67C23A',
                '#E6A23C',
                '#F56C6C',
                '#909399',
                '#00c0ef',
                '#ff851b',
                '#605ca8',
                '#d2d6de',
                '#001f3f'
              ],
              borderWidth: 2,
              borderColor: '#fff'
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: {
                position: 'bottom',
                labels: {
                  padding: 20,
                  usePointStyle: true,
                  font: {
                    size: 12
                  }
                }
              },
              tooltip: {
                callbacks: {
                  label: function (context) {
                    const label = context.label || ''
                    const value = context.parsed || 0
                    const total = context.dataset.data.reduce((a, b) => a + b, 0)
                    const percentage = ((value / total) * 100).toFixed(1)
                    return `${label}: ${percentage}%`
                  }
                }
              }
            }
          }
        })
      } catch (error) {
        console.error('Error creating allocation chart:', error)
        // Ensure chart is null on creation failure
        this.allocationChart = null
      }
    },

    preparePerformanceData() {
      // Prepare data for the chart based on performance history and time range
      if (!this.performanceHistory || this.performanceHistory.length === 0) {
        return { labels: [], data: [] }
      }

      // Sort by date
      const sortedData = [...this.performanceHistory].sort((a, b) => 
        new Date(a.date) - new Date(b.date)
      )

      // For large datasets, sample the data to prevent performance issues
      // Only limit data points for "All" time range (0 represents all)
      let sampledData = sortedData;
      if (this.timeRange === 0) {
        const maxDataPoints = 365; // Show up to 1 year of daily data points for "All" time range
        
        if (sortedData.length > maxDataPoints) {
          const step = Math.ceil(sortedData.length / maxDataPoints);
          sampledData = [];
          for (let i = 0; i < sortedData.length; i += step) {
            sampledData.push(sortedData[i]);
          }
        }
      }

      // Extract labels and values
      const labels = sampledData.map(item => 
        dayjs(item.date).format('MM/DD')
      )
      const data = sampledData.map(item => item.value)

      return { labels, data }
    },

    getAllocationData() {
      const allocation = this.store.assetAllocation || {}

      // Filter out zero percentages and sort by value
      const filteredAllocation = Object.entries(allocation)
        .filter(([_, percentage]) => percentage > 0)
        .sort(([, a], [, b]) => b - a)

      if (filteredAllocation.length === 0) {
        // Return empty structure instead of placeholder data
        return {
          labels: [],
          data: []
        }
      }

      // Format labels for display
      const labels = filteredAllocation.map(([type]) => {
        return type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')
      })

      const data = filteredAllocation.map(([_, percentage]) => percentage)

      return { labels, data }
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
        this.performanceHistory = await this.store.fetchPerformanceHistory(portfolioId, days)
        
        // Wait for DOM update then refresh chart
        this.$nextTick(() => {
          setTimeout(() => {
            if (this.$refs.performanceChart && this.$refs.performanceChart.getContext) {
              this.updatePerformanceChart()
            } else {
              console.log('Canvas not ready, creating new chart...')
              this.createPerformanceChart()
            }
          }, 100)
        })
      } catch (error) {
        console.error('Error fetching performance history:', error)
        this.$message.error('Failed to load performance data')
      }
    },



    updatePerformanceChart() {
      console.log('Updating performance chart...')
      
      const canvas = this.$refs.performanceChart
      if (!canvas || !canvas.getContext) {
        console.log('Canvas not ready, will retry...')
        setTimeout(() => this.createPerformanceChart(), 50)
        return
      }

      try {
        const { labels, data } = this.preparePerformanceData()
        console.log('Chart data:', { labels: labels.length, data: data.length })
        
        if (labels.length === 0 || data.length === 0) {
          console.log('No data for chart')
          return
        }

        // Always recreate chart instead of updating to prevent memory leaks
        if (this.performanceChart) {
          try {
            this.performanceChart.destroy()
          } catch (e) {
            // Ignore destroy errors
          }
          this.performanceChart = null
        }
        this.createPerformanceChart()
      } catch (error) {
        console.error('Error updating performance chart:', error)
        // Ensure chart is null on error and recreate
        this.performanceChart = null
        this.createPerformanceChart()
      }
    },

    updateAllocationChart() {
      const allocationData = this.getAllocationData()
      // Check if we have valid data
      const hasValidData = allocationData.data &&
        allocationData.data.length > 0 &&
        !allocationData.data.every(val => val === 0)

      if (!hasValidData) {
        // Destroy existing chart if no valid data
        if (this.allocationChart) {
          try {
            this.allocationChart.destroy()
          } catch (e) {
            // Ignore destroy errors
          }
          this.allocationChart = null
        }
        return
      }

      try {
        // Always recreate chart instead of updating
        if (this.allocationChart) {
          try {
            this.allocationChart.destroy()
          } catch (e) {
            // Ignore destroy errors
          }
          this.allocationChart = null
        }
        this.createAllocationChart()
      } catch (error) {
        console.error('Error updating allocation chart:', error)
        // Ensure chart is null on error
        this.allocationChart = null
      }
    },

    formatPercentage(value) {
      if (value == null) return '0.00%'
      return Number(value).toFixed(2) + '%'
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
    },

    formatAllocationType(type) {
      if (!type) return 'Unknown'
      return type.charAt(0).toUpperCase() + type.slice(1).replace('_', ' ')
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

.chart-container {
  height: 300px;
  position: relative;
}

.tables-row {
  margin-bottom: 20px;
}

.el-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
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