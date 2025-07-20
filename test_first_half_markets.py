#!/usr/bin/env python3
"""
Test script for first half market detection in MSport
"""

import json
from bet_engine import BetEngine

def test_first_half_market_detection():
    """Test first half market detection with sample event details"""
    print("=" * 60)
    print("TESTING FIRST HALF MARKET DETECTION")
    print("=" * 60)
    
    # Sample event details with first half markets
    sample_event_details = {
        "eventId": "sr:match:57490675",
        "homeTeam": "Fluminense",
        "awayTeam": "Al Hilal SFC",
        "markets": [
            {
                "description": "1x2",
                "outcomes": [
                    {"id": "1", "description": "Home", "odds": "2.15"},
                    {"id": "2", "description": "Draw", "odds": "3.25"},
                    {"id": "3", "description": "Away", "odds": "3.40"}
                ]
            },
            {
                "description": "1st half - 1x2",
                "outcomes": [
                    {"id": "1", "description": "Home", "odds": "2.80"},
                    {"id": "2", "description": "Draw", "odds": "2.10"},
                    {"id": "3", "description": "Away", "odds": "4.20"}
                ]
            },
            {
                "description": "over/under",
                "outcomes": [
                    {"id": "12", "description": "Over 2.5", "odds": "1.85"},
                    {"id": "13", "description": "Under 2.5", "odds": "1.95"}
                ]
            },
            {
                "description": "1st half - o/u",
                "outcomes": [
                    {"id": "12", "description": "Over 0.5", "odds": "1.60"},
                    {"id": "13", "description": "Under 0.5", "odds": "2.30"},
                    {"id": "12", "description": "Over 1.5", "odds": "3.10"},
                    {"id": "13", "description": "Under 1.5", "odds": "1.35"}
                ]
            },
            {
                "description": "asian handicap",
                "outcomes": [
                    {"id": "1714", "description": "Home (-0.5)", "odds": "1.90"},
                    {"id": "1715", "description": "Away (+0.5)", "odds": "1.90"}
                ]
            },
            {
                "description": "1st half - asian handicap",
                "outcomes": [
                    {"id": "1714", "description": "Home (-0.25)", "odds": "2.05"},
                    {"id": "1715", "description": "Away (+0.25)", "odds": "1.75"}
                ]
            }
        ]
    }
    
    # Initialize BetEngine (without browser)
    bet_engine = BetEngine(headless=True, config_file="config.json")
    
    # Test cases for first half markets
    test_cases = [
        {
            "description": "Full Match - Moneyline Home",
            "line_type": "money_line",
            "outcome": "home",
            "points": None,
            "is_first_half": False,
            "expected_market": "1x2"
        },
        {
            "description": "First Half - Moneyline Home",
            "line_type": "money_line",
            "outcome": "home",
            "points": None,
            "is_first_half": True,
            "expected_market": "1st half - 1x2"
        },
        {
            "description": "Full Match - Total Over 2.5",
            "line_type": "total",
            "outcome": "over",
            "points": "2.5",
            "is_first_half": False,
            "expected_market": "over/under"
        },
        {
            "description": "First Half - Total Over 0.5",
            "line_type": "total",
            "outcome": "over",
            "points": "0.5",
            "is_first_half": True,
            "expected_market": "1st half - o/u"
        },
        {
            "description": "Full Match - Asian Handicap Home -0.5",
            "line_type": "spread",
            "outcome": "home",
            "points": "-0.5",
            "is_first_half": False,
            "expected_market": "asian handicap"
        },
        {
            "description": "First Half - Asian Handicap Home -0.25",
            "line_type": "spread",
            "outcome": "home",
            "points": "-0.25",
            "is_first_half": True,
            "expected_market": "1st half - asian handicap"
        }
    ]
    
    print(f"Testing with event: {sample_event_details['homeTeam']} vs {sample_event_details['awayTeam']}")
    print()
    
    results = []
    for test_case in test_cases:
        print(f"Test: {test_case['description']}")
        print(f"  Market Type: {test_case['line_type']}")
        print(f"  Outcome: {test_case['outcome']}")
        print(f"  Points: {test_case['points']}")
        print(f"  First Half: {test_case['is_first_half']}")
        print(f"  Expected Market: {test_case['expected_market']}")
        
        try:
            outcome_id, odds, adjusted_points = bet_engine._BetEngine__find_market_bet_code_with_points(
                sample_event_details,
                test_case["line_type"],
                test_case["points"],
                test_case["outcome"],
                test_case["is_first_half"],
                1,  # sport_id (soccer)
                sample_event_details["homeTeam"],
                sample_event_details["awayTeam"]
            )
            
            if outcome_id and odds:
                print(f"  ✅ FOUND: Outcome ID: {outcome_id}, Odds: {odds}, Adjusted Points: {adjusted_points}")
                results.append(True)
            else:
                print(f"  ❌ NOT FOUND")
                results.append(False)
                
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            results.append(False)
        
        print("-" * 40)
    
    # Summary
    passed = sum(results)
    total = len(results)
    print(f"\nSUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All first half market detection tests passed!")
    else:
        print("⚠️  Some tests failed. Check market descriptions and logic.")
    
    # Cleanup
    bet_engine.cleanup()
    
    return passed == total

if __name__ == "__main__":
    success = test_first_half_market_detection()
    exit(0 if success else 1) 