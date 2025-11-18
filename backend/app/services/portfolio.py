"""
Portfolio management and trade execution logic.
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.database import Trade, Position, PortfolioSnapshot
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class PortfolioManager:
    """Manages simulated portfolio state and trade execution."""
    
    def __init__(self, db: Session, run_id: str = "live"):
        """
        Initialize portfolio manager.
        
        Args:
            db: Database session
            run_id: Identifier for this run (live, backtest ID, etc.)
        """
        self.db = db
        self.run_id = run_id
    
    def get_cash_balance(self) -> float:
        """Get current cash balance."""
        snapshot = self._get_latest_snapshot()
        if snapshot:
            return snapshot.cash_balance
        return settings.initial_cash
    
    def get_total_equity(self) -> float:
        """Get total portfolio equity (cash + position values)."""
        snapshot = self._get_latest_snapshot()
        if snapshot:
            return snapshot.total_equity
        return settings.initial_cash
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get current position for a symbol."""
        return self.db.query(Position).filter(
            Position.symbol == symbol
        ).first()
    
    def get_all_positions(self) -> List[Position]:
        """Get all open positions."""
        return self.db.query(Position).filter(
            Position.quantity > 0
        ).all()
    
    def execute_trade(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        timestamp: Optional[datetime] = None
    ) -> Trade:
        """
        Execute a simulated trade.
        
        Args:
            symbol: Trading pair symbol
            side: 'BUY' or 'SELL'
            quantity: Quantity to trade
            price: Execution price
            timestamp: Trade timestamp (defaults to now)
        
        Returns:
            Created Trade object
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Validate trade
        if side not in ['BUY', 'SELL']:
            raise ValueError(f"Invalid side: {side}")
        
        if quantity <= 0:
            raise ValueError(f"Invalid quantity: {quantity}")
        
        if price <= 0:
            raise ValueError(f"Invalid price: {price}")
        
        # Calculate trade value
        trade_value = quantity * price
        
        # Get current cash and position
        cash_balance = self.get_cash_balance()
        position = self.get_position(symbol)
        
        # Validate sufficient funds/position
        if side == 'BUY':
            if trade_value > cash_balance:
                raise ValueError(f"Insufficient cash: need {trade_value}, have {cash_balance}")
        elif side == 'SELL':
            if not position or position.quantity < quantity:
                current_qty = position.quantity if position else 0
                raise ValueError(f"Insufficient position: need {quantity}, have {current_qty}")
        
        # Create trade record
        trade = Trade(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            timestamp=timestamp,
            run_id=self.run_id
        )
        self.db.add(trade)
        
        # Update position
        if side == 'BUY':
            trade.pnl = 0.0  # No PnL on entry
            self._update_position_buy(symbol, quantity, price)
            new_cash = cash_balance - trade_value
        else:  # SELL
            # Calculate PnL
            trade.pnl = self._calculate_pnl(position, quantity, price)
            self._update_position_sell(symbol, quantity, price)
            new_cash = cash_balance + trade_value
        
        # Create portfolio snapshot
        self._create_snapshot(new_cash, timestamp)
        
        self.db.commit()
        logger.info(f"Executed {side} {quantity} {symbol} @ {price} (PnL: {trade.pnl})")
        
        return trade
    
    def _update_position_buy(self, symbol: str, quantity: float, price: float):
        """Update position after a buy."""
        position = self.get_position(symbol)
        
        if position:
            # Update existing position (calculate new average entry)
            total_cost = (position.quantity * position.avg_entry_price) + (quantity * price)
            position.quantity += quantity
            position.avg_entry_price = total_cost / position.quantity
        else:
            # Create new position
            position = Position(
                symbol=symbol,
                quantity=quantity,
                avg_entry_price=price,
                unrealized_pnl=0.0
            )
            self.db.add(position)
    
    def _update_position_sell(self, symbol: str, quantity: float, price: float):
        """Update position after a sell."""
        position = self.get_position(symbol)
        
        if not position:
            raise ValueError(f"No position found for {symbol}")
        
        position.quantity -= quantity
        
        if position.quantity <= 0:
            # Close position completely
            self.db.delete(position)
    
    def _calculate_pnl(self, position: Position, quantity: float, sell_price: float) -> float:
        """Calculate realized PnL for a sell trade."""
        if not position:
            return 0.0
        
        entry_value = quantity * position.avg_entry_price
        exit_value = quantity * sell_price
        pnl = exit_value - entry_value
        
        return pnl
    
    def update_unrealized_pnl(self, symbol: str, current_price: float):
        """Update unrealized PnL for a position."""
        position = self.get_position(symbol)
        
        if position and position.quantity > 0:
            current_value = position.quantity * current_price
            entry_value = position.quantity * position.avg_entry_price
            position.unrealized_pnl = current_value - entry_value
            self.db.commit()
    
    def update_all_unrealized_pnl(self, prices: Dict[str, float]):
        """Update unrealized PnL for all positions."""
        for symbol, price in prices.items():
            self.update_unrealized_pnl(symbol, price)
    
    def _create_snapshot(self, cash_balance: float, timestamp: Optional[datetime] = None):
        """Create a portfolio snapshot."""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Calculate total equity (cash + position values)
        positions = self.get_all_positions()
        total_position_value = sum(
            p.quantity * p.avg_entry_price + p.unrealized_pnl
            for p in positions
        )
        total_equity = cash_balance + total_position_value
        
        snapshot = PortfolioSnapshot(
            timestamp=timestamp,
            total_equity=total_equity,
            cash_balance=cash_balance,
            run_id=self.run_id
        )
        self.db.add(snapshot)
    
    def _get_latest_snapshot(self) -> Optional[PortfolioSnapshot]:
        """Get the most recent portfolio snapshot."""
        return self.db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.run_id == self.run_id
        ).order_by(PortfolioSnapshot.timestamp.desc()).first()
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current portfolio state.
        
        Returns:
            Dictionary with portfolio details
        """
        cash_balance = self.get_cash_balance()
        positions = self.get_all_positions()
        
        position_data = []
        total_position_value = 0.0
        total_unrealized_pnl = 0.0
        
        for pos in positions:
            position_value = pos.quantity * pos.avg_entry_price + pos.unrealized_pnl
            total_position_value += position_value
            total_unrealized_pnl += pos.unrealized_pnl
            
            position_data.append({
                'symbol': pos.symbol,
                'quantity': pos.quantity,
                'avg_entry_price': pos.avg_entry_price,
                'current_value': position_value,
                'unrealized_pnl': pos.unrealized_pnl,
                'updated_at': pos.updated_at.isoformat()
            })
        
        total_equity = cash_balance + total_position_value
        
        # Calculate realized PnL from trades
        realized_pnl = self.db.query(func.sum(Trade.pnl)).filter(
            Trade.run_id == self.run_id,
            Trade.pnl.isnot(None)
        ).scalar() or 0.0
        
        initial_cash = settings.initial_cash
        total_return = ((total_equity - initial_cash) / initial_cash) * 100
        
        return {
            'run_id': self.run_id,
            'cash_balance': cash_balance,
            'total_equity': total_equity,
            'total_position_value': total_position_value,
            'total_unrealized_pnl': total_unrealized_pnl,
            'realized_pnl': realized_pnl,
            'total_return_pct': total_return,
            'positions': position_data,
            'num_positions': len(position_data)
        }
    
    def get_trade_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent trade history."""
        trades = self.db.query(Trade).filter(
            Trade.run_id == self.run_id
        ).order_by(Trade.timestamp.desc()).limit(limit).all()
        
        return [
            {
                'id': t.id,
                'symbol': t.symbol,
                'side': t.side,
                'quantity': t.quantity,
                'price': t.price,
                'value': t.quantity * t.price,
                'pnl': t.pnl,
                'timestamp': t.timestamp.isoformat()
            }
            for t in trades
        ]
    
    def check_risk_limits(
        self,
        symbol: str,
        side: str,
        proposed_value: float
    ) -> tuple[bool, str]:
        """
        Check if a proposed trade violates risk limits.
        
        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            proposed_value: Value of proposed trade
        
        Returns:
            Tuple of (is_valid, reason)
        """
        if side == 'SELL':
            return True, "SELL trades reduce risk"
        
        total_equity = self.get_total_equity()
        
        # Check max position size
        max_position_value = total_equity * settings.max_position_size_pct
        current_position = self.get_position(symbol)
        current_value = 0.0
        if current_position:
            current_value = current_position.quantity * current_position.avg_entry_price
        
        new_position_value = current_value + proposed_value
        
        if new_position_value > max_position_value:
            return False, f"Exceeds max position size ({settings.max_position_size_pct*100}% of equity)"
        
        # Check total exposure
        total_position_value = sum(
            p.quantity * p.avg_entry_price
            for p in self.get_all_positions()
        )
        new_total_exposure = (total_position_value + proposed_value) / total_equity
        
        if new_total_exposure > settings.max_total_exposure_pct:
            return False, f"Exceeds max total exposure ({settings.max_total_exposure_pct*100}% of equity)"
        
        return True, "Within risk limits"


def initialize_portfolio(db: Session, run_id: str = "live"):
    """
    Initialize a new portfolio with starting cash.
    
    Args:
        db: Database session
        run_id: Portfolio run identifier
    """
    # Create initial snapshot
    snapshot = PortfolioSnapshot(
        timestamp=datetime.utcnow(),
        total_equity=settings.initial_cash,
        cash_balance=settings.initial_cash,
        run_id=run_id
    )
    db.add(snapshot)
    db.commit()
    
    logger.info(f"Initialized portfolio {run_id} with ${settings.initial_cash}")
