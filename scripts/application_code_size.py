#!/usr/bin/env python3

import os
import subprocess
import polars as pl

from pathlib import Path


def ebpf_build(dir, benchmark):
    env = os.environ.copy()
    env["BENCHMARK"] = benchmark

    subprocess.run(["make", "benchmark.bin"], cwd=dir, check=True, env=env)


def ebpf_check_size(dir, _benchmark):
    return os.path.getsize(Path(dir) / "benchmark.bin")


def no_build(_dir, _benchmark): ...


def wamr_build(dir, benchmark):
    env = os.environ.copy()
    env["BENCHMARK"] = benchmark

    subprocess.run(["make", "benchmark.wasm"], cwd=dir, check=True, env=env)


def wamr_check_size(dir, _benchmark):
    return os.path.getsize(Path(dir) / "benchmark.wasm")


def script_check_size(dir, benchmark):
    path = Path(dir)
    path /= "benchmarks"
    path /= f"{benchmark}"

    return os.path.getsize(path)


def js_check_size(dir, benchmark):
    return script_check_size(dir, benchmark + ".js")


def lua_check_size(dir, benchmark):
    return script_check_size(dir, benchmark + ".lua")


def python_check_size(dir, benchmark):
    return script_check_size(dir, benchmark + ".py")


ebpf_commands = [
    {"platform": "femto-container", "build": ebpf_build, "check_size": ebpf_check_size},
    {"platform": "micro-bpf", "build": ebpf_build, "check_size": ebpf_check_size},
]

heap_supported_commands = [
    {"platform": "wamr", "build": wamr_build, "check_size": wamr_check_size},
    {"platform": "jerryscript", "build": no_build, "check_size": js_check_size},
    {"platform": "lua", "build": no_build, "check_size": lua_check_size},
    {"platform": "micropython", "build": no_build, "check_size": python_check_size},
]

heap_less_benchmarks = ["libud", "crc_32", "xgboost"]
heap_benchmarks = ["tarfind", "md5"]


if __name__ == "__main__":
    results = []

    for command in ebpf_commands + heap_supported_commands:
        if command in heap_supported_commands:
            benchmarks = heap_less_benchmarks + heap_benchmarks
        else:
            benchmarks = heap_less_benchmarks

        for benchmark in benchmarks:
            platform = command["platform"]
            build = command["build"]
            check_size = command["check_size"]

            dir = platform

            print(f"Building {benchmark} for {platform}...")
            build(dir, benchmark)

            print(f"Checking size for {benchmark} on {platform}...")
            size = check_size(dir, benchmark)

            results.append(
                {"environment": platform, "benchmark": benchmark, "size_bytes": size}
            )

    write_path = "data/memory/application_code_size.csv"
    print(f"Writing results to {write_path}...")
    pl.DataFrame(results).write_csv(write_path)
