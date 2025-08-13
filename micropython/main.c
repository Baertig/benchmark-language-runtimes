/*
 * SPDX-FileCopyrightText: 2019 Kaspar Schleiser <kaspar@schleiser.de>
 * SPDX-License-Identifier: LGPL-2.1-only
 */

/**
 * @ingroup     examples
 * @{
 *
 * @file
 * @brief       micropython example application
 *
 * @author      Kaspar Schleiser <kaspar@schleiser.de>
 *
 * @}
 */

#include <stdio.h>

#include "thread.h"

#include "micropython.h"
#include "py/stackctrl.h"
#include "lib/utils/pyexec.h"

#include "blob/tarfind.py.h"

static char mp_heap[MP_RIOT_HEAPSIZE];

int main(void)
{

    /* let MicroPython know the top of this thread's stack */
    uint32_t stack_dummy;
    mp_stack_set_top((char*)&stack_dummy);

    /* Make MicroPython's stack limit somewhat smaller than actual stack limit */
    mp_stack_set_limit(THREAD_STACKSIZE_MAIN - MP_STACK_SAFEAREA);
    mp_riot_init(mp_heap, sizeof(mp_heap));

    puts("-- Executing tarfind.py");
    mp_do_str((const char *)tarfind_py, tarfind_py_len);
    puts("-- boot.py exited. Starting REPL..");

    return 0;
}
