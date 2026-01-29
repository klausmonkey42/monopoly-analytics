#!/usr/bin/env python3
"""
Quick test to verify the simulator is working
"""

print("Testing Monopoly Simulator Setup...")
print("="*60)

# Test 1: Load board
print("\n1. Testing board loading...")
try:
    from properties import load_board
    board = load_board()
    print(f"   ✓ Board loaded successfully: {len(board.properties)} properties")
except Exception as e:
    print(f"   ✗ Error loading board: {e}")
    exit(1)

# Test 2: Create game
print("\n2. Testing game state creation...")
try:
    from game_state import create_game
    player_configs = [
        {'name': 'Test Player', 'cash': 1500, 'position': 0, 
         'owned_properties': [], 'risk_tolerance': 0.5}
    ]
    game = create_game(board, player_configs)
    print(f"   ✓ Game created with {len(game.players)} player(s)")
except Exception as e:
    print(f"   ✗ Error creating game: {e}")
    exit(1)

# Test 3: Run a tiny simulation
print("\n3. Testing simulation engine...")
try:
    from simulator import MonopolySimulator
    simulator = MonopolySimulator(board)
    
    player_configs = [
        {'name': 'You', 'cash': 3500, 'position': 20, 
         'owned_properties': [31], 'risk_tolerance': 0.6},
        {'name': 'Opponent', 'cash': 1500, 'position': 0, 
         'owned_properties': [], 'risk_tolerance': 0.5}
    ]
    
    # Run just 10 simulations as a quick test
    results = simulator.run_monte_carlo(
        target_player_idx=0,
        target_property_position=32,
        player_configs=player_configs,
        num_simulations=10,
        max_turns=50
    )
    
    print(f"   ✓ Ran {results['num_simulations']} simulations successfully")
    print(f"   ✓ Property analyzed: {results['property_name']}")
except Exception as e:
    print(f"   ✗ Error running simulation: {e}")
    exit(1)

# Test 4: Analytics
print("\n4. Testing analytics module...")
try:
    from analytics import analyze_property_investment
    analysis = analyze_property_investment(results, discount_rate=0.05)
    print(f"   ✓ Analytics calculated")
    print(f"   ✓ Recommendation: {analysis['recommendation']}")
except Exception as e:
    print(f"   ✗ Error in analytics: {e}")
    exit(1)

print("\n" + "="*60)
print("✅ ALL TESTS PASSED!")
print("="*60)
print("\nYour simulator is ready to use!")
print("\nRun the full analysis with:")
print("  python main.py")
print("\nOr create your own test with:")
print("  python test.py")
