<template>
  <div class="dashboard">
    <!-- Portfolio Overview Cards -->
    <el-row :gutter="20" class="overview-cards">
      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-header">
            <el-icon class="card-icon" color="#409EFF"><Money /></el-icon>
            <span class="card-title">Total Value</span>
          </div>
          <div class="card-value">
            {{ formatCurrency(totalPortfolioValue, { symbol: portfolioSummary?.primary_currency_symbol || '¥' }) }}
          </div>
          <div class="card-change positive">
            <el-icon><TrendCharts /></el-icon>
            {{ formatPercentage(totalReturn) }}
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-header">
            <el-icon class="card-icon" color="#67C23A"><Trophy /></el-icon>
                          <span class="card-title">Total P&L</span>
          </div>
                          <div class="card-value" :class="totalPnL >= 0 ? 'positive' : 'negative'">
                  {{ formatCurrency(totalPnL, { symbol: portfolioSummary?.primary_currency_symbol || '¥' }) }}
                </div>
          <div class="card-change">
            <el-icon><TrendCharts /></el-icon>
            Today: {{ formatCurrency(todayChange) }}
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-header">
            <el-icon class="card-icon" color="#E6A23C"><Goods /></el-icon>
            <span class="card-title">Assets</span>
          </div>
          <div class="card-value">
            {{ positions.length }}
          </div>
          <div class="card-change">
            <el-icon><List /></el-icon>
            Positions
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="overview-card">
          <div class="card-header">
            <el-icon class="card-icon" color="#F56C6C"><DataAnalysis /></el-icon>
            <span class="card-title">Performance</span>
          </div>
          <div class="card-value">
            {{ formatPercentage(annualizedReturn) }}
          </div>
          <div class="card-change">
            <el-icon><TrendCharts /></el-icon>
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
                <el-button size="small" @click="setTimeRange('1M')">1M</el-button>
                <el-button size="small" @click="setTimeRange('3M')">3M</el-button>
                <el-button size="small" @click="setTimeRange('6M')">6M</el-button>
                <el-button size="small" @click="setTimeRange('1Y')" type="primary">1Y</el-button>
                <el-button size="small" @click="setTimeRange('ALL')">ALL</el-button>
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
            <canvas ref="allocationChart"></canvas>
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
              <el-button type="text" @click="$router.push('/portfolio')">View All</el-button>
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
                {{ formatCurrency(scope.row.market_value, scope.row.currency) }}
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
              <el-button type="text" @click="$router.push('/transactions')">View All</el-button>
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
      timeRange: '1Y',
      todayChange: 0,
      totalReturn: 0,
      annualizedReturn: 0
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
    }
  },
  
  async created() {
    await this.initializeDashboard()
  },
  
  mounted() {
    this.initializeCharts()
  },
  
  methods: {
    async initializeDashboard() {
      try {
        await this.store.fetchPortfolios()
        
        if (this.currentPortfolio) {
          await Promise.all([
            this.store.fetchPositions(this.currentPortfolio.id),
            this.store.fetchPortfolioSummary({ portfolioId: this.currentPortfolio.id }),
            this.store.fetchTransactions(),
            this.store.fetchAssets()
          ])
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
      const ctx = this.$refs.performanceChart.getContext('2d')
      
      // Sample data - replace with actual portfolio performance data
      const labels = this.generateDateLabels()
      const data = this.generateSamplePerformanceData()
      
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
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: false,
              ticks: {
                callback: function(value) {
                  return '¥' + value.toLocaleString()
                }
              }
            }
          },
          plugins: {
            legend: {
              display: false
            }
          }
        }
      })
    },
    
    createAllocationChart() {
      const ctx = this.$refs.allocationChart.getContext('2d')
      
      // Sample data - replace with actual asset allocation data
      const allocationData = this.generateAllocationData()
      
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
              '#909399'
            ]
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom'
            }
          }
        }
      })
    },
    
    generateDateLabels() {
      const labels = []
      const now = dayjs()
      const daysBack = this.timeRange === '1M' ? 30 : 
                      this.timeRange === '3M' ? 90 : 
                      this.timeRange === '6M' ? 180 : 365
      
      for (let i = daysBack; i >= 0; i -= Math.floor(daysBack / 20)) {
        labels.push(now.subtract(i, 'day').format('MM/DD'))
      }
      
      return labels
    },
    
    generateSamplePerformanceData() {
      const data = []
      const baseValue = 100000
      
      for (let i = 0; i < 20; i++) {
        const randomChange = (Math.random() - 0.5) * 0.1
        const value = baseValue * (1 + randomChange * i / 20)
        data.push(value)
      }
      
      return data
    },
    
    generateAllocationData() {
      return {
        labels: ['Stocks', 'Bonds', 'Funds', 'Cash', 'Other'],
        data: [45, 20, 25, 5, 5]
      }
    },
    
    setTimeRange(range) {
      this.timeRange = range
      this.updatePerformanceChart()
    },
    
    updatePerformanceChart() {
      if (this.performanceChart) {
        this.performanceChart.data.labels = this.generateDateLabels()
        this.performanceChart.data.datasets[0].data = this.generateSamplePerformanceData()
        this.performanceChart.update()
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
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
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
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
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
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.el-table {
  font-size: 12px;
}

.el-table th {
  background-color: #f8f9fa;
}
</style> 