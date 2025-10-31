/* BEEBS ud benchmark

   This version, copyright (C) 2014-2019 Embecosm Limited and University of
   Bristol

   Contributor James Pallister <james.pallister@bristol.ac.uk>
   Contributor Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later */

/* MDH WCET BENCHMARK SUITE. */

#include <stddef.h>
// #include <femtocontainer/helpers.h>
#include <helpers.h>

/* This scale factor will be changed to equalise the runtime of the
   benchmarks. */
#ifndef SCALE_FACTOR
#define SCALE_FACTOR 1
#endif


typedef struct {
    long a[20][20];  // Changed to signed long
    long b[20];      // Changed to signed long
    long x[20];      // Changed to signed long
    long y[100];     // Changed to signed long
    long x_ref[20];  // Changed to signed long (assuming reference can be negative)
    char msg[100];
} context;



/* Write to CHKERR from BENCHMARK to ensure calls are not optimised away.  */
// volatile int chkerr;

static inline int memcmp(const void *s1, const void *s2, size_t n) {
    const unsigned char *p1 = (const unsigned char *)s1;
    const unsigned char *p2 = (const unsigned char *)s2;
    for (size_t i = 0; i < n; ++i) {
        if (p1[i] != p2[i]) {
            return (p1[i] < p2[i]) ? -1 : 1;
        }
    }
    return 0;
}


static inline int verify_benchmark (int res, context *ctx)
{
  unsigned long *x = ctx->x;
  unsigned long *x_ref = ctx->x_ref;
  return (0 == memcmp (x, x_ref, 20 * sizeof (x[0]))) && (0 == res);
}


// Helper function for signed division using unsigned ops
// Assumes eBPF supports signed comparisons and unsigned division (UDIV)
static inline long sdiv(long dividend, long divisor, context *ctx) {

    if (divisor == 0) {
        // Handle division by zero (e.g., return 0 or error; adjust as needed)
        return 0;
    }
    int sign = ((dividend < 0) ^ (divisor < 0)) ? -1 : 1;
    unsigned long abs_dividend = (dividend < 0) ? -dividend : dividend;
    unsigned long abs_divisor = (divisor < 0) ? -divisor : divisor;

    unsigned long abs_result = abs_dividend / abs_divisor;  // Unsigned division
    long result = (long)abs_result;

    if (sign < 0) {
        result = -result;  // Use negation instead of multiplication
    }
    return result;
}

int benchmark (context *ctx) {
    long (*a)[20] = ctx->a;  
    long *b = ctx->b;        
    long *x = ctx->x;        
    int chkerr = 0;

    unsigned int sf = SCALE_FACTOR;

    for (unsigned int sf_cnt = 0; sf_cnt < sf; sf_cnt++) {
        int i, j, nmax = 20, n = 5;
        long w;  

        /* Init loop */
        for(i = 0; i <= n; i++) {
            w = 0;              /* data to fill in cells */
            for(j = 0; j <= n; j++) {
                a[i][j] = (i + 1) + (j + 1);  // Now signed
                if(i == j) a[i][j] *= 2; /* only once per loop pass */
                w += a[i][j];
            }

            b[i] = w;
        }


        // chkerr = ludcmp(n, ctx);

        //ludcmp inline
        int k;
        long *y = ctx->y;

        for(i = 0; i < n; i++) {
            for(j = i+1; j <= n; j++) { /* triangular loop vs. i */
                w = a[j][i];
                if(i != 0)            /* sub-loop is conditional, done
                                    all iterations except first of the
                                    OUTER loop */
                for(k = 0; k < i; k++) 
                    w -= a[j][k] * a[k][i];

                a[j][i] = sdiv(w, a[i][i], ctx);  
            }


            for(j = i+1; j <= n; j++) { /* triangular loop vs. i */
                w = a[i+1][j];
                for(k = 0; k <= i; k++) /* triangular loop vs. i */
                    w -= a[i+1][k] * a[k][j];

                a[i+1][j] = w;
            }
        }

        y[0] = b[0];
        for(i = 1; i <= n; i++) { /* iterates n times */
            w = b[i];
            for(j = 0; j < i; j++)    /* triangular sub loop */
                w -= a[i][j] * y[j];

            y[i] = w;
        }

        x[n] = sdiv(y[n], a[n][n], ctx);  
        for(i = n-1; i >= 0; i--) { /* iterates n times */
            w = y[i];
            for(j = i+1; j <= n; j++) /* triangular sub loop */
                w -= a[i][j] * x[j];

            x[i] = sdiv(w, a[i][i], ctx);  
        }
        // end ludcmp inline
    }

  return verify_benchmark(chkerr, ctx);
}


