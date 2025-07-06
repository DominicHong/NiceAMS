from sqlmodel import Session, select
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime, timedelta
from decimal import Decimal
import pandas as pd
import numpy as np
from collections import defaultdict

from models import (
    Currency, ExchangeRate, Asset, AssetMetadata, Transaction, Price, Portfolio, 
    PortfolioStatistics, Holding, get_session
)


class CurrencyService:
    """Service for currency conversion and management"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_primary_currency(self) -> Currency:
        """Get the primary currency"""
        primary = self.session.exec(select(Currency).where(Currency.is_primary == True)).first()
        if not primary:
            # Create CNY as default primary currency
            primary = Currency(
                code="CNY",
                name="Chinese Yuan",
                symbol="¥",
                is_primary=True
            )
            self.session.add(primary)
            self.session.commit()
            self.session.refresh(primary)
        return primary
    
    def get_exchange_rate(self, currency_id: int, rate_date: date) -> Decimal:
        """Get exchange rate for a currency on a specific date"""
        if currency_id == self.get_primary_currency().id:
            return Decimal('1.0')
        
        # Get the most recent exchange rate before or on the date
        rate = self.session.exec(
            select(ExchangeRate)
            .where(ExchangeRate.currency_id == currency_id)
            .where(ExchangeRate.rate_date <= rate_date)
            .order_by(ExchangeRate.rate_date.desc())
        ).first()
        
        return rate.rate_to_primary if rate else Decimal('1.0')
    
    def convert_to_primary_currency(self, amount: Decimal, currency_id: int, rate_date: date) -> Decimal:
        """Convert amount to primary currency"""
        rate = self.get_exchange_rate(currency_id, rate_date)
        return amount * rate


class PriceService:
    """Service for price management"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_latest_price(self, asset_id: int, as_of_date: date = None) -> Optional[Price]:
        """Get the latest price for an asset"""
        if as_of_date is None:
            as_of_date = date.today()
        
        price = self.session.exec(
            select(Price)
            .where(Price.asset_id == asset_id)
            .where(Price.price_date <= as_of_date)
            .order_by(Price.price_date.desc())
        ).first()
        
        return price
    
    def get_price_history(self, asset_id: int, start_date: date, end_date: date) -> List[Price]:
        """Get price history for an asset"""
        prices = self.session.exec(
            select(Price)
            .where(Price.asset_id == asset_id)
            .where(Price.price_date >= start_date)
            .where(Price.price_date <= end_date)
            .order_by(Price.price_date)
        ).all()
        
        return prices


class TransactionService:
    """Service for transaction processing"""
    
    def __init__(self, session: Session):
        self.session = session
        self.currency_service = CurrencyService(session)
    
    def process_transaction(self, transaction: Transaction) -> Dict:
        """Process a transaction and update holdings"""
        result = {"success": False, "message": ""}
        
        try:
            if transaction.action in ['buy', 'sell']:
                self._process_trade_transaction(transaction)
            elif transaction.action == 'dividends':
                self._process_dividend_transaction(transaction)
            elif transaction.action == 'split':
                self._process_split_transaction(transaction)
            elif transaction.action == 'interest':
                self._process_interest_transaction(transaction)
            elif transaction.action in ['cash_in', 'cash_out']:
                self._process_cash_transaction(transaction)
            
            result["success"] = True
            result["message"] = f"Transaction {transaction.action} processed successfully"
            
        except Exception as e:
            result["message"] = f"Error processing transaction: {str(e)}"
        
        return result
    
    def _process_trade_transaction(self, transaction: Transaction):
        """Process buy/sell transactions"""
        # Find or create holding
        holding = self.session.exec(
            select(Holding)
            .where(Holding.asset_id == transaction.asset_id)
            .where(Holding.portfolio_id == 1)  # Assuming single portfolio for now
        ).first()
        
        if not holding:
            holding = Holding(
                portfolio_id=1,
                asset_id=transaction.asset_id,
                quantity=Decimal('0'),
                average_cost=Decimal('0')
            )
            self.session.add(holding)
        
        if transaction.action == 'buy':
            # Update average cost and quantity
            total_cost = holding.average_cost * holding.quantity + transaction.amount
            holding.quantity += transaction.quantity
            holding.average_cost = total_cost / holding.quantity if holding.quantity > 0 else Decimal('0')
        
        elif transaction.action == 'sell':
            # Reduce quantity
            holding.quantity -= transaction.quantity
            if holding.quantity <= 0:
                self.session.delete(holding)
        
        self.session.commit()
    
    def _process_dividend_transaction(self, transaction: Transaction):
        """Process dividend transactions"""
        # Add to cash balance (implementation depends on cash management structure)
        pass
    
    def _process_split_transaction(self, transaction: Transaction):
        """Process stock split transactions"""
        holding = self.session.exec(
            select(Holding)
            .where(Holding.asset_id == transaction.asset_id)
            .where(Holding.portfolio_id == 1)
        ).first()
        
        if holding:
            split_ratio = transaction.quantity  # e.g., 2 for 2-for-1 split
            holding.quantity *= split_ratio
            holding.average_cost /= split_ratio
            self.session.commit()
    
    def _process_interest_transaction(self, transaction: Transaction):
        """Process interest transactions"""
        # Add to cash balance
        pass
    
    def _process_cash_transaction(self, transaction: Transaction):
        """Process cash in/out transactions"""
        # Update cash balance
        pass


