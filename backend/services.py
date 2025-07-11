from sqlmodel import Session, select
from typing import List, Dict, Optional, Tuple
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pandas as pd
import numpy as np
from collections import defaultdict

from models import (
    Currency,
    ExchangeRate,
    Asset,
    AssetMetadata,
    Transaction,
    Price,
    Portfolio,
    PortfolioStatistics,
    Position,
    get_session,
)


class CurrencyService:
    """Service for currency conversion and management"""

    def __init__(self, session: Session):
        self.session = session

    def get_primary_currency(self) -> Currency:
        """Get the primary currency"""
        primary = self.session.exec(
            select(Currency).where(Currency.is_primary == True)
        ).first()
        if not primary:
            # Create CNY as default primary currency
            primary = Currency(
                code="CNY", name="Chinese Yuan", symbol="¥", is_primary=True
            )
            self.session.add(primary)
            self.session.commit()
            self.session.refresh(primary)
        return primary

    def get_exchange_rate(self, currency_id: int, rate_date: date) -> Decimal:
        """Get exchange rate for a currency on a specific date"""
        if currency_id == self.get_primary_currency().id:
            return Decimal("1.0")

        # Get the most recent exchange rate before or on the date
        rate = self.session.exec(
            select(ExchangeRate)
            .where(ExchangeRate.currency_id == currency_id)
            .where(ExchangeRate.rate_date <= rate_date)
            .order_by(ExchangeRate.rate_date.desc())
        ).first()

        return rate.rate_to_primary if rate else Decimal("1.0")

    def convert_to_primary_currency(
        self, amount: Decimal, currency_id: int, rate_date: date
    ) -> Decimal:
        """Convert amount to primary currency"""
        rate = self.get_exchange_rate(currency_id, rate_date)
        return amount * rate


