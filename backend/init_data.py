"""
Initialize the database with sample data for the Portfolio Tracker
"""

from sqlmodel import Session, select, delete
from datetime import date, datetime
from decimal import Decimal

from models import (
    Currency, ExchangeRate, Asset, Portfolio, Transaction, Price,
    AssetMetadata, PortfolioStatistics, Holding,
    create_db_and_tables, drop_db_and_tables, engine
)
from services import TransactionService


def init_currencies():
    """Initialize basic currencies"""
    with Session(engine) as session:
        currencies = [
            Currency(
                code="CNY",
                name="Chinese Yuan",
                symbol="¥",
                is_primary=True
            ),
            Currency(
                code="USD",
                name="US Dollar",
                symbol="$",
                is_primary=False
            ),
            Currency(
                code="HKD",
                name="Hong Kong Dollar",
                symbol="HK$",
                is_primary=False
            ),
            Currency(
                code="EUR",
                name="Euro",
                symbol="€",
                is_primary=False
            )
        ]
        
        session.add_all(currencies)
        session.commit()
        print("Currencies initialized successfully")


def init_exchange_rates():
    """Initialize sample exchange rates"""
    with Session(engine) as session:
        rates = [
            ExchangeRate(
                currency_id=2,  # USD
                rate_date=date(2024, 1, 15),
                rate_to_primary=Decimal('7.2')
            ),
            ExchangeRate(
                currency_id=3,  # HKD
                rate_date=date(2024, 1, 15),
                rate_to_primary=Decimal('0.92')
            ),
            ExchangeRate(
                currency_id=4,  # EUR
                rate_date=date(2024, 1, 15),
                rate_to_primary=Decimal('7.8')
            )
        ]
        
        session.add_all(rates)
        session.commit()
        print("Exchange rates initialized successfully")


def init_assets():
    """Initialize sample assets including cash assets for each currency"""
    with Session(engine) as session:
        assets = [
            # Cash assets for each currency
            Asset(
                symbol="CNY_CASH",
                name="Chinese Yuan Cash",
                asset_type="cash",
                currency_id=1,
                isin="CASH_CNY"
            ),
            Asset(
                symbol="USD_CASH",
                name="US Dollar Cash",
                asset_type="cash",
                currency_id=2,
                isin="CASH_USD"
            ),
            Asset(
                symbol="HKD_CASH",
                name="Hong Kong Dollar Cash",
                asset_type="cash",
                currency_id=3,
                isin="CASH_HKD"
            ),
            Asset(
                symbol="EUR_CASH",
                name="Euro Cash",
                asset_type="cash",
                currency_id=4,
                isin="CASH_EUR"
            ),
            # Stock assets
            Asset(
                symbol="600036.SH",
                name="China Merchants Bank",
                asset_type="stock",
                currency_id=1,
                isin="CNE000001R84"
            ),
            Asset(
                symbol="000858.SZ",
                name="Wuliangye",
                asset_type="stock",
                currency_id=1,
                isin="CNE000001CJ3"
            ),
            Asset(
                symbol="AAPL",
                name="Apple Inc.",
                asset_type="stock",
                currency_id=2,
                isin="US0378331005"
            ),
            Asset(
                symbol="GOOGL",
                name="Alphabet Inc.",
                asset_type="stock",
                currency_id=2,
                isin="US02079K3059"
            ),
            Asset(
                symbol="510300.SH",
                name="CSI 300 ETF",
                asset_type="etf",
                currency_id=1,
                isin="CNE000001234"
            )
        ]
        
        session.add_all(assets)
        session.commit()
        print("Assets initialized successfully")


def init_portfolio():
    """Initialize sample portfolio"""
    with Session(engine) as session:
        portfolio = Portfolio(
            name="My Portfolio",
            description="Personal investment portfolio",
            base_currency_id=1
        )
        
        session.add(portfolio)
        session.commit()
        print("Portfolio initialized successfully")


def init_sample_prices():
    """Initialize sample prices"""
    with Session(engine) as session:
        prices = [
            # Cash assets (always 1.0)
            Price(
                asset_id=1,  # CNY_CASH
                price_date=date(2025, 3, 1),
                price=Decimal('1.0'),
                price_type='historical',
                source='sample'
            ),
            Price(
                asset_id=2,  # USD_CASH
                price_date=date(2025, 3, 1),
                price=Decimal('1.0'),
                price_type='historical',
                source='sample'
            ),
            Price(
                asset_id=3,  # HKD_CASH
                price_date=date(2025, 3, 1),
                price=Decimal('1.0'),
                price_type='historical',
                source='sample'
            ),
            Price(
                asset_id=4,  # EUR_CASH
                price_date=date(2025, 3, 1),
                price=Decimal('1.0'),
                price_type='historical',
                source='sample'
            ),
            # Stock assets
            Price(
                asset_id=5,  # CMB
                price_date=date(2025, 3, 1),
                price=Decimal('35.50'),
                price_type='historical',
                source='sample'
            ),
            Price(
                asset_id=6,  # Wuliangye
                price_date=date(2025, 3, 1),
                price=Decimal('185.20'),
                price_type='historical',
                source='sample'
            ),
            Price(
                asset_id=7,  # Apple
                price_date=date(2025, 3, 1),
                price=Decimal('185.64'),
                price_type='historical',
                source='sample'
            ),
            Price(
                asset_id=8,  # GOOGL
                price_date=date(2025, 3, 1),
                price=Decimal('2800.50'),
                price_type='historical',
                source='sample'
            ),
            Price(
                asset_id=9,  # CSI 300 ETF
                price_date=date(2025, 3, 1),
                price=Decimal('3.85'),
                price_type='historical',
                source='sample'
            )
        ]
        
        session.add_all(prices)
        session.commit()
        print("Sample prices initialized successfully")


