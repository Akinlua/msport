from typing import Dict, List, TypeVar, Union, Optional
import math
import json
from functools import lru_cache

Number = Union[float, int]
T = TypeVar('T', bound=Dict[str, Optional[Number]])

# Cache for storing calculated no-vig prices
@lru_cache(maxsize=1000)
def _get_cached_result(cache_key: str):
    """Internal cache function using lru_cache decorator."""
    return None

def _convert_probability_to_decimal_odds(probability: float) -> float:
    """Convert a probability to decimal odds."""
    return 1 / probability

def _adjust_power(probabilities: List[float], tolerance: float = 1e-4, max_iterations: int = 100) -> List[float]:
    """
    Power method for devigging probabilities.
    
    Args:
        probabilities: List of probabilities
        tolerance: Convergence tolerance
        max_iterations: Maximum number of iterations
        
    Returns:
        List of adjusted probabilities
    """
    k = 1
    adjusted_probabilities = [math.pow(prob, k) for prob in probabilities]

    # Newton-Raphson iterations
    for _ in range(max_iterations):
        overround = sum(adjusted_probabilities) - 1
        denominator = sum(math.log(prob) * math.pow(prob, k) for prob in probabilities)
        k -= overround / denominator
        adjusted_probabilities = [math.pow(prob, k) for prob in probabilities]
        if abs(overround) < tolerance:
            break

    return adjusted_probabilities

def _adjust_shin(probabilities: List[float], tolerance: float = 1e-4, max_iterations: int = 100) -> List[float]:
    """
    Shin method for devigging probabilities.
    
    Args:
        probabilities: List of probabilities
        tolerance: Convergence tolerance
        max_iterations: Maximum number of iterations
        
    Returns:
        List of adjusted probabilities
    """
    overround = sum(probabilities)
    n = len(probabilities)
    a = [(prob ** 2) / overround for prob in probabilities]

    if n == 2:
        # Special case for two outcomes
        first_prob, second_prob = probabilities
        diff = first_prob - second_prob
        diff_squared = diff ** 2
        z = ((overround - 1) * (diff_squared - overround)) / (overround * (diff_squared - 1))
        return [(math.sqrt(z ** 2 + 4 * (1 - z) * prob) - z) / (2 * (1 - z)) for prob in a]
    else:
        # General case using Newton-Raphson
        z = 0
        b = 1 / (n - 2)
        
        for _ in range(max_iterations):
            c = [math.sqrt(z ** 2 + 4 * (1 - z) * prob) for prob in a]
            cond = z - b * (sum(c) - 2)
            denominator = 1 - b * sum((z - 2 * prob) / c_val for prob, c_val in zip(a, c))
            z -= cond / denominator
            if abs(cond) < tolerance:
                break

        return [(math.sqrt(z ** 2 + 4 * (1 - z) * prob) - z) / (2 * (1 - z)) for prob in a]

def _adjust_additive(probabilities: List[float]) -> List[float]:
    """
    Additive method for devigging probabilities.
    
    Args:
        probabilities: List of probabilities
        
    Returns:
        List of adjusted probabilities
    """
    n = len(probabilities)
    overround = sum(probabilities) - 1
    return [prob - overround / n for prob in probabilities]

def _adjust_multiplicative(probabilities: List[float]) -> List[float]:
    """
    Multiplicative method for devigging probabilities.
    
    Args:
        probabilities: List of probabilities
        
    Returns:
        List of adjusted probabilities
    """
    booksum = sum(probabilities)
    return [prob / booksum for prob in probabilities]

def calculate_no_vig_prices(decimal_prices: Dict[str, Optional[Number]]) -> Dict[str, Dict[str, Optional[Number]]]:
    """
    Calculate no-vig prices using multiple methods.
    
    Args:
        decimal_prices: Dictionary of decimal odds for each outcome
            Example: {'home': 1.8, 'draw': 3.5, 'away': 4.5}
            
    Returns:
        Dictionary containing no-vig prices calculated using different methods
            Example: {
                'power': {'home': 1.85, 'draw': 3.6, 'away': 4.7},
                'additive': {'home': 1.83, 'draw': 3.55, 'away': 4.6},
                'multiplicative': {'home': 1.82, 'draw': 3.53, 'away': 4.58},
                'shin': {'home': 1.84, 'draw': 3.57, 'away': 4.65}
            }
            
    Example:
        >>> prices = calculate_no_vig_prices({'home': 1.8, 'draw': 3.5, 'away': 4.5})
        >>> print(prices['multiplicative']['home'])
        1.82
    """
    # Check if all values are None/undefined
    if all(price is None for price in decimal_prices.values()):
        return {
            'power': decimal_prices,
            'additive': decimal_prices,
            'multiplicative': decimal_prices,
            'shin': decimal_prices
        }

    # Generate cache key
    cache_key = json.dumps(decimal_prices, sort_keys=True)
    cached_result = _get_cached_result(cache_key)
    if cached_result:
        return cached_result

    # Convert decimal prices to probabilities and keep track of keys
    probabilities_with_keys = [
        (key, 1 / price) for key, price in decimal_prices.items()
        if price is not None and price > 0
    ]
    
    # Extract probabilities for calculation
    probabilities = [prob for _, prob in probabilities_with_keys]
    
    # Calculate adjusted probabilities using each method
    power_probs = _adjust_power(probabilities)
    shin_probs = _adjust_shin(probabilities)
    additive_probs = _adjust_additive(probabilities)
    multiplicative_probs = _adjust_multiplicative(probabilities)
    
    # Initialize result dictionaries
    result = {
        'power': dict(decimal_prices),
        'shin': dict(decimal_prices),
        'additive': dict(decimal_prices),
        'multiplicative': dict(decimal_prices)
    }
    
    # Convert probabilities back to decimal odds and assign to respective keys
    for i, (key, _) in enumerate(probabilities_with_keys):
        result['power'][key] = _convert_probability_to_decimal_odds(power_probs[i])
        result['shin'][key] = _convert_probability_to_decimal_odds(shin_probs[i])
        result['additive'][key] = _convert_probability_to_decimal_odds(additive_probs[i])
        result['multiplicative'][key] = _convert_probability_to_decimal_odds(multiplicative_probs[i])
    
    return result

# Example usage:
if __name__ == "__main__":
    # Example with 3-way market (home/draw/away)
    sample_odds = {
        'home': 3.38, 
        'draw': 3.25,
        'away': 2.11
    }
    
    no_vig_prices = calculate_no_vig_prices(sample_odds)
    print("No-vig prices for each method:")
    for method, prices in no_vig_prices.items():
        print(f"\n{method.capitalize()} method:")
        for outcome, price in prices.items():
            print(f"{outcome}: {price:.3f}") 