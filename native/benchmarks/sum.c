#ifndef SCALE_FACTOR
#define SCALE_FACTOR 1
#endif

int __attribute__ ((noinline))
benchmark()
{
    int volatile sum = 0;
    for (int i = 0; i <= SCALE_FACTOR; i++) {
        sum += i;
    }

    int expected_sum = (SCALE_FACTOR * (SCALE_FACTOR + 1)) / 2;
    return sum == expected_sum;
}