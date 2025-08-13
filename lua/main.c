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

#include "blob/tarfind.lua.h"

#define LUA_MEM_SIZE (350 * 1024)

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
    lua_State *L = lua_riot_newstate(lua_mem, sizeof(lua_mem), NULL);

    if (L == NULL) {
        puts("cannot create state: not enough memory");
        return ENOMEM;
    }

    lua_riot_openlibs(L, LUAR_LOAD_BASE);
    lua_riot_openlibs(L, LUAR_LOAD_MATH);
    lua_riot_openlibs(L, LUAR_LOAD_STRING);
    lua_riot_openlibs(L, LUAR_LOAD_TABLE);

    lua_pushcfunction(L, msghandler);
    int errfunc = lua_gettop(L);

    int status = luaL_loadbuffer(L, (const char *)buffer, buffer_len, "lua input script");
    if (status != LUA_OK) {
        const char *msg = lua_tostring(L, -1);
        printf("Lua load %s error (%d): %s\n",
               lua_status_name(status), status, msg ? msg : "(non-string error)");

        lua_pop(L, 1);           // pop error message
        lua_riot_close(L);
        return EINTR;
    } else {
        puts("Loaded lua script successfully!");
    }

    status = lua_pcall(L, 0, 0, errfunc);
    if (status != LUA_OK) {
        const char *msg = lua_tostring(L, -1);
        printf("Lua %s runtime error (%d): %s\n",
               lua_status_name(status), status, msg ? msg : "(non-string error)");
        lua_pop(L, 1);           // pop error + traceback
        lua_pop(L, 1);           // pop msghandler
        lua_riot_close(L);
        return EINTR;
    }

    lua_pop(L, 1);               // pop msghandler
    lua_riot_close(L);
    return 0;
}

int main(void)
{
    puts("Lua RIOT build");
    lua_run_script(tarfind_lua, tarfind_lua_len);
    puts("Lua interpreter exited");

    return 0;
}
