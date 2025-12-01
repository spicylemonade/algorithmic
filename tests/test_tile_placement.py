"""
Comprehensive tests for the tile placement solution.
"""

import sys
sys.path.insert(0, '/home/claude/work/repo/src')

from tile_placement import calculate_minimum_tiles, verify_configuration, solve_for_2025


def test_small_grids():
    """Test the formula on small grids."""
    print("Testing small grids...")

    test_cases = [
        (2, 2),   # 2×2 grid: 2*2 - 2 = 2 tiles
        (3, 4),   # 3×3 grid: 2*3 - 2 = 4 tiles
        (4, 6),   # 4×4 grid: 2*4 - 2 = 6 tiles
        (5, 8),   # 5×5 grid: 2*5 - 2 = 8 tiles
        (10, 18), # 10×10 grid: 2*10 - 2 = 18 tiles
    ]

    all_passed = True
    for n, expected in test_cases:
        result = calculate_minimum_tiles(n)
        passed = result == expected
        all_passed = all_passed and passed
        status = "✓" if passed else "✗"
        print(f"  {status} n={n}: Expected {expected}, Got {result}")

    return all_passed


def test_verification():
    """Test that our configuration is valid for small grids."""
    print("\nTesting configuration verification...")

    test_sizes = [2, 3, 4, 5, 7, 10]

    all_passed = True
    for n in test_sizes:
        min_tiles = calculate_minimum_tiles(n)
        is_valid = verify_configuration(n, min_tiles)
        all_passed = all_passed and is_valid
        status = "✓" if is_valid else "✗"
        print(f"  {status} n={n}: {min_tiles} tiles - Valid: {is_valid}")

    return all_passed


def test_2025_solution():
    """Test the specific solution for 2025."""
    print("\nTesting 2025×2025 solution...")

    result = solve_for_2025()
    expected = 4048  # 2*2025 - 2

    passed = result['minimum_tiles'] == expected
    status = "✓" if passed else "✗"
    print(f"  {status} Expected: {expected}, Got: {result['minimum_tiles']}")

    return passed


def test_edge_cases():
    """Test edge cases."""
    print("\nTesting edge cases...")

    all_passed = True

    # n=1: 0 tiles (single square is uncovered)
    result = calculate_minimum_tiles(1)
    passed = result == 0
    all_passed = all_passed and passed
    status = "✓" if passed else "✗"
    print(f"  {status} n=1: Expected 0, Got {result}")

    return all_passed


def visualize_small_grid(n=5):
    """
    Visualize the tiling for a small grid.
    Shows how the diagonal uncovered pattern works.
    """
    print(f"\nVisualizing {n}×{n} grid tiling:")
    print("  'X' = uncovered square (diagonal)")
    print("  Numbers = tile ID covering that square")
    print()

    # Create grid
    grid = [[-1] * n for _ in range(n)]

    # Mark uncovered squares
    for i in range(n):
        grid[i][i] = -2  # Special marker for uncovered

    tile_id = 1

    # Upper tiles: row i covers columns [i+1, n-1]
    for i in range(n - 1):
        if i + 1 < n:
            for c in range(i + 1, n):
                grid[i][c] = tile_id
            tile_id += 1

    # Lower tiles: row i covers columns [0, i-1]
    for i in range(1, n):
        if i > 0:
            for c in range(0, i):
                grid[i][c] = tile_id
            tile_id += 1

    # Print grid
    print("    ", end="")
    for j in range(n):
        print(f" {j:2}", end="")
    print()
    print("    " + "---" * n)

    for i in range(n):
        print(f" {i:2} |", end="")
        for j in range(n):
            if grid[i][j] == -2:
                print("  X", end="")
            elif grid[i][j] == -1:
                print("  .", end="")
            else:
                print(f" {grid[i][j]:2}", end="")
        print()

    print(f"\nTotal tiles used: {tile_id - 1}")
    print(f"Expected (2n-2): {2*n - 2}")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("RUNNING ALL TESTS")
    print("=" * 60)

    tests = [
        ("Small Grids", test_small_grids),
        ("Configuration Verification", test_verification),
        ("2025×2025 Solution", test_2025_solution),
        ("Edge Cases", test_edge_cases),
    ]

    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"  ✗ Test '{name}' raised exception: {e}")
            results.append((name, False))

    # Visualization
    visualize_small_grid(5)

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
    print("=" * 60)

    return all_passed


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
