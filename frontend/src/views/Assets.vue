<template>
  <div class="assets">
    <div class="page-header">
      <h2>Asset Management</h2>
      <el-button type="primary" @click="showAddDialog = true">Add Asset</el-button>
    </div>
    
    <el-card>
      <el-table :data="assets" style="width: 100%" v-loading="loading">
        <el-table-column prop="symbol" label="Symbol" width="100" />
        <el-table-column prop="name" label="Name" />
        <el-table-column prop="type" label="Type" width="100" />
        <el-table-column prop="isin" label="ISIN" />
        <el-table-column label="Actions" width="120">
          <template #default="scope">
            <el-button size="small" @click="editAsset(scope.row)">Edit</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- Add Asset Dialog -->
    <el-dialog v-model="showAddDialog" title="Add Asset" width="500px">
      <el-form :model="assetForm" ref="assetFormRef">
        <el-form-item label="Symbol" prop="symbol">
          <el-input v-model="assetForm.symbol" />
        </el-form-item>
        <el-form-item label="Name" prop="name">
          <el-input v-model="assetForm.name" />
        </el-form-item>
        <el-form-item label="Type" prop="type">
          <el-select v-model="assetForm.type" style="width: 100%">
            <el-option label="Stock" value="stock" />
            <el-option label="Bond" value="bond" />
            <el-option label="Fund" value="fund" />
            <el-option label="ETF" value="etf" />
            <el-option label="Cash" value="cash" />
          </el-select>
        </el-form-item>
        <el-form-item label="ISIN" prop="isin">
          <el-input v-model="assetForm.isin" />
        </el-form-item>
        <el-form-item label="Currency" prop="currency_id">
          <el-select v-model="assetForm.currency_id" style="width: 100%">
            <el-option v-for="currency in currencies" :key="currency.id" :label="currency.code" :value="currency.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">Cancel</el-button>
        <el-button type="primary" @click="saveAsset">Save</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useMainStore } from '../stores'

// Component name
const name = 'Assets'

// Pinia store
const store = useMainStore()

// Reactive state
const showAddDialog = ref(false)
const assetForm = ref({
  symbol: '',
  name: '',
  type: 'stock',
  isin: '',
  currency_id: 1
})

// Computed properties from store
const assets = computed(() => store.assets)
const currencies = computed(() => store.currencies)
const loading = computed(() => store.loading)

// Methods
const resetAssetForm = () => {
  assetForm.value = {
    symbol: '',
    name: '',
    type: 'stock',
    isin: '',
    currency_id: 1
  }
}

const saveAsset = async () => {
  try {
    await store.createAsset(assetForm.value)
    showAddDialog.value = false
    resetAssetForm()
    ElMessage.success('Asset saved successfully')
  } catch (error) {
    ElMessage.error('Failed to save asset')
  }
}

const editAsset = (asset) => {
  ElMessage.info('Edit functionality to be implemented')
}

// Lifecycle hooks
onMounted(async () => {
  await Promise.all([
    store.fetchAssets(),
    store.fetchCurrencies()
  ])
})
</script>

<style scoped>
.assets {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.el-card {
  border: none;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}
</style>