class PriceService:
    """Service for price management"""

    def __init__(self, session: Session):
        self.session = session

    def get_latest_price(
        self, asset_id: int, as_of_date: date = None
    ) -> Optional[Price]:
        """Get the latest price for an asset"""
        if as_of_date is None:
            as_of_date = date.today()

        # Check if this is a cash asset
        asset = self.session.get(Asset, asset_id)
        if asset and asset.asset_type == "cash":
            # Cash assets always have a price of 1.0
            return Price(
                asset_id=asset_id,
                price_date=as_of_date,
                price=Decimal("1.0"),
                price_type="real_time",
                source="system",
            )

        price = self.session.exec(
            select(Price)
            .where(Price.asset_id == asset_id)
            .where(Price.price_date <= as_of_date)
            .order_by(Price.price_date.desc())
        ).first()

        return price

    def get_price_history(
        self, asset_id: int, start_date: date, end_date: date
    ) -> List[Price]:
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

    def get_cash_asset(self, currency_id: int) -> Asset | None:
        """Get the cash asset for a given currency"""
        # Get currency code
        currency = self.session.get(Currency, currency_id)
        if not currency:
            return None

        # Find cash asset by symbol pattern
        cash_symbol = f"{currency.code}_CASH"
        cash_asset = self.session.exec(
            select(Asset)
            .where(Asset.symbol == cash_symbol)
            .where(Asset.asset_type == "cash")
        ).first()

        # Create cash asset if it doesn't exist
        if not cash_asset:
            cash_asset = Asset(
                symbol=cash_symbol,
                name=f"{currency.name} Cash",
                asset_type="cash",
                currency_id=currency_id,
                isin=f"{currency.code}_CASH",
            )
            self.session.add(cash_asset)
            self.session.commit()
            self.session.refresh(cash_asset)

        return cash_asset

    def process_transaction(
        self, transaction: Transaction, portfolio_id: int = 1
    ) -> Dict:
        """Process a transaction and update positions"""
        result = {"success": False, "message": ""}

        try:
            # Ensure cash transactions have the correct asset_id
            if transaction.action in ["cash_in", "cash_out"]:
                cash_asset = self.get_cash_asset(transaction.currency_id)
                if not cash_asset:
                    raise ValueError(
                        f"Cash asset not found for currency {transaction.currency_id}"
                    )
                transaction.asset_id = cash_asset.id

            if transaction.action in ["buy", "sell"]:
                self._process_trade_transaction(transaction, portfolio_id)
            elif transaction.action == "dividends":
                self._process_dividend_transaction(transaction, portfolio_id)
            elif transaction.action == "split":
                self._process_split_transaction(transaction, portfolio_id)
            elif transaction.action == "interest":
                self._process_interest_transaction(transaction, portfolio_id)
            elif transaction.action in ["cash_in", "cash_out"]:
                self._process_cash_transaction(transaction, portfolio_id)

            result["success"] = True
            result["message"] = (
                f"Transaction {transaction.action} processed successfully"
            )

        except Exception as e:
            result["message"] = f"Error processing transaction: {str(e)}"

        return result

    def _process_trade_transaction(self, transaction: Transaction, portfolio_id: int):
        """Process buy/sell transactions"""
        # Find or create position for the asset on the transaction date
        position = self.session.exec(
            select(Position)
            .where(Position.asset_id == transaction.asset_id)
            .where(Position.portfolio_id == portfolio_id)
            .where(Position.position_date == transaction.trade_date)
        ).first()

        if not position:
            position = Position(
                portfolio_id=portfolio_id,
                asset_id=transaction.asset_id,
                position_date=transaction.trade_date,
                quantity=Decimal("0"),
                average_cost=Decimal("0"),
            )
            self.session.add(position)

        # Get cash asset for the transaction currency
        cash_asset = self.get_cash_asset(transaction.currency_id)
        if not cash_asset:
            raise ValueError(
                f"Cash asset not found for currency {transaction.currency_id}"
            )

        # Find or create cash position
        cash_position = self.session.exec(
            select(Position)
            .where(Position.asset_id == cash_asset.id)
            .where(Position.portfolio_id == portfolio_id)
            .where(Position.position_date == transaction.trade_date)
        ).first()

        if not cash_position:
            cash_position = Position(
                portfolio_id=portfolio_id,
                asset_id=cash_asset.id,
                position_date=transaction.trade_date,
                quantity=Decimal("0"),
                average_cost=Decimal("1.0"),  # Cash always has a cost of 1.0
            )
            self.session.add(cash_position)

        # Calculate total cost including fees
        total_cost = transaction.amount + (transaction.fees or Decimal("0"))

        if transaction.action == "buy":
            # Check if we have enough cash
            if cash_position.quantity < total_cost:
                raise ValueError("Insufficient cash balance for purchase")

            # Update asset position
            existing_cost = position.average_cost * position.quantity
            position.quantity += transaction.quantity
            position.average_cost = (
                (existing_cost + transaction.amount) / position.quantity
                if position.quantity > 0
                else Decimal("0")
            )

            # Reduce cash position
            cash_position.quantity -= total_cost

        elif transaction.action == "sell":
            # Check if we have enough quantity to sell
            if position.quantity < transaction.quantity:
                raise ValueError("Insufficient quantity to sell")

            # Reduce asset position
            position.quantity -= transaction.quantity
            if position.quantity <= 0:
                self.session.delete(position)

            # Calculate proceeds (amount - fees)
            proceeds = transaction.amount - (transaction.fees or Decimal("0"))

            # Increase cash position
            cash_position.quantity += proceeds

        self.session.commit()

    def _process_dividend_transaction(
        self, transaction: Transaction, portfolio_id: int
    ):
        """Process dividend transactions"""
        # Add to cash balance
        # TODO: Implement dividend transactions
        pass

    def _process_split_transaction(self, transaction: Transaction, portfolio_id: int):
        """Process stock split transactions"""
        position = self.session.exec(
            select(Position)
            .where(Position.asset_id == transaction.asset_id)
            .where(Position.portfolio_id == portfolio_id)
            .where(Position.position_date == transaction.trade_date)
        ).first()

        if position:
            split_ratio = transaction.quantity  # e.g., 2 for 2-for-1 split
            position.quantity *= split_ratio
            position.average_cost /= split_ratio
            self.session.commit()

    def _process_interest_transaction(
        self, transaction: Transaction, portfolio_id: int
    ):
        """Process interest transactions"""
        # Add to cash balance
        # TODO: Implement interest transactions
        pass

    def _process_cash_transaction(self, transaction: Transaction, portfolio_id: int):
        """Process cash in/out transactions"""
        # Find or create position for cash asset
        position = self.session.exec(
            select(Position)
            .where(Position.asset_id == transaction.asset_id)
            .where(Position.portfolio_id == portfolio_id)
            .where(Position.position_date == transaction.trade_date)
        ).first()

        if not position:
            position = Position(
                portfolio_id=portfolio_id,
                asset_id=transaction.asset_id,
                position_date=transaction.trade_date,
                quantity=Decimal("0"),
                average_cost=Decimal("1.0"),  # Cash always has a cost of 1.0
            )
            self.session.add(position)

        # Update cash position
        if transaction.action == "cash_in":
            position.quantity += transaction.quantity
        elif transaction.action == "cash_out":
            position.quantity -= transaction.quantity
            if position.quantity < 0:
                raise ValueError("Insufficient cash balance")

        self.session.commit()


