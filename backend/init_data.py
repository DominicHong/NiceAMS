"""
Initialize the database with sample data for the Portfolio Tracker
"""

from sqlmodel import Session, select, delete
from datetime import date
from decimal import Decimal
import pandas as pd
import os

from models import (
    ROOT_PATH,
    Currency,
    ExchangeRate,
    Asset,
    Portfolio,
    Price,
    create_db_and_tables,
    drop_db_and_tables,
    engine,
)
from services import PositionService
from main import _import_transactions_from_dataframe


def init_currencies():
    """Initialize basic currencies"""
    with Session(engine) as session:
        currencies = [
            Currency(code="CNY", name="Chinese Yuan", symbol="¥", is_primary=True),
            Currency(code="USD", name="US Dollar", symbol="$", is_primary=False),
            Currency(
                code="HKD", name="Hong Kong Dollar", symbol="HK$", is_primary=False
            ),
            Currency(code="EUR", name="Euro", symbol="€", is_primary=False),
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
                rate_to_primary=Decimal("7.2"),
            ),
            ExchangeRate(
                currency_id=3,  # HKD
                rate_date=date(2024, 1, 15),
                rate_to_primary=Decimal("0.92"),
            ),
            ExchangeRate(
                currency_id=4,  # EUR
                rate_date=date(2024, 1, 15),
                rate_to_primary=Decimal("7.8"),
            ),
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
                isin="CASH_CNY",
            ),
            Asset(
                symbol="USD_CASH",
                name="US Dollar Cash",
                asset_type="cash",
                currency_id=2,
                isin="CASH_USD",
            ),
            Asset(
                symbol="HKD_CASH",
                name="Hong Kong Dollar Cash",
                asset_type="cash",
                currency_id=3,
                isin="CASH_HKD",
            ),
            Asset(
                symbol="EUR_CASH",
                name="Euro Cash",
                asset_type="cash",
                currency_id=4,
                isin="CASH_EUR",
            ),
            # Stock
            Asset(
                symbol="600036.SH",
                name="China Merchants Bank",
                asset_type="stock",
                currency_id=1,
                isin="CNE000001R84",
            ),
            Asset(
                symbol="AAPL",
                name="Apple Inc.",
                asset_type="stock",
                currency_id=2,
                isin="US0378331005",
            ),
            # ETF
            Asset(
                symbol="510300.SH",
                name="CSI 300 ETF",
                asset_type="etf",
                currency_id=1,
                isin="CNE000001234",
            ),
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
            base_currency_id=1,
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
                price=Decimal("1.0"),
                price_type="historical",
                source="sample",
            ),
            Price(
                asset_id=2,  # USD_CASH
                price_date=date(2025, 3, 1),
                price=Decimal("1.0"),
                price_type="historical",
                source="sample",
            ),
            Price(
                asset_id=3,  # HKD_CASH
                price_date=date(2025, 3, 1),
                price=Decimal("1.0"),
                price_type="historical",
                source="sample",
            ),
            Price(
                asset_id=4,  # EUR_CASH
                price_date=date(2025, 3, 1),
                price=Decimal("1.0"),
                price_type="historical",
                source="sample",
            ),
            # Stock assets
            Price(
                asset_id=5,  # CMB
                price_date=date(2025, 3, 1),
                price=Decimal("35.50"),
                price_type="historical",
                source="sample",
            ),
            Price(
                asset_id=6,  # Apple
                price_date=date(2025, 3, 1),
                price=Decimal("185.64"),
                price_type="historical",
                source="sample",
            ),
            Price(
                asset_id=7,  # CSI 300 ETF
                price_date=date(2025, 3, 1),
                price=Decimal("3.85"),
                price_type="historical",
                source="sample",
            ),
        ]

        session.add_all(prices)
        session.commit()
        print("Sample prices initialized successfully")


def init_sample_transactions():
    """Initialize sample transactions from CSV file using shared import logic"""
    with Session(engine) as session:
        # Get the portfolio that was created in init_portfolio()
        portfolio = session.exec(select(Portfolio)).first()
        if not portfolio or portfolio.id is None:
            raise ValueError("No portfolio found. Please run init_portfolio() first.")

        # Read transactions from CSV file
        csv_file_path = os.path.join(
            ROOT_PATH,
            "backend",
            "sample_transactions.csv",
        )

        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")

        # Read CSV using pandas
        df = pd.read_csv(csv_file_path)

        # Use the import csv function from main.py
        transactions = _import_transactions_from_dataframe(df, session)

        session.add_all(transactions)
        session.commit()
        print(
            f"Sample transactions initialized successfully from CSV ({len(transactions)} transactions)"
        )

        # Calculate positions for the entire period using PositionService
        print("Calculating positions from transactions...")
        try:
            position_service = PositionService(session)

            # Get the date range from transactions
            start_date = min(t.trade_date for t in transactions)
            end_date = max(t.trade_date for t in transactions)

            print(f"Calculating positions from {start_date} to {end_date}")

            # Calculate positions for the period
            positions = position_service.update_positions_for_period(
                portfolio_id=portfolio.id,
                start_date=start_date,
                end_date=end_date,
                save_to_db=True,
            )

            print(f"Successfully calculated {len(positions)} positions")

            # Print summary of positions
            for asset_id, position in positions.items():
                asset = session.get(Asset, asset_id)
                if asset and position.quantity > 0:
                    print(
                        f"  {asset.symbol}: {position.quantity} shares @ {position.current_price} = {position.market_value}"
                    )

        except Exception as e:
            print(f"Error calculating positions: {e}")


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
