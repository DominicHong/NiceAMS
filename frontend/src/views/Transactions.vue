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
      <el-table :data="filteredTransactions" style="width: 100%" v-loading="loading">
        <el-table-column prop="trade_date" label="Date" width="120" sortable>
          <template #default="scope">
            {{ formatDate(scope.row.trade_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="action" label="Action" width="100">
          <template #default="scope">
            <el-tag :type="getActionTagType(scope.row.action)">
              {{ scope.row.action }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="symbol" label="Symbol" width="100" />
        <el-table-column prop="quantity" label="Quantity" width="100" align="right" />
        <el-table-column prop="price" label="Price" width="100" align="right">
          <template #default="scope">
            {{ formatCurrency(scope.row.price) }}
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="Amount" width="120" align="right">
          <template #default="scope">
            {{ formatCurrency(scope.row.amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="fees" label="Fees" width="100" align="right">
          <template #default="scope">
            {{ formatCurrency(scope.row.fees) }}
          </template>
        </el-table-column>
        <el-table-column prop="notes" label="Notes" />
        <el-table-column label="Actions" width="120">
          <template #default="scope">
            <el-button size="small" @click="editTransaction(scope.row)">Edit</el-button>
            <el-button size="small" type="danger" @click="deleteTransaction(scope.row)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>
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
            <el-form-item label="Symbol" prop="symbol">
              <el-input v-model="transactionForm.symbol" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="Quantity" prop="quantity">
              <el-input-number v-model="transactionForm.quantity" :precision="4" style="width: 100%" />
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
import { mapState, mapActions } from 'vuex'
import dayjs from 'dayjs'

export default {
  name: 'Transactions',
  
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
        symbol: '',
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
        amount: [{ required: true, message: 'Please enter amount', trigger: 'blur' }]
      }
    }
  },
  
  computed: {
    ...mapState(['transactions', 'currencies', 'loading']),
    
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
    ...mapActions(['fetchTransactions', 'createTransaction', 'importTransactions', 'fetchCurrencies']),
    
    async initializeData() {
      try {
        await Promise.all([
          this.fetchTransactions(),
          this.fetchCurrencies()
        ])
      } catch (error) {
        this.$message.error('Failed to load data')
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
        
        await this.createTransaction(this.transactionForm)
        this.showAddDialog = false
        this.resetTransactionForm()
        this.$message.success('Transaction saved successfully')
      } catch (error) {
        this.$message.error('Failed to save transaction')
      }
    },
    
    resetTransactionForm() {
      this.transactionForm = {
        trade_date: null,
        action: '',
        symbol: '',
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
        await this.fetchTransactions()
      } catch (error) {
        this.$message.error('Failed to import transactions')
      }
      return false // Prevent default upload
    },
    
    formatCurrency(value) {
      if (value == null) return '¥0.00'
      return '¥' + Number(value).toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    },
    
    formatDate(date) {
      return dayjs(date).format('YYYY-MM-DD')
    },
    
    getActionTagType(action) {
      const typeMap = {
        'buy': 'success',
        'sell': 'danger',
        'dividends': 'info',
        'cash_in': 'success',
        'cash_out': 'warning',
        'interest': 'info',
        'split': 'warning'
      }
      return typeMap[action] || 'info'
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