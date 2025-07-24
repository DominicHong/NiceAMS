"""
Fetch historical daily close prices for all non-cash assets from AKShare API
and store them in the price table of the database.
"""

import akshare as ak
from sqlmodel import Session, select
from datetime import date
from decimal import Decimal
import pandas as pd
import os
import sys
from models import Asset, Price, engine

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


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
    # Call different API methods based on asset type
    # Chinese Securities
    if symbol.endswith(".SH") or symbol.endswith(".SZ"):
        sec_code = symbol.replace(".SH", "").replace(".SZ", "")
        if asset.type == "stock":
            df = ak.stock_zh_a_hist(
                symbol=sec_code,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="",  # Default: Non-adjusted price
            )
            if not df.empty:
                df = df.rename(columns={"日期": "date", "收盘": "close"})
                df["date"] = pd.to_datetime(df["date"]).dt.date
                return df[["date", "close"]]
        elif asset.type == "etf":
            df = ak.fund_etf_hist_em(
                symbol=sec_code,
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="",  # Default: Non-adjusted price
            )
            if not df.empty:
                df = df.rename(columns={"日期": "date", "收盘": "close"})
                df["date"] = pd.to_datetime(df["date"]).dt.date
                return df[["date", "close"]]

    # # US Stocks
    # elif asset.type == "stock" and not (symbol.endswith(".SH") or symbol.endswith(".SZ")):
    #     # Get the correct US stock symbol from ak.stock_us_spot_em()
    #     us_stocks = ak.stock_us_spot_em()
    #     # Find the row matching our symbol and get the "代码" column value
    #     matching_stock = us_stocks[us_stocks["名称"] == asset.name]
    #     if not matching_stock.empty:
    #         akshare_symbol = matching_stock.iloc[0]["代码"]
    #         print(f"Using AKShare symbol: {akshare_symbol} for {asset.name}")
            
    #         # Get historical data for US stocks
    #         df = ak.stock_us_hist(
    #             symbol=akshare_symbol,
    #             period="daily",
    #             start_date=start_date.strftime("%Y%m%d"),
    #             end_date=end_date.strftime("%Y%m%d"),
    #             adjust="",  # Default: Non-adjusted price
    #         )
    #         if not df.empty:
    #             df = df.rename(columns={"日期": "date", "收盘": "close"})
    #             df["date"] = pd.to_datetime(df["date"]).dt.date
    #             return df[["date", "close"]]

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


def main():
    """Main function to fetch and store historical prices"""
    start_date = date(2024, 1, 1)
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


if __name__ == "__main__":
    main()
