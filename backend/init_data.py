"""
Initialize the database with sample data for the Portfolio Tracker
"""

from sqlmodel import Session
from datetime import date, datetime
from decimal import Decimal

from models import (
    Currency, ExchangeRate, Asset, Portfolio, Transaction, Price,
    create_db_and_tables, engine
)


def init_currencies():
    """Initialize basic currencies"""
    with Session(engine) as session:
        # Check if currencies already exist
        existing = session.get(Currency, 1)
        if existing:
            print("Currencies already initialized")
            return
        
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
    """Initialize sample assets"""
    with Session(engine) as session:
        assets = [
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
                symbol="TSLA",
                name="Tesla Inc.",
                asset_type="stock",
                currency_id=2,
                isin="US88160R1014"
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
            # CMB
            Price(
                asset_id=1,
                price_date=date(2024, 1, 15),
                price=Decimal('35.50'),
                price_type='historical',
                source='sample'
            ),
            # Wuliangye
            Price(
                asset_id=2,
                price_date=date(2024, 1, 15),
                price=Decimal('185.20'),
                price_type='historical',
                source='sample'
            ),
            # Apple
            Price(
                asset_id=3,
                price_date=date(2024, 1, 15),
                price=Decimal('185.64'),
                price_type='historical',
                source='sample'
            ),
            # Tesla
            Price(
                asset_id=4,
                price_date=date(2024, 1, 15),
                price=Decimal('219.16'),
                price_type='historical',
                source='sample'
            ),
            # CSI 300 ETF
            Price(
                asset_id=5,
                price_date=date(2024, 1, 15),
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
        transactions = [
            # Initial cash deposit
            Transaction(
                trade_date=date(2024, 1, 1),
                action='cash_in',
                amount=Decimal('500000'),
                currency_id=1,
                notes='Initial capital'
            ),
            # Buy CMB
            Transaction(
                trade_date=date(2024, 1, 5),
                action='buy',
                asset_id=1,
                quantity=Decimal('1000'),
                price=Decimal('35.20'),
                amount=Decimal('35200'),
                fees=Decimal('5.28'),
                currency_id=1,
                notes='Buy CMB shares'
            ),
            # Buy Wuliangye
            Transaction(
                trade_date=date(2024, 1, 8),
                action='buy',
                asset_id=2,
                quantity=Decimal('100'),
                price=Decimal('180.50'),
                amount=Decimal('18050'),
                fees=Decimal('2.71'),
                currency_id=1,
                notes='Buy Wuliangye shares'
            ),
            # Buy Apple
            Transaction(
                trade_date=date(2024, 1, 10),
                action='buy',
                asset_id=3,
                quantity=Decimal('50'),
                price=Decimal('182.00'),
                amount=Decimal('9100'),
                fees=Decimal('1.82'),
                currency_id=2,
                notes='Buy Apple shares'
            ),
            # Buy CSI 300 ETF
            Transaction(
                trade_date=date(2024, 1, 12),
                action='buy',
                asset_id=5,
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


def main():
    """Main initialization function"""
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