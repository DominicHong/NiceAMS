# Portfolio Tracker (资产管理系统)

A comprehensive portfolio tracking and asset management system built with Vue.js + FastAPI + SQLModel + SQLite.

## Features

### Core Features
- **Multi-currency Support**: Track assets in CNY, USD, HKD, EUR with automatic currency conversion
- **Portfolio Management**: Comprehensive portfolio tracking with holdings, transactions, and performance metrics
- **Transaction Processing**: Support for buy/sell/dividends/splits/cash flows with CSV import
- **Real-time Pricing**: Integration with price APIs and manual price updates
- **Advanced Analytics**: Time-Weighted Return (TWR), Sharpe ratio, max drawdown, volatility calculations
- **Asset Allocation**: Visual breakdown by asset type and sector
- **Multi-asset Support**: Stocks, bonds, funds, ETFs, cash, and other instruments

### Technical Features
- **Frontend**: Vue.js 3 + Element Plus UI + Chart.js for visualizations
- **Backend**: FastAPI + SQLModel + SQLite for robust data management
- **Architecture**: Clean separation of frontend/backend with RESTful APIs
- **Database**: SQLite for local deployment with comprehensive data models
- **CSV Import/Export**: Batch transaction and price data management

## Project Structure

```
NiceAMS/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── models.py            # SQLModel database models
│   ├── services.py          # Business logic and calculations
│   ├── init_data.py         # Database initialization with sample data
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── main.js          # Vue.js application entry
│   │   ├── App.vue          # Main application component
│   │   ├── router/          # Vue Router configuration
│   │   ├── store/           # Vuex state management
│   │   └── views/           # Vue components
│   ├── public/
│   └── package.json         # Node.js dependencies
└── README.md
```

## Installation & Setup

### Prerequisites
- Python 3.9+
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Install Python dependencies**:
```bash
cd backend
pip install -r requirements.txt
```

2. **Initialize database with sample data**:
```bash
python init_data.py
```

3. **Start the FastAPI server**:
```bash
uvicorn main:app --reload
```

The backend API will be available at `http://localhost:8000`

### Frontend Setup

1. **Install Node.js dependencies**:
```bash
cd frontend
npm install
```

2. **Start the development server**:
```bash
npm run serve
```

The frontend will be available at `http://localhost:8080`

## Usage

### Dashboard
- **Portfolio Overview**: Total value, unrealized P&L, asset count, and performance metrics
- **Performance Chart**: Interactive time-series chart with 1M/3M/6M/1Y/All time ranges
- **Asset Allocation**: Pie chart showing distribution by asset type
- **Top Holdings**: List of largest positions with current values and P&L
- **Recent Transactions**: Latest portfolio activity

### Transaction Management
- **Add Transactions**: Manual entry of buy/sell/dividend/cash transactions
- **CSV Import**: Batch import of transaction data
- **Transaction History**: Filterable and sortable transaction list
- **Supported Actions**: buy, sell, cash_in, cash_out, dividends, interest, split, tax

### Portfolio Holdings
- **Current Positions**: Real-time portfolio holdings with market values
- **Unrealized P&L**: Gain/loss calculations for each position
- **Asset Details**: Symbol, name, quantity, current price, market value

### Asset Management
- **Asset Registry**: Maintain database of stocks, bonds, funds, ETFs
- **Multi-currency Assets**: Support for assets in different currencies
- **Metadata Support**: Sector classification and custom attributes

### Analytics & Reporting
- **Performance Metrics**: TWR, annualized returns, volatility, Sharpe ratio
- **Risk Analysis**: Maximum drawdown, beta, alpha calculations
- **Benchmark Comparison**: Compare portfolio performance against market indices
- **Monthly Returns**: Detailed month-by-month performance breakdown

### Settings
- **Currency Management**: Set primary currency and exchange rates
- **Portfolio Configuration**: Tax rates, benchmark indices, risk-free rates
- **Exchange Rate Updates**: Manual rate updates and CSV import

## API Documentation

