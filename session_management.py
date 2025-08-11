# --- Session Management Module ---
"""
Trading session analysis and time-based adjustments
"""

import datetime
from typing import Optional, Dict, Any
from logger_utils import logger
from config import TRADING_SESSIONS, CRITICAL_NEWS_TIMES


def is_high_impact_news_time() -> bool:
    """Enhanced high-impact news detection with basic time-based filtering"""
    try:
        # Basic time-based news schedule (UTC)
        utc_now = datetime.datetime.now()
        current_hour = utc_now.hour
        current_minute = utc_now.minute
        day_of_week = utc_now.weekday()  # 0=Monday, 6=Sunday
        
        # Critical news times (UTC) - avoid trading during these
        critical_times = list(CRITICAL_NEWS_TIMES)
        
        # Weekly specifics
        if day_of_week == 2:  # Wednesday FOMC minutes
            critical_times.append((13, 0, 14, 0))
        if day_of_week == 4:  # Friday NFP + major data
            critical_times.append((12, 30, 15, 0))
        
        current_time_minutes = current_hour * 60 + current_minute
        
        for start_h, start_m, end_h, end_m in critical_times:
            start_minutes = start_h * 60 + start_m
            end_minutes = end_h * 60 + end_m
            
            if start_minutes <= current_time_minutes <= end_minutes:
                logger(f"⚠️ High-impact news time detected: {current_hour:02d}:{current_minute:02d} UTC")
                return True
        
        return False
        
    except Exception as e:
        logger(f"❌ Error in news time check: {str(e)}")
        return False  # Continue trading if check fails


def get_current_trading_session() -> Optional[Dict[str, Any]]:
    """Enhanced trading session detection with session characteristics"""
    try:
        utc_now = datetime.datetime.now()
        current_hour = utc_now.hour
        day_of_week = utc_now.weekday()  # 0=Monday, 6=Sunday
        
        # Weekend check
        if day_of_week >= 5:  # Saturday or Sunday
            return {
                'name': 'Weekend',
                'active': False,
                'volatility': 'NONE',
                'recommended_pairs': [],
                'risk_modifier': 0.0
            }
        
        # Determine active session
        session_data = {
            'time_utc': current_hour,
            'day_of_week': day_of_week,
            'active': True
        }
        
        if 0 <= current_hour < 9:  # Asian session
            session_data.update({
                'name': 'Asian',
                'volatility': 'LOW',
                'recommended_pairs': ['USDJPY', 'AUDUSD', 'NZDUSD'],
                'risk_modifier': 0.8,  # Lower risk during low volatility
                'characteristics': ['Range-bound', 'Lower spreads', 'JPY pairs active']
            })
            
        elif 8 <= current_hour < 17:  # European session
            session_data.update({
                'name': 'European', 
                'volatility': 'HIGH',
                'recommended_pairs': ['EURUSD', 'GBPUSD', 'EURGBP', 'XAUUSD'],
                'risk_modifier': 1.2,  # Higher risk during high volatility
                'characteristics': ['High volatility', 'Trending markets', 'EUR/GBP pairs active']
            })
            
        elif 13 <= current_hour < 22:  # US session (overlap with European)
            if 13 <= current_hour < 17:  # US-European overlap
                session_data.update({
                    'name': 'US-European Overlap',
                    'volatility': 'VERY_HIGH',
                    'recommended_pairs': ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD'],
                    'risk_modifier': 1.5,  # Highest risk during overlap
                    'characteristics': ['Maximum volatility', 'Strong trends', 'Major news impact']
                })
            else:  # US session only
                session_data.update({
                    'name': 'US',
                    'volatility': 'MEDIUM',
                    'recommended_pairs': ['EURUSD', 'GBPUSD', 'USDCAD'],
                    'risk_modifier': 1.0,  # Standard risk
                    'characteristics': ['Moderate volatility', 'USD pairs active', 'Commodity influence']
                })
                
        else:  # Pacific session (21-24 UTC)
            session_data.update({
                'name': 'Pacific',
                'volatility': 'LOW',
                'recommended_pairs': ['AUDUSD', 'NZDUSD', 'USDJPY'],
                'risk_modifier': 0.7,  # Lower risk
                'characteristics': ['Lower activity', 'Range-bound', 'Preparing for Asian open']
            })
        
        return session_data
        
    except Exception as e:
        logger(f"❌ Error getting current trading session: {str(e)}")
        return None


