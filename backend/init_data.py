"""
Initialize the database with sample data for the Portfolio Tracker
"""

from sqlmodel import Session, select
from datetime import date, timedelta
from decimal import Decimal
import pandas as pd
import os
import sys
# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import akshare as ak
import pandas as pd
from datetime import date
from decimal import Decimal

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
from sqlmodel import Session, select


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
                rate_date=date(2024, 12, 31),
                rate_to_primary=Decimal("7.2"),
            ),
            ExchangeRate(
                currency_id=3,  # HKD
                rate_date=date(2024, 12, 31),
                rate_to_primary=Decimal("0.92"),
            ),
            ExchangeRate(
                currency_id=4,  # EUR
                rate_date=date(2024, 12, 31),
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
                type="cash",
                currency_id=1,
                isin="CASH_CNY",
            ),
            Asset(
                symbol="USD_CASH",
                name="US Dollar Cash",
                type="cash",
                currency_id=2,
                isin="CASH_USD",
            ),
            Asset(
                symbol="HKD_CASH",
                name="Hong Kong Dollar Cash",
                type="cash",
                currency_id=3,
                isin="CASH_HKD",
            ),
            Asset(
                symbol="EUR_CASH",
                name="Euro Cash",
                type="cash",
                currency_id=4,
                isin="CASH_EUR",
            ),
            # Stock
            Asset(
                symbol="600036.SH",
                name="China Merchants Bank",
                type="stock",
                currency_id=1,
                isin="CNE000001R84",
            ),
            Asset(
                symbol="00700.HK",
                name="Tencent Holdings",
                type="stock",
                currency_id=3,  # HKD
                isin="KYG875721634",
            ),
            # ETF
            Asset(
                symbol="510300.SH",
                name="CSI 300 ETF",
                type="etf",
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
        ]

        session.add_all(prices)
        session.commit()
        print("Sample prices initialized successfully")


def get_non_cash_assets() -> list[Asset]:
    """Get all non-cash assets from the database"""
    with Session(engine) as session:
        statement = select(Asset).where(Asset.type != "cash")
        assets = session.exec(statement).all()
        return assets


def fetch_historical_prices(asset: Asset, start_date: date, end_date: date) -> pd.DataFrame:
    """
    Fetch historical daily close prices from AKShare API

    Args:
        asset: Asset object containing symbol and other asset information
        start_date: Start date as datetime.date object
        end_date: End date as datetime.date object

    Returns:
        DataFrame with historical price data
    """
    symbol = asset.symbol
    if asset.type == "stock":
        # Chinese Stocks
        if symbol.endswith(".SH") or symbol.endswith(".SZ"):
            sec_code = symbol.replace(".SH", "").replace(".SZ", "")
            df = ak.stock_zh_a_hist(
                symbol=sec_code,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="",  # Non-adjusted price
            )
            if not df.empty:
                df = df.rename(columns={"日期": "date", "收盘": "close"})
                df["date"] = pd.to_datetime(df["date"]).dt.date
                return df[["date", "close"]]
        # Hong Kong Stocks
        elif symbol.endswith(".HK"):
            sec_code = symbol.replace(".HK", "")
            df = ak.stock_hk_hist(
                symbol=sec_code,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="",  # Non-adjusted price
            )
            if not df.empty:
                df = df.rename(columns={"日期": "date", "收盘": "close"})
                df["date"] = pd.to_datetime(df["date"]).dt.date
                return df[["date", "close"]]
    elif asset.type == "etf":
        # Chinese ETFs
        if symbol.endswith(".SH") or symbol.endswith(".SZ"):
            sec_code = symbol.replace(".SH", "").replace(".SZ", "")
            if asset.type == "etf":
                df = ak.fund_etf_hist_em(
                    symbol=sec_code,
                    start_date=start_date.strftime("%Y%m%d"),
                    end_date=end_date.strftime("%Y%m%d"),
                    adjust="",  # Non-adjusted price
                )
                if not df.empty:
                    df = df.rename(columns={"日期": "date", "收盘": "close"})
                    df["date"] = pd.to_datetime(df["date"]).dt.date
                    return df[["date", "close"]]
    print(f"No data found for symbol: {symbol}")
    return pd.DataFrame()