def init_sample_transactions():
    """Initialize sample transactions"""
    with Session(engine) as session:
        # Get the portfolio that was created in init_portfolio()
        portfolio = session.exec(select(Portfolio)).first()
        if not portfolio:
            raise ValueError("No portfolio found. Please run init_portfolio() first.")
        
        transactions = [
            # Initial cash deposit (CNY cash asset)
            Transaction(
                portfolio_id=portfolio.id,
                trade_date=date(2025, 1, 1),
                action='cash_in',
                asset_id=1,  # CNY_CASH
                quantity=Decimal('500000'),
                price=Decimal('1.0'),
                amount=Decimal('500000'),
                currency_id=1,
                notes='Initial capital'
            ),
            # Buy CMB
            Transaction(
                portfolio_id=portfolio.id,
                trade_date=date(2025, 1, 5),
                action='buy',
                asset_id=5,  # CMB
                quantity=Decimal('1000'),
                price=Decimal('35.20'),
                amount=Decimal('35200'),
                fees=Decimal('5.28'),
                currency_id=1,
                notes='Buy CMB shares'
            ),
            # Buy Wuliangye
            Transaction(
                portfolio_id=portfolio.id,
                trade_date=date(2025, 1, 8),
                action='buy',
                asset_id=6,  # Wuliangye
                quantity=Decimal('100'),
                price=Decimal('180.50'),
                amount=Decimal('18050'),
                fees=Decimal('2.71'),
                currency_id=1,
                notes='Buy Wuliangye shares'
            ),
            # Start of currency exchange (CNY to USD)
            # Sell CNY
            Transaction(
                portfolio_id=portfolio.id,
                trade_date=date(2025, 1, 9),
                action='cash_out',
                asset_id=1,  # CNY_CASH
                quantity=Decimal('65520'),
                price=Decimal('1.0'),
                amount=Decimal('65520'),
                currency_id=1,
                notes='Currency exchange: Sell CNY'
            ),
            # Buy USD
            Transaction(
                portfolio_id=portfolio.id,
                trade_date=date(2025, 1, 9),
                action='cash_in',
                asset_id=2,  # USD_CASH
                quantity=Decimal('9100'),
                price=Decimal('1.0'),
                amount=Decimal('9100'),
                currency_id=2,
                notes='Currency exchange: Buy USD'
            ),
            # End of cash exchange
            # Buy Apple
            Transaction(
                portfolio_id=portfolio.id,
                trade_date=date(2025, 1, 10),
                action='buy',
                asset_id=7,  # Apple
                quantity=Decimal('50'),
                price=Decimal('182.00'),
                amount=Decimal('9100'),
                fees=Decimal('1.82'),
                currency_id=2,
                notes='Buy Apple shares'
            ),
            # Buy CSI 300 ETF
            Transaction(
                portfolio_id=portfolio.id,
                trade_date=date(2025, 1, 12),
                action='buy',
                asset_id=9,  # CSI 300 ETF
                quantity=Decimal('10000'),
                price=Decimal('3.80'),
                amount=Decimal('38000'),
                fees=Decimal('5.70'),
                currency_id=1,
                notes='Buy CSI 300 ETF'
            )
        ]
        
        session.add_all(transactions)
        session.commit()
        print("Sample transactions initialized successfully")
        
        # Process transactions to create holdings
        print("Processing transactions to create holdings...")
        processed_count = 0
        error_count = 0
        
        for transaction in transactions:
            try:
                # Create a new session for each transaction processing
                # to avoid session conflicts with the main session
                with Session(engine) as tx_session:
                    tx_service = TransactionService(tx_session)
                    result = tx_service.process_transaction(transaction, portfolio.id)
                    print(f"Processed transaction {transaction.id}: {result.get('message', 'Success')}")
                    processed_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error processing transaction {transaction.id}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"Successfully processed {processed_count} transactions and created holdings")
        print(f"Errors encountered: {error_count}")
        
        # Verify holdings were created
        with Session(engine) as verify_session:
            holdings = verify_session.exec(select(Holding)).all()
            print(f"Holdings created: {len(holdings)}")
            for holding in holdings:
                asset = verify_session.get(Asset, holding.asset_id)
                print(f"  {asset.symbol if asset else 'Unknown'}: quantity={holding.quantity}, avg_cost={holding.average_cost}")


def main():
    print("Clearing existing data...")
    drop_db_and_tables()

    print("Creating database and tables...")
    create_db_and_tables()
    
    print("Initializing sample data...")
    init_currencies()
    init_exchange_rates()
    init_assets()
    init_portfolio()
    init_sample_prices()
    init_sample_transactions()
    
    print("\nDatabase initialization completed successfully!")
    print("You can now start the FastAPI server with: uvicorn main:app --reload")


if __name__ == "__main__":
    main() 