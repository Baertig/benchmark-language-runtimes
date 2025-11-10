/*
 * SPDX-FileCopyrightText: 2018 FU Berlin
 * SPDX-License-Identifier: LGPL-2.1-only
 */

/**
 * @ingroup     examples
 * @{
 *
 * @file
 * @brief       Basic lua example application
 *
 * @author      Daniel Petry <daniel.petry@fu-berlin.de>
 *
 * @}
 */

#include <stdio.h>
#include <errno.h>

#include "lauxlib.h"
#include "lualib.h"
#include "lua_run.h"
#include "ztimer.h"
#include "periph/pm.h"

/* Include header generated from the benchmark file */
#include "blob/benchmark.lua.h"

#ifndef BENCH_ITERATIONS
#define BENCH_ITERATIONS 5
#endif

#define BOOL_TO_STR(x) ((x) ? "true" : "false")

#ifndef LUA_MEM_SIZE
#define LUA_MEM_SIZE (350 * 1024)
#endif

extern void dump_opcodes(void);

static char lua_mem[LUA_MEM_SIZE] __attribute__ ((aligned(__BIGGEST_ALIGNMENT__)));

static int msghandler(lua_State *L) {
    const char *msg = lua_tostring(L, 1);
    if (msg == NULL) {
        if (luaL_callmeta(L, 1, "__tostring") && lua_type(L, -1) == LUA_TSTRING) {
            return 1;
        }
        msg = lua_pushfstring(L, "(error object is a %s value)", luaL_typename(L, 1));
    }
    luaL_traceback(L, L, msg, 1); // append traceback
    return 1; // return the traceback string
}

static const char* lua_status_name(int code) {
    switch (code) {
        case LUA_OK:        return "OK";
        case LUA_ERRRUN:    return "runtime";
        case LUA_ERRMEM:    return "memory";
        case LUA_ERRERR:    return "message-handler";
        case LUA_ERRSYNTAX: return "syntax";
        default:            return "unknown";
    }
}

int lua_run_script(const uint8_t *buffer, size_t buffer_len)
{

    uint32_t init_runtime_begin = ztimer_now(ZTIMER_USEC);
    lua_State *L = lua_riot_newstate(lua_mem, sizeof(lua_mem), NULL);

    if (L == NULL) {
        puts("cannot create state: not enough memory");
        return ENOMEM;
    }

    #ifdef GC_AGGRESSIVE
    // ref: https://www.lua.org/manual/5.3/manual.html#2.5
    lua_gc(L, LUA_GCSETPAUSE, 0); // -> "values smaller then 100 mean the gc will not wait before starting a new cycle"
    #endif

    lua_riot_openlibs(L, LUAR_LOAD_BASE);
    lua_riot_openlibs(L, LUAR_LOAD_MATH);
    lua_riot_openlibs(L, LUAR_LOAD_STRING);
    lua_riot_openlibs(L, LUAR_LOAD_TABLE);

    uint32_t init_runtime_end = ztimer_now(ZTIMER_USEC);
    printf("%d;", (int) init_runtime_end - (int) init_runtime_begin);

    lua_pushcfunction(L, msghandler);
    int errfunc = lua_gettop(L);

    uint32_t load_program_begin = ztimer_now(ZTIMER_USEC);
    int status = luaL_loadbuffer(L, (const char *)buffer, buffer_len, "lua input script");
    uint32_t load_program_end = ztimer_now(ZTIMER_USEC);
    printf("%d;", (int) load_program_end - (int) load_program_begin);

    if (status != LUA_OK) {
        const char *msg = lua_tostring(L, -1);
        printf("Lua load %s error (%d): %s\n",
               lua_status_name(status), status, msg ? msg : "(non-string error)");

        #ifdef MEM_STATS
            /* get memory usage */
            size_t mem_used = get_peak_lua_heap();
            reset_peak_lua_heap_counter();

            printf("\npeak_allocated_bytes = %zu\n", mem_used);
        #endif

        lua_pop(L, 1);           // pop error message
        lua_riot_close(L);
        return EINTR;
    } 


    uint32_t execution_time_begin = ztimer_now(ZTIMER_USEC);
    // lua_pcall(L, nargs, nresults, errfunc)
    // L: Lua state
    // nargs: number of arguments passed to the function (0 - no arguments)
    // nresults: number of return values expected (1 - expect 1 return value)
    // errfunc: stack index of error handler function (msghandler)
    status = lua_pcall(L, 0, 1, errfunc);
    uint32_t execution_time_end = ztimer_now(ZTIMER_USEC);
    printf("%d;", (int) execution_time_end - (int) execution_time_begin);

    if (status != LUA_OK) {
        const char *msg = lua_tostring(L, -1);
        printf("Lua %s runtime error (%d): %s\n",
               lua_status_name(status), status, msg ? msg : "(non-string error)");

        #ifdef MEM_STATS
            /* get memory usage */
            size_t mem_used = get_peak_lua_heap();
            reset_peak_lua_heap_counter();

            printf("\npeak_allocated_bytes = %zu\n", mem_used);
        #endif

        lua_pop(L, 1);           // pop error + traceback
        lua_pop(L, 1);           // pop msghandler
        lua_riot_close(L);
        return EINTR;
    }

#ifdef MEM_STATS
    /* get memory usage */
    size_t mem_used = get_peak_lua_heap();
    reset_peak_lua_heap_counter();

    printf("\npeak_allocated_bytes = %zu\n", mem_used);
#endif

#ifdef DUMP_OPCODES
    dump_opcodes();
#endif

    // Get the return value from the script
    bool correct = false;
    if (lua_isboolean(L, -1)) {
        correct = lua_toboolean(L, -1);
    } else {
        printf("Error: unexpected return value type from Lua script\n");
    }
    
    printf("%s\n", BOOL_TO_STR(correct));

    lua_pop(L, 1);               // pop msghandler
    lua_riot_close(L);
    return 0;
}

int main(void)
{

    ztimer_init();

    printf("=== Benchmark Begins ===\n");
    printf("iteration;init_runtime_us;load_program_us;execution_time_us;correct\n");
    ztimer_sleep(ZTIMER_USEC, 3000000);

    for (int i=0; i < BENCH_ITERATIONS; i++) {
        printf("%d;", i);
        lua_run_script(benchmark_lua, benchmark_lua_len);
    }
    printf("=== Benchmark End ===\n");

    /* Power off to prevent hanging */
    pm_off();

    return 0;
}
