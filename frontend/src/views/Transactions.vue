<template>
  <div class="transactions">
    <div class="page-header">
      <h2>Transaction Management</h2>
      <div class="header-actions">
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          Add Transaction
        </el-button>
        <el-button @click="showImportDialog = true">
          <el-icon><Upload /></el-icon>
          Import CSV
        </el-button>
      </div>
    </div>
    
    <!-- Filters -->
    <el-card class="filter-card">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-select v-model="filters.action" placeholder="Select Action" clearable>
            <el-option label="All Actions" value="" />
            <el-option label="Buy" value="buy" />
            <el-option label="Sell" value="sell" />
            <el-option label="Dividends" value="dividends" />
            <el-option label="Cash In" value="cash_in" />
            <el-option label="Cash Out" value="cash_out" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="To"
            start-placeholder="Start Date"
            end-placeholder="End Date"
            format="YYYY-MM-DD"
          />
        </el-col>
        <el-col :span="6">
          <el-input v-model="filters.symbol" placeholder="Symbol" clearable />
        </el-col>
        <el-col :span="6">
          <el-button type="primary" @click="applyFilters">Filter</el-button>
          <el-button @click="resetFilters">Reset</el-button>
        </el-col>
      </el-row>
    </el-card>
    
    <!-- Transactions Table -->
    <el-card>
      <SharedDataTable 
        :data="filteredTransactions" 
        :columns="tableColumns" 
        :loading="loading"
        @action="handleTableAction"
      >
        <template #symbol="{ row }">
          {{ getAssetSymbol(row.asset_id) }}
        </template>
      </SharedDataTable>
    </el-card>
    
    <!-- Add/Edit Transaction Dialog -->
    <el-dialog v-model="showAddDialog" title="Add Transaction" width="600px">
      <el-form :model="transactionForm" :rules="transactionRules" ref="transactionFormRef">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Date" prop="trade_date">
              <el-date-picker v-model="transactionForm.trade_date" type="date" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Action" prop="action">
              <el-select v-model="transactionForm.action" style="width: 100%">
                <el-option label="Buy" value="buy" />
                <el-option label="Sell" value="sell" />
                <el-option label="Dividends" value="dividends" />
                <el-option label="Cash In" value="cash_in" />
                <el-option label="Cash Out" value="cash_out" />
                <el-option label="Interest" value="interest" />
                <el-option label="Split" value="split" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Asset" prop="asset_id">
              <el-select v-model="transactionForm.asset_id" filterable placeholder="Select Asset" style="width: 100%">
                <el-option
                  v-for="asset in assets"
                  :key="asset.id"
                  :label="asset.symbol + ' - ' + asset.name"
                  :value="asset.id">
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Quantity" prop="quantity">
              <el-input-number v-model="transactionForm.quantity" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Price" prop="price">
              <el-input-number v-model="transactionForm.price" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Amount" prop="amount">
              <el-input-number v-model="transactionForm.amount" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Fees" prop="fees">
              <el-input-number v-model="transactionForm.fees" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Currency" prop="currency_id">
              <el-select v-model="transactionForm.currency_id" style="width: 100%">
                <el-option v-for="currency in currencies" :key="currency.id" :label="currency.code" :value="currency.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="Notes" prop="notes">
          <el-input v-model="transactionForm.notes" type="textarea" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">Cancel</el-button>
        <el-button type="primary" @click="saveTransaction">Save</el-button>
      </template>
    </el-dialog>
    
    <!-- Import Dialog -->
    <el-dialog v-model="showImportDialog" title="Import Transactions" width="500px">
      <el-upload
        class="upload-demo"
        drag
        action=""
        :before-upload="handleImportFile"
        accept=".csv"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          Drop CSV file here or <em>click to upload</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            CSV file with columns: trade_date, action, symbol, quantity, price, amount, fees
          </div>
        </template>
      </el-upload>
      <template #footer>
        <el-button @click="showImportDialog = false">Close</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { useMainStore } from '../stores'
import dayjs from 'dayjs'
import SharedDataTable from '../components/SharedDataTable.vue'
import formatMixin from '../mixins/formatMixin'

