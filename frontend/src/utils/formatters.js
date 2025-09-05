import dayjs from 'dayjs'

/**
 * Format a number with fixed decimal places
 * @param {number} value - The number to format
 * @param {number} decimalPlaces - Number of decimal places (default: 2)
 * @returns {string} Formatted number string
 */
export const formatNumber = (value, decimalPlaces = 2) => {
  if (value == null) return '0.00'
  return Number(value).toLocaleString('zh-CN', {
    minimumFractionDigits: decimalPlaces,
    maximumFractionDigits: decimalPlaces
  })
}

/**
 * Format a value as currency with symbol
 * @param {number} value - The currency amount
 * @param {object} currency - Currency object with symbol property
 * @param {number} decimalPlaces - Number of decimal places (default: 2)
 * @returns {string} Formatted currency string
 */
export const formatCurrency = (value, currency = null, decimalPlaces = 2) => {
  if (value == null) return '¥0.00'
  
  // Determine currency symbol
  let symbol = '¥' // Default to Chinese Yuan
  if (currency && currency.symbol) {
    symbol = currency.symbol
  }
  
  return symbol + formatNumber(value, decimalPlaces)
}

/**
 * Format a date as YYYY-MM-DD
 * @param {string|Date} date - The date to format
 * @returns {string} Formatted date string
 */
export const formatDate = (date) => {
  if (!date) return ''
  return dayjs(date).format('YYYY-MM-DD')
}

/**
 * Format a value as percentage
 * @param {number} value - The percentage value (e.g., 0.15 for 15%)
 * @param {number} decimalPlaces - Number of decimal places (default: 2)
 * @returns {string} Formatted percentage string
 */
export const formatPercentage = (value, decimalPlaces = 2) => {
  if (value == null) return '0.00%'
  return (100 * Number(value)).toFixed(decimalPlaces) + '%'
}

/**
 * Format quantity with 2 decimal places
 * @param {number} value - The quantity to format
 * @returns {string} Formatted quantity string
 */
export const formatQuantity = (value) => {
  if (value == null) return '0.00'
  return formatNumber(value, 2)
}