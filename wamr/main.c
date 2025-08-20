/*
 * SPDX-FileCopyrightText: 2020 TU Bergakademie Freiberg Karl Fessel
 * SPDX-License-Identifier: LGPL-2.1-only
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include "ztimer.h"
/*include the benchmark main*/
#include "blob/main.wasm.h"

bool iwasm_runtime_init(void);
void iwasm_runtime_destroy(void);

/* wamr_run is a very direct interpretation of "i like to have a wamr_run" */
int wamr_run(void *bytecode, size_t bytecode_len, int argc, char **argv);

/* wamr_run_cp creates a copy bytecode and argv
 * if argc is 0 it is set to 1 and argv[0] is set to ""
 * to create some space for a return value */
int wamr_run_cp(const void *bytecode, size_t bytecode_len, int argc, const char **argv);


#ifndef BENCH_ITERATIONS
#define BENCH_ITERATIONS 5
#endif

#define BOOL_TO_STR(x) ((x) ? "True" : "False")

int main(void)
{
    printf("=== Benchmark Begins ===\n");
    printf("iteration;init_runtime_us;load_program_us;execution_time_us;correct\n");
    for (int i = 0; i < BENCH_ITERATIONS; i++) {
        printf("%d;", i);
        uint32_t init_runtime_begin = ztimer_now(ZTIMER_USEC);
        bool init_successful = iwasm_runtime_init();
        uint32_t init_runtime_end = ztimer_now(ZTIMER_USEC);

        printf("%d;", init_runtime_end - init_runtime_begin);
        if(!init_successful) {
            printf("Error when initializing iwasm runtime");
        }

        int incorrect = wamr_run_cp(main_wasm, main_wasm_len, 0, NULL);
        printf("%s\n", BOOL_TO_STR(!incorrect));

        iwasm_runtime_destroy();
    }

    printf("=== Benchmark End ===\n");
}

