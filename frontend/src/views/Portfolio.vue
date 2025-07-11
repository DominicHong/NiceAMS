<template>
  <div class="portfolio">
    <div class="page-header">
      <h2>Portfolio Positions</h2>
      <el-button 
        type="primary" 
        @click="handleRecalculate"
        :loading="loading"
        size="default"
      >
        Recalculate Positions
      </el-button>
    </div>
    
    <el-card>
      <div v-if="positions.length === 0 && !loading" class="empty-state">
        <p>No positions found. Your portfolio appears to be empty.</p>
        <p>If you have transactions, click "Recalculate Positions" to generate positions from your transactions.</p>
      </div>
      
      <SharedDataTable 
        v-else
        :data="positions" 
        :columns="tableColumns" 
        :loading="loading"
        empty-text="No positions found. Your portfolio appears to be empty."
      />
    </el-card>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex'
import { ElMessage } from 'element-plus'
import SharedDataTable from '../components/SharedDataTable.vue'
import formatMixin from '../mixins/formatMixin'

export default {
  name: 'Portfolio',
  
  components: {
    SharedDataTable
  },
  
  mixins: [formatMixin],
  
  computed: {
    ...mapState(['positions', 'loading', 'currentPortfolio', 'portfolios']),
    
    tableColumns() {
      return [
        { prop: 'symbol', label: 'Symbol', width: '100' },
        { prop: 'name', label: 'Name' },
        { prop: 'quantity', label: 'Quantity', align: 'right', type: 'quantity' },
        { prop: 'current_price', label: 'Current Price', align: 'right', type: 'currency' },
        { prop: 'market_value', label: 'Market Value', align: 'right', type: 'currency' },
        { prop: 'unrealized_pnl', label: 'Unrealized P&L', align: 'right', type: 'pnl' }
      ]
    }
  },
  
  async created() {
    await this.initializePortfolio()
  },
  
  methods: {
    ...mapActions(['fetchPositions', 'recalculatePositions', 'fetchPortfolios']),
    
    async initializePortfolio() {
      try {
        // If no current portfolio, fetch portfolios first
        if (!this.currentPortfolio) {
          await this.fetchPortfolios()
        }
        
        // Now fetch positions if we have a current portfolio
        if (this.currentPortfolio) {
          await this.fetchPositions(this.currentPortfolio.id)
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
        const result = await this.recalculatePositions(this.currentPortfolio.id)
        ElMessage.success(result.message || 'Positions recalculated successfully')
        
        // Ensure positions are refreshed after recalculation
        await this.fetchPositions(this.currentPortfolio.id)
      } catch (error) {
        ElMessage.error('Failed to recalculate positions: ' + error.message)
      }
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

.el-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}
</style> 