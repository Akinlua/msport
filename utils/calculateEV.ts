/**
 * Calculate the Expected Value (EV) percentage for a bet
 * @param decimalOdds The decimal odds you're getting from the bookmaker
 * @param noVigPrice The true probability (derived from no-vig price)
 * @returns The expected value as a percentage
 */
export const calculateEV = (decimalOdds: number, noVigPrice: number): number => {
    // Convert no-vig price to true probability
    const trueProb = noVigPrice;
    
    // Calculate EV%
    const evPercentage = ((decimalOdds * trueProb) - 1) * 100;
    
    return evPercentage;
}; 