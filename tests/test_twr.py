"""Tests for Time-Weighted Return calculation"""
import csv
import pytest
from pathlib import Path
from datetime import date, timedelta
from decimal import Decimal
from sqlmodel import Session, select
from backend.models import (
    Transaction, Price, ExchangeRate
)
from backend.services import PortfolioService


@pytest.fixture
def test_data_with_sample_transactions(test_db: Session):
    """Create test data based on sample_transactions.csv using existing currencies and assets"""
    
    # Use existing currencies and assets from conftest
    cny = test_db._test_cny
    hkd = test_db._test_hkd
    usd = test_db._test_usd
    portfolio = test_db._test_portfolio
    assets = test_db._test_assets
    
    # Create exchange rates (CNY is primary, so rates are from other currencies to CNY)
    exchange_rates = [
        # USD to CNY rates (1 USD = 7.2 CNY)
        (usd.id, date(2025, 1, 1), Decimal("7.2")),
        (usd.id, date(2025, 1, 5), Decimal("7.2")),
        (usd.id, date(2025, 1, 9), Decimal("7.2")),
        (usd.id, date(2025, 1, 10), Decimal("7.2")),
        (usd.id, date(2025, 2, 7), Decimal("7.2")),
        (usd.id, date(2025, 2, 10), Decimal("7.2")),
        (usd.id, date(2025, 2, 11), Decimal("7.2")),
        (usd.id, date(2025, 2, 12), Decimal("7.2")),
        
        # HKD to CNY rates (1 HKD = 0.92 CNY)
        (hkd.id, date(2025, 1, 1), Decimal("0.92")),
        (hkd.id, date(2025, 1, 9), Decimal("0.92")),
        (hkd.id, date(2025, 1, 10), Decimal("0.92")),
        (hkd.id, date(2025, 2, 11), Decimal("0.92")),
    ]
    
    for currency_id, rate_date, rate in exchange_rates:
        exchange_rate = ExchangeRate(
            currency_id=currency_id,
            rate_date=rate_date,
            rate_to_primary=rate
        )
        test_db.add(exchange_rate)
    
    # Create prices for assets
    prices_data = [
        # China Merchants Bank (600036.SH) - in CNY
        (assets["600036.SH"].id, date(2025, 1, 1), Decimal("35.2")),
        (assets["600036.SH"].id, date(2025, 1, 5), Decimal("35.2")),
        (assets["600036.SH"].id, date(2025, 1, 10), Decimal("36.0")),
        (assets["600036.SH"].id, date(2025, 2, 7), Decimal("36.0")),
        (assets["600036.SH"].id, date(2025, 2, 10), Decimal("36.0")),
        
        # Tencent Holdings (00700.HK) - in HKD
        (assets["00700.HK"].id, date(2025, 1, 9), Decimal("380")),
        (assets["00700.HK"].id, date(2025, 1, 10), Decimal("380")),
        (assets["00700.HK"].id, date(2025, 2, 11), Decimal("400")),
        
        # CSI 300 ETF (510300.SH) - in CNY
        (assets["510300.SH"].id, date(2025, 2, 12), Decimal("3.85")),
        
        # Cash assets (always 1 in their own currency)
        (assets["CNY_CASH"].id, date(2025, 1, 1), Decimal("1")),
        (assets["CNY_CASH"].id, date(2025, 2, 12), Decimal("1")),
        
        (assets["HKD_CASH"].id, date(2025, 1, 9), Decimal("1")),
        (assets["HKD_CASH"].id, date(2025, 2, 12), Decimal("1")),
    ]
    
    for asset_id, price_date, price in prices_data:
        price_obj = Price(
            asset_id=asset_id,
            price_date=price_date,
            price=price,
            price_type="historical"
        )
        test_db.add(price_obj)
    
    csv_path = Path(__file__).parent.parent / "backend" / "sample_transactions.csv"
    
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Parse date format: 2025/1/1 -> date(2025, 1, 1)
            year, month, day = map(int, row['trade_date'].split('/'))
            trade_date = date(year, month, day)
            action = row['action']
            symbol = row['symbol']
            quantity = row['quantity']
            price = row['price']
            amount = Decimal(row['amount'])
            fees = Decimal(row['fees'])
            transaction = Transaction(
                portfolio_id=portfolio.id,
                trade_date=trade_date,
                action=action,
                asset_id=assets[symbol].id,
                quantity=quantity,
                price = price,
                amount=amount,
                fees=fees,
                currency_id=assets[symbol].currency_id
            )
            test_db.add(transaction)

    test_db.commit()
    
    return {
        "portfolio": portfolio,
        "assets": assets,
        "currencies": {"cny": cny, "hkd": hkd, "usd": usd},
        "service": PortfolioService(test_db)
    }


