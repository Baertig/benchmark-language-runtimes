/* Common main.c for the benchmarks

   Copyright (C) 2014 Embecosm Limited and University of Bristol
   Copyright (C) 2018-2019 Embecosm Limited

   Contributor: James Pallister <james.pallister@bristol.ac.uk>
   Contributor: Jeremy Bennett <jeremy.bennett@embecosm.com>

   This file is part of Embench and was formerly part of the Bristol/Embecosm
   Embedded Benchmark Suite.

   SPDX-License-Identifier: GPL-3.0-or-later */

#include "support.h"
#include <stdio.h>
#include <stdint.h>
#include "ztimer.h"

#ifndef BENCH_ITERATIONS
#define BENCH_ITERATIONS 5
#endif

#define BOOL_TO_STR(x) ((x) ? "True" : "False")

int main (void)
{
  volatile int result;
  int correct;

  printf("=== Benchmark Begins ===\n");
  printf("iteration;init_runtime_us;load_program_us;execution_time_us;correct\n");
  // start_trigger ();
  for (int i=0; i < BENCH_ITERATIONS; i++) {

    uint32_t execution_begin = ztimer_now(ZTIMER_USEC);

    result = benchmark ();
    correct = verify_benchmark (result);

    uint32_t execution_end = ztimer_now(ZTIMER_USEC);

    int init_runtime_us = 0;
    int load_program_us = 0;
    int execution_time_us = execution_end - execution_begin;

    printf("%d;%d;%d;%d;%s\n",
       i,
       init_runtime_us,
       load_program_us,
       execution_time_us,
       BOOL_TO_STR(correct)
    );
  }

  printf("=== Benchmark End ===\n");

  return (!correct);
}				