def store_prices_in_db(asset_id, price_data):
    """Store historical prices in the database"""
    with Session(engine) as session:
        # Check existing prices to avoid duplicates
        existing_dates = set()
        statement = select(Price).where(Price.asset_id == asset_id)
        existing_prices = session.exec(statement).all()
        for price in existing_prices:
            existing_dates.add(price.price_date)

        # Add new prices
        new_prices = []
        for _, row in price_data.iterrows():
            price_date = row["date"]
            if price_date not in existing_dates:
                price = Price(
                    asset_id=asset_id,
                    price_date=price_date,
                    price=Decimal(str(row["close"])),
                    price_type="historical",
                    source="akshare",
                )
                new_prices.append(price)

        if new_prices:
            session.add_all(new_prices)
            session.commit()
            print(f"Added {len(new_prices)} new prices for asset_id {asset_id}")
        else:
            print(f"No new prices to add for asset_id {asset_id}")


def fetch_and_store_historical_prices():
    """Fetch and store historical prices for all non-cash assets"""
    start_date = date(2025, 1, 1)
    end_date = date(2025, 6, 30)

    print("Fetching historical prices from AKShare...")
    print(
        f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    )

    # Get non-cash assets
    assets = get_non_cash_assets()

    if not assets:
        print("No non-cash assets found in the database")
        return

    print(f"Found {len(assets)} non-cash assets:")
    for asset in assets:
        print(f"  - {asset.symbol}: {asset.name}")

    # Fetch prices for each asset
    for asset in assets:
        print(f"\nFetching prices for {asset.symbol} ({asset.name})...")

        price_data = fetch_historical_prices(asset, start_date, end_date)

        if not price_data.empty:
            print(f"  Retrieved {len(price_data)} price records")
            store_prices_in_db(asset.id, price_data)
        else:
            print(f"  No price data retrieved for {asset.symbol}")

    print("\nHistorical price fetching completed!")


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
        
        # Replace AAPL with 0700.HK in the dataframe
        df.replace("AAPL", "0700.HK", inplace=True)
        df.replace("Apple Inc.", "Tencent Holdings", inplace=True)

        # Use the import csv function from main.py
        transactions = _import_transactions_from_dataframe(df, session)

        session.add_all(transactions)
        session.commit()
        print(
            f"Sample transactions initialized successfully from CSV ({len(transactions)} transactions)"
        )

        # Calculate positions for the entire period using PositionService
        print("Calculating positions from transactions...")
        position_service = PositionService(session)

        # Get the date range from transactions
        start_date = min(t.trade_date for t in transactions)
        end_date = max(t.trade_date for t in transactions)

        print(f"Calculating positions from {start_date} to {end_date}")

        # Calculate positions for every day during the period
        current_date = start_date
        while current_date <= end_date:
            positions = position_service.update_positions_for_period(
                portfolio_id=portfolio.id,
                start_date=start_date,
                end_date=current_date,
                save_to_db=True,
            )
            start_date = current_date
            current_date += timedelta(days=1)

        print(f"Successfully calculated {len(positions)} positions")

        # Print summary of positions
        for asset_id, position in positions.items():
            asset = session.get(Asset, asset_id)
            if asset and position.quantity > 0:
                print(
                    f"  {asset.symbol}: {position.quantity} shares @ {position.current_price} = {position.market_value}"
                )


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
    fetch_and_store_historical_prices()
    init_sample_transactions()

    print("\nDatabase initialization completed successfully!")
    print("You can now start the FastAPI server with: uvicorn main:app --reload")


if __name__ == "__main__":
    main()
