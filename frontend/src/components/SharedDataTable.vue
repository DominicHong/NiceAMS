<template>
  <el-table 
    :data="data" 
    style="width: 100%" 
    v-loading="loading"
    :empty-text="emptyText"
    :fit="true"
  >
    <el-table-column 
      v-for="column in columns" 
      :key="column.prop"
      :prop="column.prop"
      :label="column.label"
      :width="column.width"
      :min-width="column.minWidth"
      :align="column.align || 'left'"
      :sortable="column.sortable"
    >
      <template #default="scope">
        <div v-if="column.type === 'date'">
          {{ formatDate(scope.row[column.prop]) }}
        </div>
        <div v-else-if="column.type === 'currency'">
          {{ formatCurrency(scope.row[column.prop], scope.row.currency, column.decimalPlaces !== undefined ? column.decimalPlaces : 2) }}
        </div>
        <div v-else-if="column.type === 'quantity'">
          {{ formatQuantity(scope.row[column.prop]) }}
        </div>
        <div v-else-if="column.type === 'tag'">
          <el-tag :type="getTagType(scope.row[column.prop], column.tagTypeMap)">
            {{ scope.row[column.prop] }}
          </el-tag>
        </div>
        <div v-else-if="column.type === 'pnl'">
          <span :class="scope.row[column.prop] >= 0 ? 'positive' : 'negative'">
            {{ formatCurrency(scope.row[column.prop], scope.row.currency, column.decimalPlaces !== undefined ? column.decimalPlaces : 2) }}
          </span>
        </div>
        <div v-else-if="column.type === 'actions'">
          <el-button 
            v-for="action in column.actions" 
            :key="action.name"
            :size="action.size || 'small'"
            :type="action.type || 'default'"
            @click="emit('action', action.name, scope.row)"
          >
            {{ action.label }}
          </el-button>
        </div>
        <div v-else-if="column.type === 'custom'">
          <slot :name="column.prop" :row="scope.row" :value="scope.row[column.prop]">
            {{ scope.row[column.prop] }}
          </slot>
        </div>
        <div v-else>
          {{ scope.row[column.prop] }}
        </div>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup>
import { formatCurrency, formatDate, formatQuantity } from '../utils/formatters'

// Props definition
const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  columns: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  emptyText: {
    type: String,
    default: 'No data available'
  }
})

// Emits definition
const emit = defineEmits(['action'])

// Methods
const getTagType = (value, tagTypeMap) => {
  if (!tagTypeMap) return 'info'
  return tagTypeMap[value] || 'info'
}
</script>

<style scoped>
.positive {
  color: #67C23A;
}

.negative {
  color: #F56C6C;
}
</style>