def calculate_session_time_progress(current_hour: int, start_hour: int, end_hour: int) -> float:
    """Calculate progress through current trading session"""
    try:
        if end_hour > start_hour:
            total_hours = end_hour - start_hour
            elapsed_hours = current_hour - start_hour
        else:  # Session crosses midnight
            total_hours = (24 - start_hour) + end_hour
            if current_hour >= start_hour:
                elapsed_hours = current_hour - start_hour
            else:
                elapsed_hours = (24 - start_hour) + current_hour
                
        progress = min(max(elapsed_hours / total_hours, 0.0), 1.0)
        return progress
        
    except Exception as e:
        logger(f"❌ Error calculating session progress: {str(e)}")
        return 0.5


def get_session_priority(volatility: str) -> int:
    """Get session priority based on volatility"""
    priority_map = {
        'VERY_HIGH': 5,
        'HIGH': 4,
        'MEDIUM': 3,
        'LOW': 2,
        'NONE': 1
    }
    return priority_map.get(volatility, 3)


def get_session_optimal_symbols(session_name: str) -> list[str]:
    """Get optimal symbols for current session"""
    session_symbols = {
        'Asian': ['USDJPY', 'AUDUSD', 'NZDUSD', 'EURJPY', 'GBPJPY'],
        'European': ['EURUSD', 'GBPUSD', 'EURGBP', 'XAUUSD', 'EURJPY'],
        'US': ['EURUSD', 'GBPUSD', 'USDCAD', 'XAUUSD', 'USDJPY'],
        'US-European Overlap': ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'USDCAD'],
        'Pacific': ['AUDUSD', 'NZDUSD', 'USDJPY', 'EURAUD', 'AUDNZD'],
        'Weekend': []
    }
    return session_symbols.get(session_name, ['EURUSD', 'GBPUSD', 'USDJPY'])


def adjust_strategy_for_session(strategy: str, session_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Adjust strategy parameters based on current trading session"""
    try:
        if not session_data:
            return {"signal_threshold_modifier": 0, "risk_modifier": 1.0}
            
        volatility = session_data.get('volatility', 'MEDIUM')
        session_name = session_data.get('name', 'Unknown')
        risk_modifier = session_data.get('risk_modifier', 1.0)
        
        adjustments = {
            "signal_threshold_modifier": 0,
            "risk_modifier": risk_modifier,
            "session_name": session_name,
            "volatility": volatility
        }
        
        # Volatility-based adjustments
        if volatility == 'VERY_HIGH':
            adjustments["signal_threshold_modifier"] = 1  # Require stronger signals
        elif volatility == 'HIGH':
            adjustments["signal_threshold_modifier"] = 0  # Standard signals
        elif volatility == 'LOW':
            adjustments["signal_threshold_modifier"] = -1  # Allow weaker signals
        
        # Strategy-specific session adjustments
        if strategy == "Scalping":
            if volatility in ['VERY_HIGH', 'HIGH']:
                adjustments["signal_threshold_modifier"] += 0  # Scalping loves volatility
            else:
                adjustments["signal_threshold_modifier"] += 1  # More cautious in low volatility
                
        elif strategy == "Intraday":
            if volatility == 'VERY_HIGH':
                adjustments["signal_threshold_modifier"] += 1  # More cautious in extreme volatility
            elif volatility == 'LOW':
                adjustments["signal_threshold_modifier"] -= 1  # More aggressive in low volatility
                
        elif strategy == "HFT":
            if volatility in ['VERY_HIGH', 'HIGH']:
                adjustments["signal_threshold_modifier"] -= 1  # HFT thrives on volatility
            else:
                adjustments["signal_threshold_modifier"] += 2  # Very cautious in low volatility
                
        elif strategy == "Arbitrage":
            # Arbitrage works best in any volatility
            adjustments["signal_threshold_modifier"] += 0
        
        logger(f"📊 Session adjustments for {strategy}: {adjustments}")
        
        return adjustments
        
    except Exception as e:
        logger(f"❌ Error adjusting strategy for session: {str(e)}")
        return {"signal_threshold_modifier": 0, "risk_modifier": 1.0}


def check_trading_time() -> bool:
    """Check if current time is suitable for trading"""
    try:
        session = get_current_trading_session()
        if not session:
            return False
            
        if not session.get('active', False):
            logger("⏰ Market closed - outside trading hours")
            return False
            
        if is_high_impact_news_time():
            logger("⚠️ High impact news time - trading suspended")
            return False
            
        return True
        
    except Exception as e:
        logger(f"❌ Error checking trading time: {str(e)}")
        return False  # Err on the side of caution