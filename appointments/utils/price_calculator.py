"""
Utility functions for price calculations.
"""
import logging

logger = logging.getLogger(__name__)

def calculate_price(service, shift, special_price=None):
    """
    Calculate the price for a service based on the shift and any special pricing.
    
    Args:
        service: The service model instance
        shift: The shift (MORNING, AFTERNOON, EVENING)
        special_price: Optional special price to override calculations
        
    Returns:
        float: The calculated price
    """
    try:
        if special_price is not None and special_price > 0:
            return float(special_price)
            
        # Base price from the service
        base_price = service.base_price
        
        # Apply shift-based pricing
        if shift == 'EVENING':
            # Evening shift has 25% premium
            return float(base_price * 1.25)
        elif shift == 'AFTERNOON':
            # Afternoon shift has 10% premium
            return float(base_price * 1.1)
        else:
            # Morning shift is standard price
            return float(base_price)
    except Exception as e:
        logger.error(f"Error calculating price: {e}")
        # Return base price as fallback
        return float(service.base_price if service else 0) 