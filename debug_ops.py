"""Debug operation counting in Block-Strassen"""

import numpy as np


class DebugBlockStrassen:
    def __init__(self):
        self.ops = {'multiplications': 0, 'additions': 0}

    def strassen_2x2(self, A, B):
        """Strassen 2x2 with detailed logging"""
        print("  Strassen 2x2:")
        a, b = A[0, 0], A[0, 1]
        c, d = A[1, 0], A[1, 1]
        e, f = B[0, 0], B[0, 1]
        g, h = B[1, 0], B[1, 1]

        ops_before = self.ops['additions']

        # Preprocessing
        m1 = (a + d) * (e + h)
        self.ops['additions'] += 2
        self.ops['multiplications'] += 1

        m2 = (c + d) * e
        self.ops['additions'] += 1
        self.ops['multiplications'] += 1

        m3 = a * (f - h)
        self.ops['additions'] += 1
        self.ops['multiplications'] += 1

        m4 = d * (g - e)
        self.ops['additions'] += 1
        self.ops['multiplications'] += 1

        m5 = (a + b) * h
        self.ops['additions'] += 1
        self.ops['multiplications'] += 1

        m6 = (c - a) * (e + f)
        self.ops['additions'] += 2
        self.ops['multiplications'] += 1

        m7 = (b - d) * (g + h)
        self.ops['additions'] += 2
        self.ops['multiplications'] += 1

        pre_adds = self.ops['additions'] - ops_before
        print(f"    Preprocessing: {pre_adds} adds, 7 mults")

        ops_before = self.ops['additions']

        # Postprocessing
        p11 = m1 + m4 - m5 + m7
        p12 = m3 + m5
        p21 = m2 + m4
        p22 = m1 - m2 + m3 + m6
        self.ops['additions'] += 8

        post_adds = self.ops['additions'] - ops_before
        print(f"    Postprocessing: {post_adds} adds")
        print(f"    Strassen subtotal: 7 mults, {pre_adds + post_adds} adds")

        return np.array([[p11, p12], [p21, p22]])

    def multiply(self, A, B):
        self.ops = {'multiplications': 0, 'additions': 0}

        print("\nBlock decomposition:")
        A11 = A[:2, :2]
        u = A[:2, 2:3]
        v = A[2:3, :2]
        alpha = A[2, 2]

        B11 = B[:2, :2]
        x = B[:2, 2:3]
        y = B[2:3, :2]
        beta = B[2, 2]

        # Strassen 2x2
        P = self.strassen_2x2(A11, B11)

        print("\nBorder operations:")
        ops_before_mults = self.ops['multiplications']
        ops_before_adds = self.ops['additions']

        # Q = u @ y
        Q = u @ y
        self.ops['multiplications'] += 4
        print(f"  Q = u @ y: 4 mults, 0 adds")

        # r = A11 @ x
        r = A11 @ x
        self.ops['multiplications'] += 4
        self.ops['additions'] += 2
        print(f"  r = A11 @ x: 4 mults, 2 adds")

        # s = u * beta
        s = u * beta
        self.ops['multiplications'] += 2
        print(f"  s = u * beta: 2 mults, 0 adds")

        # t = v @ B11
        t = v @ B11
        self.ops['multiplications'] += 4
        self.ops['additions'] += 2
        print(f"  t = v @ B11: 4 mults, 2 adds")

        # w = alpha * y
        w = alpha * y
        self.ops['multiplications'] += 2
        print(f"  w = alpha * y: 2 mults, 0 adds")

        # z = v @ x
        z = (v @ x)[0, 0]
        self.ops['multiplications'] += 2
        self.ops['additions'] += 1
        print(f"  z = v @ x: 2 mults, 1 add")

        # gamma = alpha * beta
        gamma = alpha * beta
        self.ops['multiplications'] += 1
        print(f"  gamma = alpha * beta: 1 mult, 0 adds")

        border_mults = self.ops['multiplications'] - ops_before_mults
        border_adds = self.ops['additions'] - ops_before_adds
        print(f"  Border subtotal: {border_mults} mults, {border_adds} adds")

        print("\nAssembly:")
        ops_before = self.ops['additions']

        C11 = P + Q
        C12 = r + s
        C21 = t + w
        C22 = z + gamma
        self.ops['additions'] += 9

        assembly_adds = self.ops['additions'] - ops_before
        print(f"  Assembly: {assembly_adds} adds")

        C = np.zeros((3, 3))
        C[:2, :2] = C11
        C[:2, 2:3] = C12
        C[2:3, :2] = C21
        C[2, 2] = C22

        print(f"\nTotal: {self.ops['multiplications']} mults, {self.ops['additions']} adds")

        return C


# Test
np.random.seed(42)
A = np.random.randn(3, 3)
B = np.random.randn(3, 3)

algo = DebugBlockStrassen()
C = algo.multiply(A, B)

print("\n" + "=" * 60)
print("Expected: 26 mults, 29 adds (7+15 + 19+5 + 0+9)")
print(f"Got:      {algo.ops['multiplications']} mults, {algo.ops['additions']} adds")
