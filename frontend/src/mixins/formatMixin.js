import dayjs from 'dayjs'

export default {
  methods: {
    formatQuantity(value) {
      if (value == null) return '0.00'
      return Number(value).toLocaleString('zh-CN', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    },
    
    formatCurrency(value, currency = null, decimalPlaces = 2) {
      if (value == null) return '¥0.00'
      
      // Determine currency symbol
      let symbol = '¥' // Default to Chinese Yuan
      if (currency && currency.symbol) {
        symbol = currency.symbol
      }
      
      return symbol + Number(value).toLocaleString('zh-CN', {
        minimumFractionDigits: decimalPlaces,
        maximumFractionDigits: decimalPlaces
      })
    },
    
    formatDate(date) {
      if (!date) return ''
      return dayjs(date).format('YYYY-MM-DD')
    },
    
    formatPercentage(value) {
      if (value == null) return '0.00%'
      return Number(value).toFixed(2) + '%'
    }
  }
}