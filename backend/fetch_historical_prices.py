"""
Fetch historical daily close prices for all non-cash assets from AKShare API
and store them in the price table of the database.
"""

import akshare as ak
from sqlmodel import Session, select
from datetime import datetime, date
from decimal import Decimal
import pandas as pd
import os
import sys

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import Asset, Price, engine


def get_non_cash_assets() -> list[Asset]:
    """Get all non-cash assets from the database"""
    with Session(engine) as session:
        statement = select(Asset).where(Asset.asset_type != "cash")
        assets = session.exec(statement).all()
        return assets


def fetch_historical_prices(symbol, start_date, end_date):
    """
    Fetch historical daily close prices from AKShare API
    
    Args:
        symbol: Stock symbol (e.g., '600036.SH', 'AAPL', '510300.SH')
        start_date: Start date in 'YYYY-MM-DD' format
        end_date: End date in 'YYYY-MM-DD' format
    
    Returns:
        DataFrame with historical price data
    """
    try:
        # Handle different symbol formats based on market
        if symbol.endswith('.SH') or symbol.endswith('.SZ'):
            # Chinese A-shares and ETFs
            stock_code = symbol.replace('.SH', '').replace('.SZ', '')
            
            # Try stock_zh_a_hist first for stocks
            if not symbol.startswith('51') and not symbol.startswith('15'):
                try:
                    df = ak.stock_zh_a_hist(
                        symbol=stock_code,
                        period="daily",
                        start_date=start_date.replace('-', ''),
                        end_date=end_date.replace('-', ''),
                        adjust=""
                    )
                    if not df.empty:
                        df = df.rename(columns={
                            '日期': 'date',
                            '收盘': 'close'
                        })
                        df['date'] = pd.to_datetime(df['date']).dt.date
                        return df[['date', 'close']]
                except Exception as e:
                    print(f"stock_zh_a_hist failed for {symbol}: {e}")
            
            # Try fund_etf_hist_em for ETFs
            try:
                df = ak.fund_etf_hist_em(
                    symbol=stock_code,
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    adjust=""
                )
                if not df.empty:
                    df = df.rename(columns={
                        '日期': 'date',
                        '收盘': 'close'
                    })
                    df['date'] = pd.to_datetime(df['date']).dt.date
                    return df[['date', 'close']]
            except Exception as e:
                print(f"fund_etf_hist_em failed for {symbol}: {e}")
            
            # Try stock_zh_a_spot for real-time data fallback
            try:
                df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=start_date.replace('-', ''),
                    end_date=end_date.replace('-', ''),
                    adjust=""
                )
                if not df.empty:
                    df = df.rename(columns={
                        '日期': 'date',
                        '收盘': 'close'
                    })
                    df['date'] = pd.to_datetime(df['date']).dt.date
                    return df[['date', 'close']]
            except Exception as e:
                print(f"stock_zh_a_hist fallback failed for {symbol}: {e}")
                
        elif symbol == 'AAPL':
            # US stocks - using stock_us_spot
            try:
                # Get historical data for US stocks
                df = ak.stock_us_daily(symbol=symbol)
                if not df.empty:
                    # Filter by date range
                    df = df.reset_index()
                    df = df.rename(columns={
                        'date': 'date',
                        'close': 'close'
                    })
                    df['date'] = pd.to_datetime(df['date']).dt.date
                    
                    # Filter by date range
                    start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                    end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                    df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
                    
                    return df[['date', 'close']]
            except Exception as e:
                print(f"stock_us_daily failed for {symbol}: {e}")
                
                # Try alternative US stock method
                try:
                    df = ak.stock_us_hist(symbol=symbol, period="daily")
                    if not df.empty:
                        df = df.rename(columns={
                            '日期': 'date',
                            '收盘': 'close'
                        })
                        df['date'] = pd.to_datetime(df['date']).dt.date
                        
                        # Filter by date range
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                        df = df[(df['date'] >= start_dt) & (df['date'] <= end_dt)]
                        
                        return df[['date', 'close']]
                except Exception as e2:
                    print(f"stock_us_hist failed for {symbol}: {e2}")
        
        print(f"No data found for symbol: {symbol}")
        return pd.DataFrame()
        
    except Exception as e:
        print(f"Error fetching data for {symbol}: {str(e)}")
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
            price_date = row['date']
            if price_date not in existing_dates:
                price = Price(
                    asset_id=asset_id,
                    price_date=price_date,
                    price=Decimal(str(row['close'])),
                    price_type="historical",
                    source="akshare"
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
    start_date = "2024-01-01"
    end_date = "2025-06-30"
    
    print("Fetching historical prices from AKShare...")
    print(f"Date range: {start_date} to {end_date}")
    
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
        
        price_data = fetch_historical_prices(asset.symbol, start_date, end_date)
        
        if not price_data.empty:
            print(f"  Retrieved {len(price_data)} price records")
            store_prices_in_db(asset.id, price_data)
        else:
            print(f"  No price data retrieved for {asset.symbol}")
    
    print("\nHistorical price fetching completed!")


if __name__ == "__main__":
    main()