class PortfolioService:
    """Service for portfolio calculations and statistics"""

    def __init__(self, session: Session):
        self.session = session
        self.currency_service = CurrencyService(session)
        self.price_service = PriceService(session)

    def calculate_portfolio_value(
        self, portfolio_id: int, as_of_date: date = None
    ) -> Dict:
        """Calculate total portfolio value"""
        if as_of_date is None:
            as_of_date = date.today()

        # Try to get positions for the exact date
        positions = self.session.exec(
            select(Position)
            .where(Position.portfolio_id == portfolio_id)
            .where(Position.position_date == as_of_date)
        ).all()

        # If no positions found for the exact date, get latest positions
        if not positions:
            position_service = PositionService(self.session)
            positions = position_service.get_latest_positions(portfolio_id)

        if not positions:
            return {
                "total_value": Decimal("0"),
                "positions": [],
                "calculation_date": as_of_date,
            }

        total_value = Decimal("0")
        positions_value = []

        for position in positions:
            try:
                # Get latest price
                latest_price = self.price_service.get_latest_price(
                    position.asset_id, as_of_date
                )

                # If no price data available, use average cost as fallback
                if latest_price:
                    current_price = latest_price.price
                else:
                    current_price = position.average_cost

                # Calculate market value
                market_value = position.quantity * current_price

                # Convert to primary currency
                asset = self.session.get(Asset, position.asset_id)
                if asset:
                    market_value_primary = (
                        self.currency_service.convert_to_primary_currency(
                            market_value, asset.currency_id, as_of_date
                        )
                    )
                else:
                    market_value_primary = market_value

                total_value += market_value_primary

                # Update position
                position.current_price = current_price
                position.market_value = market_value_primary
                # Note: total_pnl is calculated separately using the PositionService

                positions_value.append(
                    {
                        "asset_id": position.asset_id,
                        "symbol": asset.symbol if asset else "Unknown",
                        "name": asset.name if asset else "Unknown",
                        "quantity": position.quantity,
                        "current_price": current_price,
                        "market_value": market_value_primary,
                        "total_pnl": position.total_pnl,
                    }
                )

            except Exception as e:
                print(
                    f"Error calculating position value for asset {position.asset_id}: {e}"
                )
                # Skip this position if there's an error
                continue

        try:
            self.session.commit()
        except Exception as e:
            print(f"Error committing portfolio value updates: {e}")
            self.session.rollback()

        return {
            "total_value": total_value,
            "positions": positions_value,
            "calculation_date": as_of_date,
        }

    def calculate_time_weighted_return(
        self, portfolio_id: int, start_date: date, end_date: date
    ) -> Dict:
        """Calculate Time-Weighted Return (TWR) for portfolio"""
        try:
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
                try:
                    # Calculate portfolio value
                    portfolio_value = self.calculate_portfolio_value(
                        portfolio_id, current_date
                    )["total_value"]

                    # Calculate cash flows for the day
                    daily_cash_flow = Decimal("0")
                    for transaction in daily_transactions.get(current_date, []):
                        if transaction.action in ["buy", "cash_in"]:
                            daily_cash_flow += transaction.amount
                        elif transaction.action in ["sell", "cash_out"]:
                            daily_cash_flow -= transaction.amount

                    portfolio_values.append(float(portfolio_value))
                    cash_flows.append(float(daily_cash_flow))
                    dates.append(current_date)

                except Exception as e:
                    print(f"Error calculating portfolio value for {current_date}: {e}")
                    # Skip this date if there's an error
                    pass

                current_date += timedelta(days=1)

            # Calculate TWR using Modified Dietz method
            if len(portfolio_values) < 2:
                return {
                    "twr": 0.0,
                    "period_return": 0.0,
                    "annualized_return": 0.0,
                    "beginning_value": 0.0,
                    "ending_value": 0.0,
                    "net_cash_flow": 0.0,
                }

            beginning_value = portfolio_values[0]
            ending_value = portfolio_values[-1]
            net_cash_flow = sum(cash_flows)

            # Simplified TWR calculation
            if beginning_value > 0:
                period_return = (
                    (ending_value - beginning_value - net_cash_flow) / beginning_value
                ) * 100
            else:
                period_return = 0.0

            # Annualize return
            days = (end_date - start_date).days
            if days > 0 and period_return is not None:
                try:
                    annualized_return = (1 + period_return / 100) ** (365 / days) - 1
                    annualized_return *= 100
                    # Ensure it's a real number
                    if (
                        np.iscomplex(annualized_return)
                        or np.isnan(annualized_return)
                        or np.isinf(annualized_return)
                    ):
                        annualized_return = 0.0
                    else:
                        annualized_return = float(np.real(annualized_return))
                except Exception as e:
                    print(f"Error calculating annualized return: {e}")
                    annualized_return = 0.0
            else:
                annualized_return = 0.0

            # Ensure all values are real numbers
            result = {
                "twr": float(period_return) if period_return is not None else 0.0,
                "period_return": (
                    float(period_return) if period_return is not None else 0.0
                ),
                "annualized_return": annualized_return,
                "beginning_value": float(beginning_value),
                "ending_value": float(ending_value),
                "net_cash_flow": float(net_cash_flow),
            }

            # Final validation to ensure no complex numbers
            for key, value in result.items():
                if np.iscomplex(value) or np.isnan(value) or np.isinf(value):
                    result[key] = 0.0
                else:
                    result[key] = float(np.real(value))

            return result

        except Exception as e:
            print(f"Error calculating time-weighted return: {e}")
            return {
                "twr": 0.0,
                "period_return": 0.0,
                "annualized_return": 0.0,
                "beginning_value": 0.0,
                "ending_value": 0.0,
                "net_cash_flow": 0.0,
            }

    def calculate_portfolio_statistics(
        self, portfolio_id: int, start_date: date, end_date: date
    ) -> Dict:
        """Calculate comprehensive portfolio statistics"""
        try:
            twr_data = self.calculate_time_weighted_return(
                portfolio_id, start_date, end_date
            )

            # Get daily returns for volatility calculation
            daily_returns = []
            current_date = start_date
            prev_value = None

            while current_date <= end_date:
                try:
                    value = self.calculate_portfolio_value(portfolio_id, current_date)[
                        "total_value"
                    ]
                    if prev_value is not None and prev_value > 0:
                        daily_return = (float(value) - float(prev_value)) / float(
                            prev_value
                        )
                        # Only add valid returns (not NaN, not infinite)
                        if not (np.isnan(daily_return) or np.isinf(daily_return)):
                            daily_returns.append(daily_return)
                    prev_value = value
                except Exception as e:
                    print(f"Error calculating portfolio value for {current_date}: {e}")
                    # Skip this date if there's an error
                    pass

                current_date += timedelta(days=1)

            # Calculate statistics with proper validation
            if len(daily_returns) > 1:
                # Convert to numpy array and ensure it's real
                returns_array = np.array(daily_returns, dtype=float)

                # Calculate volatility safely
                try:
                    volatility = np.std(returns_array, ddof=1) * np.sqrt(
                        252
                    )  # Annualized volatility
                    # Ensure volatility is real and positive
                    if (
                        np.iscomplex(volatility)
                        or np.isnan(volatility)
                        or np.isinf(volatility)
                    ):
                        volatility = 0.0
                    else:
                        volatility = float(np.real(volatility))
                except Exception as e:
                    print(f"Error calculating volatility: {e}")
                    volatility = 0.0

                # Calculate max drawdown safely
                try:
                    max_drawdown = self._calculate_max_drawdown(daily_returns)
                    if (
                        np.iscomplex(max_drawdown)
                        or np.isnan(max_drawdown)
                        or np.isinf(max_drawdown)
                    ):
                        max_drawdown = 0.0
                    else:
                        max_drawdown = float(np.real(max_drawdown))
                except Exception as e:
                    print(f"Error calculating max drawdown: {e}")
                    max_drawdown = 0.0

                # Calculate Sharpe ratio safely
                try:
                    annualized_return = twr_data.get("annualized_return", 0)
                    if (
                        volatility > 0
                        and not np.isnan(annualized_return)
                        and not np.isinf(annualized_return)
                    ):
                        sharpe_ratio = (annualized_return / 100) / volatility
                        if (
                            np.iscomplex(sharpe_ratio)
                            or np.isnan(sharpe_ratio)
                            or np.isinf(sharpe_ratio)
                        ):
                            sharpe_ratio = 0.0
                        else:
                            sharpe_ratio = float(np.real(sharpe_ratio))
                    else:
                        sharpe_ratio = 0.0
                except Exception as e:
                    print(f"Error calculating Sharpe ratio: {e}")
                    sharpe_ratio = 0.0
            else:
                volatility = 0.0
                max_drawdown = 0.0
                sharpe_ratio = 0.0

            # Ensure all return values are real numbers
            result = {
                "time_weighted_return": float(twr_data.get("twr", 0)),
                "annualized_return": float(twr_data.get("annualized_return", 0)),
                "volatility": volatility * 100,
                "max_drawdown": max_drawdown * 100,
                "sharpe_ratio": sharpe_ratio,
                "beginning_value": float(twr_data.get("beginning_value", 0)),
                "ending_value": float(twr_data.get("ending_value", 0)),
                "period_days": (end_date - start_date).days,
            }

            # Final validation to ensure no complex numbers
            for key, value in result.items():
                if np.iscomplex(value) or np.isnan(value) or np.isinf(value):
                    result[key] = 0.0
                else:
                    result[key] = float(np.real(value))

            return result

        except Exception as e:
            print(f"Error calculating portfolio statistics: {e}")
            # Return default values if calculation fails
            return {
                "time_weighted_return": 0.0,
                "annualized_return": 0.0,
                "volatility": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "beginning_value": 0.0,
                "ending_value": 0.0,
                "period_days": (end_date - start_date).days,
            }

    def _calculate_max_drawdown(self, returns: List[float]) -> float:
        """Calculate maximum drawdown"""
        if not returns or len(returns) < 2:
            return 0.0

        try:
            # Convert to numpy array and ensure it's real
            returns_array = np.array(returns, dtype=float)

            # Remove any NaN or infinite values
            returns_array = returns_array[
                ~(np.isnan(returns_array) | np.isinf(returns_array))
            ]

            if len(returns_array) < 2:
                return 0.0

            # Calculate cumulative returns
            cumulative = np.cumprod(1 + returns_array)

            # Calculate running maximum
            running_max = np.maximum.accumulate(cumulative)

            # Calculate drawdown
            drawdown = (cumulative - running_max) / running_max

            # Get maximum drawdown
            max_dd = np.min(drawdown)

            # Ensure result is real and valid
            if np.iscomplex(max_dd) or np.isnan(max_dd) or np.isinf(max_dd):
                return 0.0
            else:
                return float(np.real(max_dd))

        except Exception as e:
            print(f"Error calculating max drawdown: {e}")
            return 0.0

    def get_asset_allocation(self, portfolio_id: int, as_of_date: date = None) -> Dict:
        """Get asset allocation by type and sector"""
        if as_of_date is None:
            as_of_date = date.today()

        try:
            positions = self.session.exec(
                select(Position)
                .where(Position.portfolio_id == portfolio_id)
                .where(Position.position_date == as_of_date)
            ).all()

            if not positions:
                return {"by_type": {}, "by_sector": {}, "total_value": 0}

            allocation_by_type = defaultdict(Decimal)
            allocation_by_sector = defaultdict(Decimal)
            total_value = Decimal("0")

            for position in positions:
                try:
                    if position.market_value and position.market_value > 0:
                        asset = self.session.get(Asset, position.asset_id)
                        if asset:
                            allocation_by_type[
                                asset.asset_type
                            ] += position.market_value
                            total_value += position.market_value

                            # Get sector from asset metadata
                            sector_meta = self.session.exec(
                                select(AssetMetadata)
                                .where(AssetMetadata.asset_id == asset.id)
                                .where(AssetMetadata.attribute_name == "sector")
                            ).first()

                            if sector_meta:
                                allocation_by_sector[
                                    sector_meta.attribute_value
                                ] += position.market_value
                            else:
                                allocation_by_sector["Unknown"] += position.market_value
                except Exception as e:
                    print(f"Error processing position {position.id}: {e}")
                    continue

            # Convert to percentages
            type_percentages = {}
            sector_percentages = {}

            if total_value > 0:
                type_percentages = {
                    asset_type: float(value / total_value * 100)
                    for asset_type, value in allocation_by_type.items()
                }

                sector_percentages = {
                    sector: float(value / total_value * 100)
                    for sector, value in allocation_by_sector.items()
                }

            return {
                "by_type": type_percentages,
                "by_sector": sector_percentages,
                "total_value": float(total_value),
            }

        except Exception as e:
            print(f"Error calculating asset allocation: {e}")
            return {"by_type": {}, "by_sector": {}, "total_value": 0}


