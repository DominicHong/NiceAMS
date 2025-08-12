"""Shared test configuration for all test modules"""

import pytest
import tempfile
import os
from sqlmodel import create_engine, SQLModel, Session
from backend.models import Currency, Portfolio, Asset


@pytest.fixture
def test_db():
    """Create a fresh test database for each test"""
    # Create a temporary file-based SQLite database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    try:
        engine = create_engine(f"sqlite:///{db_path}")
        SQLModel.metadata.create_all(engine)
        
        with Session(engine) as session:
            # Initialize currencies with CNY as primary
            cny = Currency(code="CNY", name="Chinese Yuan", symbol="¥", is_primary=True)
            hkd = Currency(code="HKD", name="Hong Kong Dollar", symbol="HK$", is_primary=False)
            usd = Currency(code="USD", name="US Dollar", symbol="$", is_primary=False)
            
            session.add_all([cny, hkd, usd])
            session.flush()
            
            # Create portfolio with CNY as base currency
            portfolio = Portfolio(name="Test Portfolio", base_currency_id=cny.id)
            session.add(portfolio)
            session.flush()
            
            # Create basic assets
            assets = [
                Asset(symbol="600036.SH", name="China Merchants Bank", type="stock", currency_id=cny.id),
                Asset(symbol="00700.HK", name="Tencent Holdings", type="stock", currency_id=hkd.id),
                Asset(symbol="510300.SH", name="CSI 300 ETF", type="etf", currency_id=cny.id),
                Asset(symbol="CNY_CASH", name="Chinese Yuan Cash", type="cash", currency_id=cny.id),
                Asset(symbol="HKD_CASH", name="Hong Kong Dollar Cash", type="cash", currency_id=hkd.id),
                Asset(symbol="USD_CASH", name="US Dollar Cash", type="cash", currency_id=usd.id),
            ]
            
            for asset in assets:
                session.add(asset)
            session.flush()
            
            session.commit()
            
            # Store references for tests to use
            session._test_cny = cny
            session._test_hkd = hkd
            session._test_usd = usd
            session._test_portfolio = portfolio
            session._test_assets = {asset.symbol: asset for asset in assets}
            
            yield session
            
    finally:
        # Clean up - close the engine and remove the temporary file
        engine.dispose()
        os.close(db_fd)
        os.unlink(db_path)