export default {
  name: 'Transactions',
  
  components: {
    SharedDataTable
  },
  
  mixins: [formatMixin],
  
  data() {
    return {
      showAddDialog: false,
      showImportDialog: false,
      filters: {
        action: '',
        dateRange: [],
        symbol: ''
      },
      transactionForm: {
        trade_date: null,
        action: '',
        asset_id: null,
        quantity: null,
        price: null,
        amount: null,
        fees: 0,
        currency_id: 1,
        notes: ''
      },
      transactionRules: {
        trade_date: [{ required: true, message: 'Please select date', trigger: 'change' }],
        action: [{ required: true, message: 'Please select action', trigger: 'change' }],
        asset_id: [{ required: true, message: 'Please select an asset', trigger: 'change' }],
        amount: [{ required: true, message: 'Please enter amount', trigger: 'blur' }]
      }
    }
  },
  
  computed: {
    // Pinia store
    store() {
      return useMainStore()
    },
    
    // State from store
    transactions() {
      return this.store.transactions
    },
    
    currencies() {
      return this.store.currencies
    },
    
    loading() {
      return this.store.loading
    },
    
    assets() {
      return this.store.assets
    },
    
    currentPortfolio() {
      return this.store.currentPortfolio
    },
    
    actionTagTypeMap() {
      return {
        'buy': 'success',
        'sell': 'danger',
        'dividends': 'info',
        'cash_in': 'success',
        'cash_out': 'warning',
        'interest': 'info',
        'split': 'warning'
      }
    },
    
    tableColumns() {
      return [
        { prop: 'trade_date', label: 'Date', width: '120', sortable: true, type: 'date' },
        { prop: 'action', label: 'Action', width: '100', type: 'tag', tagTypeMap: this.actionTagTypeMap },
        { prop: 'symbol', label: 'Symbol', width: '100', type: 'custom' },
        { prop: 'quantity', label: 'Quantity', width: '100', align: 'right', type: 'quantity' },
        { prop: 'price', label: 'Price', width: '100', align: 'right', type: 'currency' },
        { prop: 'amount', label: 'Amount', width: '120', align: 'right', type: 'currency' },
        { prop: 'fees', label: 'Fees', width: '100', align: 'right', type: 'currency' },
        { prop: 'notes', label: 'Notes' },
        { 
          prop: 'actions', 
          label: 'Actions', 
          width: '120', 
          type: 'actions',
          actions: [
            { name: 'edit', label: 'Edit', size: 'small' },
            { name: 'delete', label: 'Delete', size: 'small', type: 'danger' }
          ]
        }
      ]
    },
    
    filteredTransactions() {
      let filtered = [...this.transactions]
      
      if (this.filters.action) {
        filtered = filtered.filter(t => t.action === this.filters.action)
      }
      
      if (this.filters.symbol) {
        filtered = filtered.filter(t => t.symbol && t.symbol.toLowerCase().includes(this.filters.symbol.toLowerCase()))
      }
      
      if (this.filters.dateRange && this.filters.dateRange.length === 2) {
        const [startDate, endDate] = this.filters.dateRange
        filtered = filtered.filter(t => {
          const date = dayjs(t.trade_date)
          return date.isAfter(startDate, 'day') && date.isBefore(endDate, 'day')
        })
      }
      
      return filtered.sort((a, b) => dayjs(b.trade_date).valueOf() - dayjs(a.trade_date).valueOf())
    }
  },
  
  async created() {
    await this.initializeData()
  },
  
  methods: {
    async initializeData() {
      try {
        await Promise.all([
          this.store.fetchTransactions(this.currentPortfolio?.id),
          this.store.fetchCurrencies(),
          this.store.fetchAssets()
        ])
      } catch (error) {
        this.$message.error('Failed to load data')
      }
    },
    
    getAssetSymbol(assetId) {
      if (!assetId || !this.assets) return 'N/A'
      const asset = this.assets.find(a => a.id === assetId)
      return asset ? asset.symbol : 'Unknown'
    },

    handleTableAction(actionName, row) {
      if (actionName === 'edit') {
        this.editTransaction(row)
      } else if (actionName === 'delete') {
        this.deleteTransaction(row)
      }
    },

    applyFilters() {
      // Filters are applied via computed property
    },
    
    resetFilters() {
      this.filters = {
        action: '',
        dateRange: [],
        symbol: ''
      }
    },
    
    async saveTransaction() {
      try {
        const valid = await this.$refs.transactionFormRef.validate()
        if (!valid) return
        
        const transactionData = {
          ...this.transactionForm,
          portfolio_id: this.currentPortfolio?.id
        }
        await this.store.createTransaction(transactionData)
        this.showAddDialog = false
        this.resetTransactionForm()
        // Refresh transactions after creating a new one
        await this.store.fetchTransactions(this.currentPortfolio?.id)
        this.$message.success('Transaction saved successfully')
      } catch (error) {
        this.$message.error('Failed to save transaction')
      }
    },
    
    resetTransactionForm() {
      this.transactionForm = {
        trade_date: null,
        action: '',
        asset_id: null,
        quantity: null,
        price: null,
        amount: null,
        fees: 0,
        currency_id: 1,
        notes: ''
      }
    },
    
    editTransaction(transaction) {
      // Implement edit functionality
      this.$message.info('Edit functionality to be implemented')
    },
    
    deleteTransaction(transaction) {
      // Implement delete functionality
      this.$message.info('Delete functionality to be implemented')
    },
    
    async handleImportFile(file) {
      try {
        const result = await this.importTransactions(file)
        this.$message.success(result.message)
        this.showImportDialog = false
        // Refresh both transactions and assets after import
        await Promise.all([
          this.fetchTransactions(this.currentPortfolio?.id),
          this.fetchAssets()
        ])
      } catch (error) {
        this.$message.error('Failed to import transactions')
      }
      return false // Prevent default upload
    }
  }
}
</script>

<style scoped>
.transactions {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-card {
  margin-bottom: 20px;
}

.el-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.upload-demo {
  text-align: center;
}
</style> 