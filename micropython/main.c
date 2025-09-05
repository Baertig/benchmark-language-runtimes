#include <stdio.h>

#include "thread.h"

#include "micropython.h"
#include "py/stackctrl.h"
#include "py/lexer.h"
#include "py/parse.h"
#include "py/compile.h"
#include "py/nlr.h"
#include "py/obj.h"
#include "py/runtime.h"

#include "lib/utils/pyexec.h"
#include "ztimer.h"
#include "periph/pm.h"

#include "blob/benchmark.py.h"

#ifndef BENCH_ITERATIONS
#define BENCH_ITERATIONS 5
#endif

#define BOOL_TO_STR(x) ((x) ? "True" : "False")

static char mp_heap[MP_RIOT_HEAPSIZE];

// this function was previously defined as mp_do_str
// TODO: insert ztimer calls
void mp_exec(const char *src, size_t len) {

    uint32_t load_program_begin = ztimer_now(ZTIMER_USEC);
    mp_lexer_t *lex = mp_lexer_new_from_str_len(MP_QSTR__lt_stdin_gt_, src, len, 0);
    if (lex == NULL) {
        printf("MemoryError: lexer could not allocate memory\n");
        return;
    }

    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        qstr source_name = lex->source_name;
        mp_parse_tree_t parse_tree = mp_parse(lex, MP_PARSE_FILE_INPUT);
        mp_obj_t module_fun = mp_compile(&parse_tree, source_name, MP_EMIT_OPT_NONE, false);

        uint32_t load_program_end = ztimer_now(ZTIMER_USEC);
        printf("%d;", (int) (load_program_end - load_program_begin));

        uint32_t execution_begin = ztimer_now(ZTIMER_USEC);
        mp_call_function_0(module_fun);
        mp_obj_t benchmark_function = mp_load_global(qstr_from_str("benchmark"));
        mp_obj_t result = mp_call_function_0(benchmark_function);
        uint32_t execution_end = ztimer_now(ZTIMER_USEC);
        printf("%d;", (int) (execution_end - execution_begin));

        bool correct = false;
        if (result == mp_const_true) {
            correct = true;
        } else if (result == mp_const_false) {
            correct = false;
        } else {
            printf("Warning: unexpected return value type from Python script\n");
        }

        printf("%s\n", BOOL_TO_STR(correct));

        nlr_pop();
    } else {
        // uncaught exception
        mp_obj_print_exception(&mp_plat_print, (mp_obj_t)nlr.ret_val);
    }
}

int main(void)
{
    printf("=== Benchmark Begins ===\n");
    printf("iteration;init_runtime_us;load_program_us;execution_time_us;correct\n");

    for (int i=0; i < BENCH_ITERATIONS; i++) {
        printf("%d;", i);
        /* let MicroPython know the top of this thread's stack */
        uint32_t stack_dummy;
        uint32_t init_runtime_begin = ztimer_now(ZTIMER_USEC);
        mp_stack_set_top((char*)&stack_dummy);

        /* Make MicroPython's stack limit somewhat smaller than actual stack limit */
        mp_stack_set_limit(THREAD_STACKSIZE_MAIN - MP_STACK_SAFEAREA);
        mp_riot_init(mp_heap, sizeof(mp_heap));

        uint32_t init_runtime_end = ztimer_now(ZTIMER_USEC);
        printf("%d;", (int) (init_runtime_end - init_runtime_begin));

        mp_exec((const char *)benchmark_py, benchmark_py_len);
    }

    printf("=== Benchmark End ===\n");

    /* Power off to prevent hanging */
    pm_off();
    
    return 0;
}
