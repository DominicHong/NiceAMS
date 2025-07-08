<template>
  <div class="portfolio">
    <div class="page-header">
      <h2>Portfolio Holdings</h2>
      <el-button 
        type="primary" 
        @click="handleRecalculate"
        :loading="loading"
        size="default"
      >
        Recalculate Holdings
      </el-button>
    </div>
    
    <el-card>
      <div v-if="holdings.length === 0 && !loading" class="empty-state">
        <p>No holdings found. Your portfolio appears to be empty.</p>
        <p>If you have transactions, click "Recalculate Holdings" to generate holdings from your transactions.</p>
      </div>
      
      <el-table v-else :data="holdings" style="width: 100%" v-loading="loading">
        <el-table-column prop="symbol" label="Symbol" width="100" />
        <el-table-column prop="name" label="Name" />
        <el-table-column prop="quantity" label="Quantity" align="right">
          <template #default="scope">
            {{ formatQuantity(scope.row.quantity) }}
          </template>
        </el-table-column>
        <el-table-column prop="current_price" label="Current Price" align="right">
          <template #default="scope">
            {{ formatCurrency(scope.row.current_price) }}
          </template>
        </el-table-column>
        <el-table-column prop="market_value" label="Market Value" align="right">
          <template #default="scope">
            {{ formatCurrency(scope.row.market_value) }}
          </template>
        </el-table-column>
        <el-table-column prop="unrealized_pnl" label="Unrealized P&L" align="right">
          <template #default="scope">
            <span :class="scope.row.unrealized_pnl >= 0 ? 'positive' : 'negative'">
              {{ formatCurrency(scope.row.unrealized_pnl) }}
            </span>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import { ElMessage } from 'element-plus'

export default {
  name: 'Portfolio',
  
  computed: {
    ...mapState(['holdings', 'loading', 'currentPortfolio', 'portfolios'])
  },
  
  async created() {
    await this.initializePortfolio()
  },
  
  methods: {
    ...mapActions(['fetchHoldings', 'recalculateHoldings', 'fetchPortfolios']),
    
    async initializePortfolio() {
      try {
        // If no current portfolio, fetch portfolios first
        if (!this.currentPortfolio) {
          await this.fetchPortfolios()
        }
        
        // Now fetch holdings if we have a current portfolio
        if (this.currentPortfolio) {
          await this.fetchHoldings(this.currentPortfolio.id)
        }
      } catch (error) {
        console.error('Failed to initialize portfolio:', error)
        ElMessage.error('Failed to load portfolio data')
      }
    },
    
    async handleRecalculate() {
      if (!this.currentPortfolio) {
        ElMessage.error('No portfolio selected')
        return
      }
      
      try {
        const result = await this.recalculateHoldings(this.currentPortfolio.id)
        ElMessage.success(result.message || 'Holdings recalculated successfully')
        
        // Ensure holdings are refreshed after recalculation
        await this.fetchHoldings(this.currentPortfolio.id)
      } catch (error) {
        ElMessage.error('Failed to recalculate holdings: ' + error.message)
      }
    },

    formatQuantity(value) {
      if (value == null) return '0.00'
      return Number(value).toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    },
    
    formatCurrency(value) {
      if (value == null) return '¥0.00'
      return '¥' + Number(value).toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    }
  }
}
</script>

<style scoped>
.portfolio {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

.empty-state p {
  margin: 10px 0;
}

.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}

.el-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}
</style> 