class PositionService:
    """Service for position calculations and management"""

    def __init__(self, session: Session):
        self.session = session
        self.currency_service = CurrencyService(session)
        self.price_service = PriceService(session)

    def get_initial_positions(
        self, portfolio_id: int, start_date: date
    ) -> list[Position]:
        """Get initial positions from database for a portfolio on a specific date"""
        positions = self.session.exec(
            select(Position)
            .where(Position.portfolio_id == portfolio_id)
            .where(Position.position_date == start_date)
        ).all()

        return positions

    def calculate_positions_for_period(
        self,
        portfolio_id: int,
        start_date: date,
        end_date: date,
        transactions: List[Transaction],
    ) -> Dict[int, Position]:
        """Calculate positions for a period based on initial positions and transactions"""
        # Get initial positions
        initial_positions = self.get_initial_positions(portfolio_id, start_date)

        # Initialize final positions with initial positions
        final_positions = {}
        for position in initial_positions:
            final_positions[position.asset_id] = Position(
                portfolio_id=portfolio_id,
                asset_id=position.asset_id,
                position_date=end_date,
                quantity=position.quantity,
                average_cost=position.average_cost,
                current_price=position.current_price,
                market_value=position.market_value,
                total_pnl=position.total_pnl or Decimal("0"),
            )

        # If no initial positions, start with empty positions
        if not final_positions:
            final_positions = {}

        # Filter and order transactions for the period by trade_date
        period_transactions = sorted(
            [t for t in transactions if start_date <= t.trade_date <= end_date],
            key=lambda t: t.trade_date,
        )

        # Track cash flows for total P&L calculation
        cash_flows = defaultdict(
            lambda: {
                "cash_paid_on_bought": Decimal("0"),
                "cash_received_on_sale": Decimal("0"),
                "dividends_received": Decimal("0"),
            }
        )

        # Process transactions
        for transaction in period_transactions:
            asset_id = transaction.asset_id

            # Initialize position if it doesn't exist
            if asset_id not in final_positions:
                final_positions[asset_id] = Position(
                    portfolio_id=portfolio_id,
                    asset_id=asset_id,
                    position_date=end_date,
                    quantity=Decimal("0"),
                    average_cost=Decimal("0"),
                    current_price=None,
                    market_value=None,
                    total_pnl=Decimal("0"),
                )

            position = final_positions[asset_id]

            if transaction.action == "buy":
                # Update average cost and quantity
                total_cost = position.average_cost * position.quantity
                position.quantity += transaction.quantity
                position.average_cost = (
                    total_cost + transaction.amount
                ) / position.quantity

                # Track cash paid
                cash_flows[asset_id]["cash_paid_on_bought"] += transaction.amount + (
                    transaction.fees or Decimal("0")
                )

            elif transaction.action == "sell":
                # Reduce quantity
                position.quantity -= transaction.quantity
                if position.quantity < 0:
                    position.quantity = Decimal("0")

                # Track cash received
                cash_flows[asset_id]["cash_received_on_sale"] += transaction.amount - (
                    transaction.fees or Decimal("0")
                )

            elif transaction.action == "dividends":
                # Track dividends received
                cash_flows[asset_id]["dividends_received"] += transaction.amount

            elif transaction.action == "split":
                # Handle stock splits
                split_ratio = transaction.quantity
                position.quantity *= split_ratio
                if position.average_cost > 0:
                    position.average_cost /= split_ratio

            elif transaction.action == "cash_in":
                # Add cash to position
                position.quantity += transaction.quantity
                position.average_cost = Decimal("1.0")  # Cash always has cost of 1.0

            elif transaction.action == "cash_out":
                # Remove cash from position
                position.quantity -= transaction.quantity
                position.average_cost = Decimal("1.0")  # Cash always has cost of 1.0

        # Calculate current prices and market values
        for asset_id, position in final_positions.items():
            # Get current price
            latest_price = self.price_service.get_latest_price(asset_id, end_date)
            if latest_price:
                position.current_price = latest_price.price
            elif position.current_price is None:
                position.current_price = position.average_cost

            # Calculate market value
            position.market_value = position.quantity * position.current_price

            # Calculate total P&L
            # If the asset is cash, set total_pnl to 0
            asset = self.session.get(Asset, position.asset_id)
            if asset and asset.asset_type == "cash":
                position.total_pnl = Decimal("0")
                continue
            position.total_pnl = (
                position.market_value
                + cash_flows[asset_id]["cash_received_on_sale"]
                + cash_flows[asset_id]["dividends_received"]
                - cash_flows[asset_id]["cash_paid_on_bought"]
            )

        return final_positions

    def save_positions(self, positions: Dict[int, Position]):
        """Save calculated positions to database"""
        for position in positions.values():
            # Check if position already exists for this date
            existing_position = self.session.exec(
                select(Position)
                .where(Position.portfolio_id == position.portfolio_id)
                .where(Position.asset_id == position.asset_id)
                .where(Position.position_date == position.position_date)
            ).first()

            if existing_position:
                # Update existing position
                existing_position.quantity = position.quantity
                existing_position.average_cost = position.average_cost
                existing_position.current_price = position.current_price
                existing_position.market_value = position.market_value
                existing_position.total_pnl = position.total_pnl
            else:
                # Add new position
                self.session.add(position)

        self.session.commit()

    def get_latest_positions(self, portfolio_id: int) -> List[Position]:
        """Get the latest positions for a portfolio"""
        # Get all positions for the portfolio
        positions = self.session.exec(
            select(Position)
            .where(Position.portfolio_id == portfolio_id)
            .order_by(Position.position_date.desc())
        ).all()

        # Get the latest position for each asset
        latest_positions = {}
        for position in positions:
            if position.asset_id not in latest_positions:
                latest_positions[position.asset_id] = position

        return list(latest_positions.values())

    def update_positions_for_period(
        self,
        portfolio_id: int,
        start_date: date,
        end_date: date,
        save_to_db: bool = True,
    ) -> Dict[int, Position]:
        """
        Calculate and optionally save positions for a given period.

        Args:
            portfolio_id: The portfolio ID
            start_date: Start date for the calculation period
            end_date: End date for the calculation period
            save_to_db: Whether to save the calculated positions to the database

        Returns:
            Dictionary of asset_id to Position objects
        """
        # Get all transactions for the portfolio
        transactions = self.session.exec(
            select(Transaction)
            .where(Transaction.portfolio_id == portfolio_id)
            .order_by(Transaction.trade_date)
        ).all()

        # Calculate positions for the period
        positions = self.calculate_positions_for_period(
            portfolio_id, start_date, end_date, transactions
        )

        # Save to database if requested
        if save_to_db:
            self.save_positions(positions)

        return positions
