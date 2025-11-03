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
#include <stdbool.h>

#ifdef MEM_STATS
#include "malloc_monitor.h"
#endif

#ifndef BENCH_ITERATIONS
#define BENCH_ITERATIONS 5
#endif

#define BOOL_TO_STR(x) ((x) ? "true" : "false")

int main (void)
{
  bool correct;

#ifdef MEM_STATS
  size_t initial_watermark = malloc_monitor_get_usage_high_watermark();
#endif

  ztimer_sleep(ZTIMER_USEC, 3000000); // sleep for 3 seconds, so that a uart connection can be established

  printf("=== Benchmark Begins ===\n");
  printf("iteration;init_runtime_us;load_program_us;execution_time_us;correct\n");
  for (int i=0; i < BENCH_ITERATIONS; i++) {

    uint32_t execution_begin = ztimer_now(ZTIMER_USEC);

    correct = benchmark();

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

#ifdef MEM_STATS
    size_t final_watermark = malloc_monitor_get_usage_high_watermark();
    printf("mem_usage_high_watermark_bytes:%zu\n", final_watermark - initial_watermark);
#endif

  return (!correct);
}
