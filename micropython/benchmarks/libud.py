SCALE_FACTOR = 1
a = [[0] * 20 for _ in range(20)]
b = [0] * 20
x = [0] * 20

chkerr = 0


def ludcmp(n: int) -> int:
    global a, b, x

    y = [0] * 100

    # --- LU Decomposition ---
    # This part decomposes the matrix 'a' into Lower (L) and Upper (U)
    # triangular matrices, stored in-place in 'a'.

    for i in range(n):
        for j in range(i + 1, n + 1):
            w = a[j][i]
            if i != 0:
                for k in range(i):
                    w -= a[j][k] * a[k][i]

            a[j][i] = w // a[i][i]

        for j in range(i + 1, n + 1):
            w = a[i + 1][j]
            for k in range(i + 1):
                w -= a[i + 1][k] * a[k][j]
            a[i + 1][j] = w

    # --- Forward Substitution (solves L*y = b) ---
    y[0] = b[0]
    for i in range(1, n + 1):
        w = b[i]
        for j in range(i):
            w -= a[i][j] * y[j]
        y[i] = w

    # --- Backward Substitution (solves U*x = y) ---
    x[n] = y[n] // a[n][n]
    for i in range(n - 1, -1, -1):
        w = y[i]
        for j in range(i + 1, n + 1):
            w -= a[i][j] * x[j]
        x[i] = w // a[i][i]

    return 0


def verify_benchmark(res: int) -> bool:
    global x
    x_ref = [0, 0, 1, 1, 1, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

    # In Python, lists can be compared directly with '=='.
    # This checks if every element in 'x' matches the corresponding
    # element in 'x_ref' and that the result from ludcmp was 0.
    return x == x_ref and res == 0


def benchmark() -> bool:
    global a, b, chkerr, SCALE_FACTOR
    sf = SCALE_FACTOR

    for _ in range(sf):
        n = 5

        for i in range(n + 1):
            w = 0
            for j in range(n + 1):
                a[i][j] = (i + 1) + (j + 1)
                # Double the value on the main diagonal
                if i == j:
                    a[i][j] *= 2
                w += a[i][j]
            b[i] = w

        chkerr = ludcmp(n)

    return verify_benchmark(chkerr)
