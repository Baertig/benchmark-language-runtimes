SCALE_FACTOR = 100  # Define SCALE_FACTOR, adjust as needed


def benchmark():
    sum_value = 0
    for i in range(SCALE_FACTOR + 1):
        sum_value += i

    expected_sum = (SCALE_FACTOR * (SCALE_FACTOR + 1)) // 2

    return sum_value == expected_sum
