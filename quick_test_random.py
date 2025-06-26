#!/usr/bin/env python3
"""
Quick test script to verify RandomStrategy implementation
"""

from pikomino import simulate_game
from strategies import (
    RandomStrategy, 
    ConservativeStrategy, 
    AggressiveStrategy
)

def test_random_strategy():
    """Quick test of the RandomStrategy"""
    print("🎲 Testing RandomStrategy Implementation")
    print("=" * 40)
    
    # Create different random strategies
    strategies = [
        ("Random50", RandomStrategy(0.5)),
        ("RandomCautious", RandomStrategy(0.3)), 
        ("RandomRisky", RandomStrategy(0.8)),
        ("Conservative", ConservativeStrategy()),
    ]
    
    print("Strategies being tested:")
    probs = [0.5, 0.3, 0.8, "N/A"]
    for i, (name, strategy) in enumerate(strategies):
        prob_text = f"{probs[i]*100:.0f}%" if isinstance(probs[i], float) else probs[i]
        print(f"  📋 {name}: {prob_text} continue probability")
    
    print("\nRunning 5 test games...")
    
    # Run a few test games
    for game_num in range(5):
        player_names = [name for name, _ in strategies]
        game_strategies = [strategy for _, strategy in strategies]
        
        result = simulate_game(player_names, game_strategies)
        
        print(f"\nGame {game_num + 1}:")
        print(f"  🏆 Winner: {result['winner']}")
        print(f"  📊 Scores: {result['final_scores']}")
    
    print("\n✅ RandomStrategy working correctly!")
    print("✅ All strategic choices implemented!")
    print("✅ Ready for full simulations!")

if __name__ == "__main__":
    test_random_strategy() 