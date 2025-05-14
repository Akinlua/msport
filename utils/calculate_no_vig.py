def calculate_no_vig_price(home_odds: float, away_odds: float) -> tuple[float, float]:
    """
    Calculate no-vig probabilities from raw odds.
    
    Args:
        home_odds (float): Decimal odds for home team
        away_odds (float): Decimal odds for away team
        
    Returns:
        tuple[float, float]: No-vig prices for (home, away)
        
    Example:
        >>> home_nvp, away_nvp = calculate_no_vig_price(2.0, 1.8)
    """
    # Convert odds to probabilities
    home_prob = 1 / home_odds
    away_prob = 1 / away_odds
    
    # Calculate the vig/juice
    total_probability = home_prob + away_prob
    
    # Remove the vig by normalizing probabilities
    home_no_vig_prob = home_prob / total_probability
    away_no_vig_prob = away_prob / total_probability
    
    # Convert probabilities back to decimal odds
    home_no_vig_price = 1 / home_no_vig_prob
    away_no_vig_price = 1 / away_no_vig_prob
    
    return home_no_vig_price, away_no_vig_price

def calculate_no_vig_price_3way(home_odds: float, draw_odds: float, away_odds: float) -> tuple[float, float, float]:
    """
    Calculate no-vig probabilities for 3-way markets (like soccer).
    
    Args:
        home_odds (float): Decimal odds for home team
        draw_odds (float): Decimal odds for draw
        away_odds (float): Decimal odds for away team
        
    Returns:
        tuple[float, float, float]: No-vig prices for (home, draw, away)
        
    Example:
        >>> home_nvp, draw_nvp, away_nvp = calculate_no_vig_price_3way(2.5, 3.2, 2.8)
    """
    # Convert odds to probabilities
    home_prob = 1 / home_odds
    draw_prob = 1 / draw_odds
    away_prob = 1 / away_odds
    
    # Calculate the vig/juice
    total_probability = home_prob + draw_prob + away_prob
    
    # Remove the vig by normalizing probabilities
    home_no_vig_prob = home_prob / total_probability
    draw_no_vig_prob = draw_prob / total_probability
    away_no_vig_prob = away_prob / total_probability
    
    # Convert probabilities back to decimal odds
    home_no_vig_price = 1 / home_no_vig_prob
    draw_no_vig_price = 1 / draw_no_vig_prob
    away_no_vig_price = 1 / away_no_vig_prob
    
    return home_no_vig_price, draw_no_vig_price, away_no_vig_price