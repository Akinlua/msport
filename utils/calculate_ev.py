def calculate_ev(odds: float, no_vig_price: float) -> float:
    """
    Calculate the Expected Value (EV) percentage for a bet.
    
    Args:
        odds (float): The decimal odds you're getting from the bookmaker
        no_vig_price (float): The fair odds without the vig/juice
        
    Returns:
        float: The expected value as a percentage
        
    Example:
        >>> calculate_ev(2.0, 1.95)  # If fair odds are 1.95 but you're getting 2.0
        2.564102564102564  # Approximately 2.56% EV
    """
    fair_probability = 1 / no_vig_price
    return (fair_probability * odds - 1) * 100 