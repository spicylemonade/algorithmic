"""Debug the Strassen-Only algorithm to see why it's failing correctness."""

import numpy as np

np.random.seed(42)
A = np.random.randn(3, 3)
B = np.random.randn(3, 3)
C_ref = A @ B

print("A =")
print(A)
print("\nB =")
print(B)
print("\nExpected C = A @ B:")
print(C_ref)

# Manual Strassen-Only implementation
C = np.zeros((3, 3))

# Strassen 2x2 on top-left
a, b = A[0, 0], A[0, 1]
c, d = A[1, 0], A[1, 1]
e, f = B[0, 0], B[0, 1]
g, h = B[1, 0], B[1, 1]

m1 = (a + d) * (e + h)
m2 = (c + d) * e
m3 = a * (f - h)
m4 = d * (g - e)
m5 = (a + b) * h
m6 = (c - a) * (e + f)
m7 = (b - d) * (g + h)

C[0, 0] = m1 + m4 - m5 + m7
C[0, 1] = m3 + m5
C[1, 0] = m2 + m4
C[1, 1] = m1 - m2 + m3 + m6

print("\nAfter Strassen 2x2:")
print(C)
print("Top-left 2x2 correct?", np.allclose(C[:2, :2], C_ref[:2, :2]))

# Standard for remaining
# Row 0, col 2
C[0, 2] = A[0, 0] * B[0, 2] + A[0, 1] * B[1, 2] + A[0, 2] * B[2, 2]

# Row 1, col 2
C[1, 2] = A[1, 0] * B[0, 2] + A[1, 1] * B[1, 2] + A[1, 2] * B[2, 2]

# Row 2, all cols
C[2, 0] = A[2, 0] * B[0, 0] + A[2, 1] * B[1, 0] + A[2, 2] * B[2, 0]
C[2, 1] = A[2, 0] * B[0, 1] + A[2, 1] * B[1, 1] + A[2, 2] * B[2, 1]
C[2, 2] = A[2, 0] * B[0, 2] + A[2, 1] * B[1, 2] + A[2, 2] * B[2, 2]

print("\nFinal C:")
print(C)
print("\nCorrect?", np.allclose(C, C_ref))
print("\nMax error:", np.max(np.abs(C - C_ref)))

# Count operations
print("\n" + "=" * 60)
print("OPERATION COUNT")
print("=" * 60)
print("Strassen 2x2: 7 mults + 18 adds = 25 ops")
print("Remaining elements:")
print("  - Row 0, col 2: 3 mults + 2 adds")
print("  - Row 1, col 2: 3 mults + 2 adds")
print("  - Row 2, col 0: 3 mults + 2 adds")
print("  - Row 2, col 1: 3 mults + 2 adds")
print("  - Row 2, col 2: 3 mults + 2 adds")
print("  Total remaining: 15 mults + 10 adds = 25 ops")
print("\nGRAND TOTAL: 22 mults + 28 adds = 50 ops")
print("Meets <81 target: YES")
print("Meets ≤22 mult target: YES!")