The FastAPI backend provides comprehensive REST APIs:

- **Currencies**: `/currencies/` - Currency management
- **Assets**: `/assets/` - Asset registry and metadata
- **Transactions**: `/transactions/` - Transaction CRUD operations
- **Portfolios**: `/portfolios/` - Portfolio management and statistics
- **Import**: `/import/transactions/`, `/import/prices/` - CSV data import
- **Holdings**: `/portfolios/{id}/holdings` - Portfolio positions
- **Statistics**: `/portfolios/{id}/statistics` - Performance metrics

Visit `http://localhost:8000/docs` for interactive API documentation.

## Database Schema

### Core Tables
- **Currency**: Multi-currency support with exchange rates
- **Asset**: Security master with symbols, names, and metadata
- **Transaction**: All portfolio transactions with flexible action types
- **Price**: Historical and real-time price data
- **Portfolio**: Portfolio definitions and configurations
- **Holding**: Current portfolio positions
- **PortfolioStatistics**: Calculated performance metrics

### Transaction Types
- `buy`: Purchase of securities
- `sell`: Sale of securities
- `cash_in`: Cash deposits
- `cash_out`: Cash withdrawals
- `dividends`: Dividend payments
- `interest`: Interest income
- `split`: Stock splits and bonus shares
- `tax`: Tax payments

## CSV Import Format

### Transactions CSV
```csv
trade_date,action,symbol,name,quantity,price,amount,fees,notes
2024-01-15,buy,AAPL,Apple Inc.,100,150.00,15000.00,5.00,Buy Apple shares
2024-01-20,dividends,AAPL,Apple Inc.,,,,120.00,Quarterly dividend
```

### Prices CSV
```csv
symbol,price_date,price
AAPL,2024-01-15,150.00
GOOGL,2024-01-15,2800.00
```

## Performance Calculations

### Time-Weighted Return (TWR)
The system implements proper TWR calculations using the Modified Dietz method, accounting for:
- Cash flows timing
- Portfolio value changes
- Fee adjustments
- Currency conversions

### Risk Metrics
- **Volatility**: Annualized standard deviation of returns
- **Sharpe Ratio**: Risk-adjusted return calculation
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Beta**: Systematic risk relative to benchmark

## Customization

### Adding New Asset Types
1. Update the `Asset` model in `models.py`
2. Add asset type options in the frontend components
3. Implement specific logic in `services.py` if needed

### Adding New Currencies
1. Use the Currency management interface in Settings
2. Add exchange rate data via CSV import or manual entry
3. The system automatically handles currency conversions

### Custom Metadata
Assets support flexible metadata through the `AssetMetadata` model:
```python
# Example: Add sector classification
{
    "match": {"symbol": "AAPL"},
    "apply": {"sector": "Technology"}
}
```

## Contributing

This is a personal portfolio management system. For modifications:

1. **Backend Changes**: Modify models, services, or API endpoints
2. **Frontend Changes**: Update Vue components or add new features
3. **Database Changes**: Create migration scripts for schema updates
4. **Testing**: Add test cases for new functionality

## License

This project is for personal use. Please respect the licenses of third-party dependencies.

## Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review the console logs for error messages
3. Verify database initialization completed successfully
4. Ensure all dependencies are installed correctly

## Architecture Notes

### Design Principles
- **Separation of Concerns**: Clean frontend/backend architecture
- **Data Integrity**: Comprehensive validation and error handling
- **Scalability**: Modular design for easy extension
- **Performance**: Efficient database queries and caching strategies
- **Security**: Input validation and SQL injection prevention

### Technology Choices
- **SQLModel**: Type-safe database operations with Pydantic integration
- **FastAPI**: Modern, fast API framework with automatic documentation
- **Vue.js 3**: Reactive frontend framework with composition API
- **Element Plus**: Professional UI component library
- **Chart.js**: Flexible charting library for financial visualizations

The system is designed for local deployment with SQLite, but can be easily adapted for PostgreSQL or MySQL in production environments. 