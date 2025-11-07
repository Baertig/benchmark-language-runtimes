#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include "jerryscript.h"
#include "jerryscript-ext/handler.h"
#include "jerryscript-port-default.h"
#include "ztimer.h"
#include "periph/pm.h"
#include "thread.h"

#ifndef BENCH_ITERATIONS
#define BENCH_ITERATIONS 5
#endif

#define BOOL_TO_STR(x) ((x) ? "true" : "false")

/* Include header generated from the benchmark file */
#include "blob/benchmark.js.h"

#if DUMP_BYTECODE
int print_get_type_freq(void); // defined in vm.c
int print_oc_type_freq(void); // defined in vm.c
#endif

void print_jerry_error(jerry_value_t error_value, const char* error_context)
{
    /* Get error details */
    jerry_value_t error_obj = jerry_get_value_from_error(error_value, false);
    jerry_value_t error_str = jerry_value_to_string(error_obj);
    
    /* Get the error message as a string */
    jerry_size_t error_str_size = jerry_get_string_size(error_str);
    jerry_char_t *error_buffer = malloc(error_str_size + 1);
    if (error_buffer) {
        jerry_string_to_char_buffer(error_str, error_buffer, error_str_size);
        error_buffer[error_str_size] = '\0';
        printf("%s: %s\n", error_context, error_buffer);
        free(error_buffer);
    } else {
        printf("%s: (could not allocate memory for error message)\n", error_context);
    }
    
    /* Check if it's a specific error type */
    jerry_error_t error_type = jerry_get_error_type(error_value);
    switch (error_type) {
        case JERRY_ERROR_COMMON:
            printf("Error type: Common/Generic error\n");
            break;
        case JERRY_ERROR_EVAL:
            printf("Error type: EvalError\n");
            break;
        case JERRY_ERROR_RANGE:
            printf("Error type: RangeError\n");
            break;
        case JERRY_ERROR_REFERENCE:
            printf("Error type: ReferenceError\n");
            break;
        case JERRY_ERROR_SYNTAX:
            printf("Error type: SyntaxError\n");
            break;
        case JERRY_ERROR_TYPE:
            printf("Error type: TypeError\n");
            break;
        case JERRY_ERROR_URI:
            printf("Error type: URIError\n");
            break;
        default:
            printf("Error type: Unknown (%d)\n", error_type);
            break;
    }
    
    jerry_release_value(error_str);
    jerry_release_value(error_obj);
}

int js_run(const jerry_char_t *script, size_t script_size)
{

    jerry_value_t parsed_code, ret_value;
    int res = 0;

    /* Initialize engine, no flags, default configuration */

    uint32_t init_runtime_begin = ztimer_now(ZTIMER_USEC);
    jerry_init_flag_t init_flags = JERRY_INIT_EMPTY;

#ifdef DUMP_BYTECODE
    init_flags |= JERRY_INIT_SHOW_OPCODES;
    jerry_port_default_set_log_level(JERRY_LOG_LEVEL_DEBUG);
#endif

    jerry_init(init_flags);

    /* Register the print function in the global object. */
    jerryx_handler_register_global((const jerry_char_t *) "print",
                                   jerryx_handler_print);

    uint32_t init_runtime_end = ztimer_now(ZTIMER_USEC);
    printf("%d;", (int) (init_runtime_end - init_runtime_begin));


    /* Setup Global scope code */

    uint32_t load_program_begin = ztimer_now(ZTIMER_USEC);
    parsed_code = jerry_parse(NULL, 0, script, script_size, JERRY_PARSE_NO_OPTS);
    uint32_t load_program_end = ztimer_now(ZTIMER_USEC);
    printf("%d;", (int) (load_program_end - load_program_begin));

    if (!jerry_value_is_error(parsed_code)) {
        /* Execute the parsed source code in the Global scope */

        uint32_t execution_time_begin = ztimer_now(ZTIMER_USEC);

        ret_value = jerry_run(parsed_code);

        uint32_t execution_time_end = ztimer_now(ZTIMER_USEC);
        printf("%d;", (int) (execution_time_end - execution_time_begin));

#ifdef MEM_STATS
        printf("\n--- JerryScript Memory Stats ---\n");
        jerry_heap_stats_t stats;
        if (jerry_get_memory_stats(&stats)) {
            printf("peak_allocated_bytes = %zu\n", stats.peak_allocated_bytes);
            printf("currently_allocated_bytes = %zu\n", stats.allocated_bytes);
            printf("heap_size = %zu\n", stats.size);
        }
        else {
            printf("Could not retrieve JerryScript memory stats.\n");
        }

        size_t stack_free = thread_measure_stack_free(thread_get_active());
        size_t stack_total = THREAD_STACKSIZE_MAIN;
        printf("riot_peak_stack_used_bytes = %zu\n", stack_total - stack_free);

        printf("--------------------------------\n");
#endif /* MEM_STATS */

#if DUMP_BYTECODE
        print_get_type_freq();
        print_oc_type_freq();
#endif /* DUMP_BYTECODE */

        if (jerry_value_is_error(ret_value)) {
            printf("js_run(): Script execution error!\n");
            print_jerry_error(ret_value, "Error message");
            res = -1;
        }

        if (!jerry_value_is_boolean(ret_value)) {
            printf("Error: unexpected return value of jerryscript");
        } else {
            bool correct = jerry_get_boolean_value(ret_value);
            printf("%s\n", BOOL_TO_STR(correct));
        }

        jerry_release_value(ret_value);
    } else {
        printf("Parse error occurred!\n");
        print_jerry_error(parsed_code, "Parse error message");
        res = -1;
    }

    jerry_release_value(parsed_code);

    /* Cleanup engine */
    jerry_cleanup();

    return res;
}

int main(void)
{
    vfprintf(stderr, "\n vprintf test \n", NULL);
    ztimer_init();
    printf("=== Benchmark Begins ===\n");
    printf("iteration;init_runtime_us;load_program_us;execution_time_us;correct\n");
    ztimer_sleep(ZTIMER_USEC, 3000000);

    for (int i=0; i < BENCH_ITERATIONS; i++) {
        printf("%d;", i);
        js_run(benchmark_js, benchmark_js_len);
    }

    printf("=== Benchmark End ===\n");

    /* Power off to prevent hanging */
    pm_off();

    return 0;
}
