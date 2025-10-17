/* BEEBS ud benchmark

   This version, copyright (C) 2014-2019 Embecosm Limited and University of
   Bristol

   Contributor James Pallister <james.pallister@bristol.ac.uk>
   Contributor Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later */

/* MDH WCET BENCHMARK SUITE. */



#include <string.h>

/* This scale factor will be changed to equalise the runtime of the
   benchmarks. */
#ifndef SCALE_FACTOR
#define SCALE_FACTOR 1
#endif


long int a[20][20], b[20], x[20];

int ludcmp(int n);


/*  static double fabs(double n) */
/*  { */
/*    double f; */

/*    if (n >= 0) f = n; */
/*    else f = -n; */
/*    return f; */
/*  } */

/* Write to CHKERR from BENCHMARK to ensure calls are not optimised away.  */
volatile int chkerr;


static int verify_benchmark (int res)
{
  long int x_ref[20] =
    { 0L, 0L, 1L, 1L, 1L, 2L, 0L, 0L, 0L, 0L,
      0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L, 0L
    };

  return (0 == memcmp (x, x_ref, 20 * sizeof (x[0]))) && (0 == res);
}


int benchmark (void) {
    unsigned int sf = SCALE_FACTOR;

    for (unsigned int sf_cnt = 0; sf_cnt < sf; sf_cnt++) {
        int i, j, nmax = 20, n = 5;
        long int w;

        /* Init loop */
        for(i = 0; i <= n; i++) {
            w = 0;              /* data to fill in cells */
            for(j = 0; j <= n; j++) {
                a[i][j] = (i + 1) + (j + 1);
                if(i == j) a[i][j] *= 2; /* only once per loop pass */
                w += a[i][j];
            }

            b[i] = w;
        }

        chkerr = ludcmp(n);
    }

  return verify_benchmark(chkerr);
}


int ludcmp(int n)
{
    int i, j, k;
    long w, y[100];

    for(i = 0; i < n; i++) {
        for(j = i+1; j <= n; j++) { /* triangular loop vs. i */
            w = a[j][i];
            if(i != 0)            /* sub-loop is conditional, done
                                   all iterations except first of the
                                   OUTER loop */
            for(k = 0; k < i; k++) 
                w -= a[j][k] * a[k][i];
            
            a[j][i] = w / a[i][i];
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

    x[n] = y[n] / a[n][n];
    for(i = n-1; i >= 0; i--) { /* iterates n times */
        w = y[i];
        for(j = i+1; j <= n; j++) /* triangular sub loop */
            w -= a[i][j] * x[j];

        x[i] = w / a[i][i] ;
    }

    return(0);
}