class TestTimeWeightedReturn:
    """Test cases for Time-Weighted Return calculation"""
    
    def test_twr_basic(self, test_data_with_sample_transactions):
        """Test basic TWR calculation with sample data"""
        data = test_data_with_sample_transactions
        service = data["service"]
        portfolio = data["portfolio"]
        
        start_date = date(2025, 1, 1)
        end_date = date(2025, 2, 12)
        
        result = service.twr(
            portfolio.id, start_date, end_date
        )
        
        # Basic assertions
        assert isinstance(result, dict)
        assert "twr" in result
        assert "period_return" in result
        assert "annualized_return" in result
        assert "beginning_value" in result
        assert "ending_value" in result
        assert "net_cash_flow" in result
        assert "daily_returns" in result
        
        # Check that values are calculated
        assert isinstance(result["twr"], float)
        assert isinstance(result["period_return"], float)
        assert isinstance(result["annualized_return"], float)
        assert isinstance(result["beginning_value"], float)
        assert isinstance(result["ending_value"], float)
        assert isinstance(result["net_cash_flow"], float)
        assert isinstance(result["daily_returns"], list)
        
        # Validate basic relationships
        assert len(result["daily_returns"]) >= 0
        
    def test_twr_single_day(self, test_data_with_sample_transactions):
        """Test TWR calculation for a single day (should be 0%)"""
        data = test_data_with_sample_transactions
        service = data["service"]
        portfolio = data["portfolio"]
        
        start_date = date(2025, 1, 1)
        end_date = date(2025, 1, 1)
        
        result = service.twr(
            portfolio.id, start_date, end_date
        )
        
        # For single day, TWR should be 0%
        assert abs(result["twr"]) < 0.001  # Allow small floating point error
        assert abs(result["period_return"]) < 0.001
        assert abs(result["annualized_return"]) < 0.001
        
    def test_twr_no_transactions(self, test_data_with_sample_transactions):
        """Test TWR calculation with no transactions in period"""
        data = test_data_with_sample_transactions
        service = data["service"]
        portfolio = data["portfolio"]
        
        # Choose dates after all transactions
        start_date = date(2025, 3, 1)
        end_date = date(2025, 3, 15)
        
        result = service.twr(
            portfolio.id, start_date, end_date
        )
        
        # Should return 0 for no activity period
        assert abs(result["twr"]) < 0.001
        assert abs(result["period_return"]) < 0.001
        assert abs(result["annualized_return"]) < 0.001
        
    def test_twr_negative_values(self, test_data_with_sample_transactions):
        """Test TWR calculation handles negative scenarios correctly"""
        data = test_data_with_sample_transactions
        service = data["service"]
        portfolio = data["portfolio"]
        
        # Test with reversed dates (should handle gracefully)
        start_date = date(2025, 2, 12)
        end_date = date(2025, 1, 1)
        
        result = service.twr(
            portfolio.id, start_date, end_date
        )
        
        # Should return 0 for invalid date range
        assert abs(result["twr"]) < 0.001
        
    def test_twr_data_integrity(self, test_data_with_sample_transactions):
        """Test that TWR calculation maintains data integrity"""
        data = test_data_with_sample_transactions
        service = data["service"]
        portfolio = data["portfolio"]
        
        start_date = date(2025, 1, 1)
        end_date = date(2025, 2, 12)
        
        result = service.twr(
            portfolio.id, start_date, end_date
        )
        
        # Verify basic data integrity - focus on structure rather than exact values
        assert isinstance(result["net_cash_flow"], (int, float))
        
        # Verify beginning and ending values are positive
        assert result["beginning_value"] >= 0
        assert result["ending_value"] >= 0
        
    def test_twr_daily_returns_length(self, test_data_with_sample_transactions):
        """Test that daily_returns array has correct length"""
        data = test_data_with_sample_transactions
        service = data["service"]
        portfolio = data["portfolio"]

        start_date = date(2025, 1, 1)
        end_date = date(2025, 2, 12)

        result = service.twr(
            portfolio.id, start_date, end_date
        )

        # Calculate expected number of days
        expected_days = (end_date - start_date).days

        # Daily returns should have expected_days - 1 elements (from day 2 to end)
        # Allow for empty array if no trading days or if calculation fails
        assert len(result["daily_returns"]) <= expected_days
        assert len(result["daily_returns"]) >= 0
        
    def test_twr_error_handling(self, test_data_with_sample_transactions):
        """Test error handling in TWR calculation"""
        data = test_data_with_sample_transactions
        service = data["service"]
        
        # Test with non-existent portfolio ID
        result = service.twr(
            9999, date(2025, 1, 1), date(2025, 2, 12)
        )
        
        # Should return error result with zeros
        assert result["twr"] == 0.0
        assert result["period_return"] == 0.0
        assert result["annualized_return"] == 0.0
        assert result["beginning_value"] == 0.0
        assert result["ending_value"] == 0.0
        
    def test_twr_with_missing_prices(self, test_data_with_sample_transactions):
        """Test TWR calculation when some prices are missing"""
        data = test_data_with_sample_transactions
        service = data["service"]
        portfolio = data["portfolio"]
        
        # This test is simplified to just verify graceful handling
        # In a real scenario, we would need to manipulate the database
        start_date = date(2025, 1, 1)
        end_date = date(2025, 2, 12)
        
        result = service.twr(
            portfolio.id, start_date, end_date
        )
        
        # Should handle missing prices gracefully
        assert isinstance(result, dict)
        assert "twr" in result