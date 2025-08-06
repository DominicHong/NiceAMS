<template>
  <div class="assets">
    <div class="page-header">
      <h2>Asset Management</h2>
      <el-button type="primary" @click="openAddDialog">Add Asset</el-button>
    </div>
    
    <el-card>
      <el-table :data="assets" style="width: 100%" v-loading="loading">
        <el-table-column prop="symbol" label="Symbol" width="100" />
        <el-table-column prop="name" label="Name" />
        <el-table-column prop="type" label="Type" width="100" />
        <el-table-column prop="isin" label="ISIN" />
        <el-table-column label="Actions" width="180">
          <template #default="scope">
            <el-button size="small" type="primary" @click="editAsset(scope.row)">Edit</el-button>
            <el-button size="small" type="danger" @click="deleteAsset(scope.row)">Delete</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
    
    <!-- Add/Edit Asset Dialog -->
    <el-dialog v-model="showDialog" :title="dialogTitle" width="500px">
      <el-form :model="assetForm" ref="assetFormRef" :rules="assetRules">
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
        <el-button @click="showDialog = false">Cancel</el-button>
        <el-button type="primary" @click="saveAsset">{{ isEditMode ? 'Update' : 'Save' }}</el-button>
      </template>
    </el-dialog>

    <!-- Delete Confirmation Dialog -->
    <el-dialog v-model="showDeleteDialog" title="Confirm Delete" width="400px">
      <p>Are you sure you want to delete the asset "{{ assetToDelete?.name }}"?</p>
      <p>This action cannot be undone.</p>
      <template #footer>
        <el-button @click="showDeleteDialog = false">Cancel</el-button>
        <el-button type="danger" @click="confirmDelete">Delete</el-button>
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
const showDialog = ref(false)
const showDeleteDialog = ref(false)
const isEditMode = ref(false)
const editingAssetId = ref(null)
const assetToDelete = ref(null)
const assetFormRef = ref()

const assetForm = ref({
  symbol: '',
  name: '',
  type: 'stock',
  isin: '',
  currency_id: 1
})

const assetRules = {
  symbol: [{ required: true, message: 'Please input symbol', trigger: 'blur' }],
  name: [{ required: true, message: 'Please input name', trigger: 'blur' }],
  type: [{ required: true, message: 'Please select type', trigger: 'change' }],
  currency_id: [{ required: true, message: 'Please select currency', trigger: 'change' }]
}

// Computed properties from store
const assets = computed(() => store.assets)
const currencies = computed(() => store.currencies)
const loading = computed(() => store.loading)

const dialogTitle = computed(() => isEditMode.value ? 'Edit Asset' : 'Add Asset')

// Methods
const resetAssetForm = () => {
  assetForm.value = {
    symbol: '',
    name: '',
    type: 'stock',
    isin: '',
    currency_id: 1
  }
  isEditMode.value = false
  editingAssetId.value = null
}

const openAddDialog = () => {
  resetAssetForm()
  showDialog.value = true
}

const editAsset = (asset) => {
  isEditMode.value = true
  editingAssetId.value = asset.id
  assetForm.value = {
    symbol: asset.symbol,
    name: asset.name,
    type: asset.type,
    isin: asset.isin || '',
    currency_id: asset.currency_id
  }
  showDialog.value = true
}

const saveAsset = async () => {
  try {
    await assetFormRef.value.validate()
    
    if (isEditMode.value) {
      await store.updateAsset(editingAssetId.value, assetForm.value)
      ElMessage.success('Asset updated successfully')
    } else {
      await store.createAsset(assetForm.value)
      ElMessage.success('Asset created successfully')
    }
    
    showDialog.value = false
    resetAssetForm()
  } catch (error) {
    if (error.message) {
      ElMessage.error(error.message)
    }
  }
}

const deleteAsset = (asset) => {
  assetToDelete.value = asset
  showDeleteDialog.value = true
}

const confirmDelete = async () => {
  try {
    await store.deleteAsset(assetToDelete.value.id)
    showDeleteDialog.value = false
    assetToDelete.value = null
    ElMessage.success('Asset deleted successfully')
  } catch (error) {
    ElMessage.error('Failed to delete asset')
  }
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