class PortfolioService:
    """Service for portfolio calculations and statistics"""
    
    def __init__(self, session: Session):
        self.session = session
        self.currency_service = CurrencyService(session)
        self.price_service = PriceService(session)
    
    def calculate_portfolio_value(self, portfolio_id: int, as_of_date: date = None) -> Dict:
        """Calculate total portfolio value"""
        if as_of_date is None:
            as_of_date = date.today()
        
        holdings = self.session.exec(
            select(Holding).where(Holding.portfolio_id == portfolio_id)
        ).all()
        
        total_value = Decimal('0')
        holdings_value = []
        
        for holding in holdings:
            # Get latest price
            latest_price = self.price_service.get_latest_price(holding.asset_id, as_of_date)
            current_price = latest_price.price if latest_price else Decimal('0')
            
            # Calculate market value
            market_value = holding.quantity * current_price
            
            # Convert to primary currency
            asset = self.session.get(Asset, holding.asset_id)
            market_value_primary = self.currency_service.convert_to_primary_currency(
                market_value, asset.currency_id, as_of_date
            )
            
            total_value += market_value_primary
            
            # Update holding
            holding.current_price = current_price
            holding.market_value = market_value_primary
            holding.unrealized_pnl = market_value_primary - (holding.average_cost * holding.quantity)
            holding.last_updated = datetime.utcnow()
            
            holdings_value.append({
                "asset_id": holding.asset_id,
                "symbol": asset.symbol,
                "name": asset.name,
                "quantity": holding.quantity,
                "current_price": current_price,
                "market_value": market_value_primary,
                "unrealized_pnl": holding.unrealized_pnl
            })
        
        self.session.commit()
        
        return {
            "total_value": total_value,
            "holdings": holdings_value,
            "calculation_date": as_of_date
        }
    
    def calculate_time_weighted_return(self, portfolio_id: int, start_date: date, end_date: date) -> Dict:
        """Calculate Time-Weighted Return (TWR) for portfolio"""
        transactions = self.session.exec(
            select(Transaction)
            .where(Transaction.trade_date >= start_date)
            .where(Transaction.trade_date <= end_date)
            .order_by(Transaction.trade_date)
        ).all()
        
        # Group transactions by date
        daily_transactions = defaultdict(list)
        for transaction in transactions:
            daily_transactions[transaction.trade_date].append(transaction)
        
        # Calculate daily returns
        portfolio_values = []
        cash_flows = []
        dates = []
        
        current_date = start_date
        while current_date <= end_date:
            # Calculate portfolio value
            portfolio_value = self.calculate_portfolio_value(portfolio_id, current_date)["total_value"]
            
            # Calculate cash flows for the day
            daily_cash_flow = Decimal('0')
            for transaction in daily_transactions.get(current_date, []):
                if transaction.action in ['buy', 'cash_in']:
                    daily_cash_flow += transaction.amount
                elif transaction.action in ['sell', 'cash_out']:
                    daily_cash_flow -= transaction.amount
            
            portfolio_values.append(float(portfolio_value))
            cash_flows.append(float(daily_cash_flow))
            dates.append(current_date)
            
            current_date += timedelta(days=1)
        
        # Calculate TWR using Modified Dietz method
        if len(portfolio_values) < 2:
            return {"twr": 0, "period_return": 0, "annualized_return": 0}
        
        beginning_value = portfolio_values[0]
        ending_value = portfolio_values[-1]
        net_cash_flow = sum(cash_flows)
        
        # Simplified TWR calculation
        if beginning_value > 0:
            period_return = ((ending_value - beginning_value - net_cash_flow) / beginning_value) * 100
        else:
            period_return = 0
        
        # Annualize return
        days = (end_date - start_date).days
        if days > 0:
            annualized_return = (1 + period_return / 100) ** (365 / days) - 1
            annualized_return *= 100
        else:
            annualized_return = 0
        
        return {
            "twr": period_return,
            "period_return": period_return,
            "annualized_return": annualized_return,
            "beginning_value": beginning_value,
            "ending_value": ending_value,
            "net_cash_flow": net_cash_flow
        }
    
    def calculate_portfolio_statistics(self, portfolio_id: int, start_date: date, end_date: date) -> Dict:
        """Calculate comprehensive portfolio statistics"""
        twr_data = self.calculate_time_weighted_return(portfolio_id, start_date, end_date)
        
        # Get daily returns for volatility calculation
        daily_returns = []
        current_date = start_date
        prev_value = None
        
        while current_date <= end_date:
            value = self.calculate_portfolio_value(portfolio_id, current_date)["total_value"]
            if prev_value is not None and prev_value > 0:
                daily_return = (float(value) - float(prev_value)) / float(prev_value)
                daily_returns.append(daily_return)
            prev_value = value
            current_date += timedelta(days=1)
        
        # Calculate statistics
        if len(daily_returns) > 0:
            volatility = np.std(daily_returns) * np.sqrt(252)  # Annualized volatility
            max_drawdown = self._calculate_max_drawdown(daily_returns)
            sharpe_ratio = (twr_data["annualized_return"] / 100) / volatility if volatility > 0 else 0
        else:
            volatility = 0
            max_drawdown = 0
            sharpe_ratio = 0
        
        return {
            "time_weighted_return": twr_data["twr"],
            "annualized_return": twr_data["annualized_return"],
            "volatility": volatility * 100,
            "max_drawdown": max_drawdown * 100,
            "sharpe_ratio": sharpe_ratio,
            "beginning_value": twr_data["beginning_value"],
            "ending_value": twr_data["ending_value"],
            "period_days": (end_date - start_date).days
        }
    
    def _calculate_max_drawdown(self, returns: List[float]) -> float:
        """Calculate maximum drawdown"""
        if not returns:
            return 0
        
        cumulative = np.cumprod(1 + np.array(returns))
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return float(np.min(drawdown))
    
    def get_asset_allocation(self, portfolio_id: int) -> Dict:
        """Get asset allocation by type and sector"""
        holdings = self.session.exec(
            select(Holding).where(Holding.portfolio_id == portfolio_id)
        ).all()
        
        allocation_by_type = defaultdict(Decimal)
        allocation_by_sector = defaultdict(Decimal)
        total_value = Decimal('0')
        
        for holding in holdings:
            if holding.market_value:
                asset = self.session.get(Asset, holding.asset_id)
                allocation_by_type[asset.asset_type] += holding.market_value
                total_value += holding.market_value
                
                # Get sector from asset metadata
                sector_meta = self.session.exec(
                    select(AssetMetadata)
                    .where(AssetMetadata.asset_id == asset.id)
                    .where(AssetMetadata.attribute_name == "sector")
                ).first()
                
                if sector_meta:
                    allocation_by_sector[sector_meta.attribute_value] += holding.market_value
                else:
                    allocation_by_sector["Unknown"] += holding.market_value
        
        # Convert to percentages
        type_percentages = {
            asset_type: float(value / total_value * 100) if total_value > 0 else 0
            for asset_type, value in allocation_by_type.items()
        }
        
        sector_percentages = {
            sector: float(value / total_value * 100) if total_value > 0 else 0
            for sector, value in allocation_by_sector.items()
        }
        
        return {
            "by_type": type_percentages,
            "by_sector": sector_percentages,
            "total_value": float(total_value)
        } 