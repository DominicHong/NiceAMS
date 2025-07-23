"""
Verify the historical prices stored in the database
"""

from sqlmodel import Session, select
from models import Price, Asset, engine
from datetime import datetime

def verify_stored_prices():
    """Verify the historical prices stored in the database"""
    
    with Session(engine) as session:
        # Get total count of prices
        total_prices = session.exec(select(Price)).all()
        print(f"Total prices stored: {len(total_prices)}")
        
        # Get prices grouped by asset
        assets = session.exec(select(Asset).where(Asset.asset_type != "cash")).all()
        
        for asset in assets:
            asset_prices = session.exec(
                select(Price).where(Price.asset_id == asset.id)
            ).all()
            
            if asset_prices:
                print(f"\n{asset.symbol} ({asset.name}):")
                print(f"  Total prices: {len(asset_prices)}")
                print(f"  Date range: {min(p.price_date for p in asset_prices)} to {max(p.price_date for p in asset_prices)}")
                print(f"  Price range: {min(p.price for p in asset_prices)} to {max(p.price for p in asset_prices)}")
                
                # Show first 3 prices
                sorted_prices = sorted(asset_prices, key=lambda x: x.price_date)
                print("  Sample prices:")
                for price in sorted_prices[:3]:
                    print(f"    {price.price_date}: {price.price}")
            else:
                print(f"\n{asset.symbol} ({asset.name}): No prices found")

if __name__ == "__main__":
    verify_stored_prices()