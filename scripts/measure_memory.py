#!/usr/bin/env python3

import os
import json
import yaml
import csv
import argparse
import subprocess
import sys
from enum import Enum

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

import altair as alt
import polars as pl


class SymbolType(Enum):
    """Symbol section types as reported by cosy.

    Known codes:
    - 't' -> .text
    - 'd' -> .data
    - 'b' -> .bss
    - 'r' -> .rodata
    Any unknown code maps to UNKNOWN.
    """

    TEXT = "t"
    DATA = "d"
    BSS = "b"
    RODATA = "r"
    UNKNOWN = "?"

    @classmethod
    def from_code(cls, code: str) -> "SymbolType":
        if not code:
            return cls.UNKNOWN
        c = code.lower()
        if c == "t":
            return cls.TEXT
        if c == "d":
            return cls.DATA
        if c == "b":
            return cls.BSS
        if c == "r":
            return cls.RODATA
        return cls.UNKNOWN

    @property
    def section(self) -> str:
        return {
            SymbolType.TEXT: ".text",
            SymbolType.DATA: ".data",
            SymbolType.BSS: ".bss",
            SymbolType.RODATA: ".rodata",
            SymbolType.UNKNOWN: "unknown"
        }.get(self)


def load_config(config_file):
    try:
        with open(config_file) as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"Error loading {config_file}: {e}")


def load_mappings(mappings_file):
    """Load mappings keyed by board name with a 'default' fallback.

        Expected YAML structure:
            mappings:
                default:
                    - prefix: [core]
                        category: Core
                adafruit-feather-nrf52840-sense:
                    - prefix: [pkg, lua]
                        category: App

    Returns a dict: { board_name: { (prefix_tuple) : category, ... }, 'default': {...} }
    """
    if not mappings_file:
        return {}
    try:
        with open(mappings_file) as f:
            data = yaml.safe_load(f) or {}

        mappings_node = data.get('mappings')
        if not isinstance(mappings_node, dict):
            raise RuntimeError(
                "'mappings' must be a mapping keyed by board names (use 'default' for fallback)")

        board_mappings: dict[str, dict[tuple, str]] = {}
        for env_name, entries in mappings_node.items():
            if entries is None:
                board_mappings[str(env_name)] = {}
                continue

            if not isinstance(entries, list):
                raise RuntimeError(
                    f"mappings['{env_name}'] must be a list of {{prefix, category}} objects")

            for m in entries:
                if not isinstance(m, dict):
                    continue

                prefix = tuple(m.get('prefix', []) or [])
                category = m.get('category')

                if not prefix or not category:
                    continue

                board_mappings.setdefault(str(env_name), {})[prefix] = category

        return board_mappings
    except Exception as e:
        raise RuntimeError(f"Error loading mappings file: {e}")


def process_symbols(symbols, mappings, board_name):
    """Aggregate sizes per (category, type) with board-specific mappings.

    - mappings: dict returned by load_mappings() keyed by board names and 'default'.
    - board_name: current board name used to select mappings.
    Returns a dict keyed by (category, SymbolType) -> total size.
    """
    board_map = mappings.get(board_name, {}) if isinstance(
        mappings, dict) else {}
    default_map = mappings.get(
        'default', {}) if isinstance(mappings, dict) else {}

    agg = {}
    for sym in symbols:
        path = sym.get('path', [])
        if not path:
            continue

        sym_name = sym.get('sym')
        if sym_name != None and sym_name != "":
            path.append(sym_name)

        size = sym.get('size', 0)
        if not size:
            continue
        stype = SymbolType.from_code(sym.get('type'))

        # Check mappings: prefer board-specific, then default
        matched = False
        for mapping_dict in (board_map, default_map):
            for prefix, cat in mapping_dict.items():
                if path[:len(prefix)] == list(prefix):
                    cat_name = cat
                    matched = True
                    break
            if matched:
                break

        if not matched:
            print(f"path: {"/".join(path)} not matched")
            cat_name = path[0] if path else 'unknown'

        key = (cat_name, stype)
        agg[key] = agg.get(key, 0) + size
    return agg


def run_make_cosy(console, env_dir, board_name, filename):
    # Set environment variables locally for the subprocess
    env = os.environ.copy()
    env['BOARD'] = board_name
    env['BENCHMARK'] = filename

    # 1) Build everything first
    build_output = []
    build_panel = Panel(Text("\n"), title="Make all Output",
                        border_style="blue")

    with Live(build_panel, console=console, refresh_per_second=4) as live:
        build_proc = subprocess.Popen(
            ['make', 'all'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=env_dir, env=env)

        while True:
            output = build_proc.stdout.readline()
            if output == '' and build_proc.poll() is not None:
                break

            if output:
                build_output.append(output.rstrip('\n\r'))
                recent_lines = build_output[-10:]
                display_text = "\n".join(recent_lines)

                live.update(
                    Panel(Text(display_text), title="Make all Output", border_style="blue"))

        rc = build_proc.poll()
        if rc != 0:
            raise subprocess.CalledProcessError(rc, 'make all')

    # 2) Generate cosy output
    all_output = []
    panel = Panel(Text("\n"), title="Make cosy-output Output",
                  border_style="blue")

    with Live(panel, console=console, refresh_per_second=4) as live:
        process = subprocess.Popen(
            ['make', 'cosy-output'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, cwd=env_dir, env=env)

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break

            if output:
                all_output.append(output.rstrip('\n\r'))
                recent_lines = all_output[-15:]
                display_text = "\n".join(recent_lines)

                live.update(
                    Panel(Text(display_text), title="Make cosy-output Output", border_style="blue"))

        rc = process.poll()
        if rc != 0:
            raise subprocess.CalledProcessError(rc, 'make cosy-output')

    return 'symbols.json'


def process_combination(console, bench_name, filename, board_name, env_name, mappings):
    console.print(
        f"\nProcessing {bench_name} on {board_name} with {env_name}...")

    env_dir = env_name
    if not os.path.isdir(env_dir):
        console.print(f"[red]Directory {env_dir} not found, skipping[/red]")
        return []

    try:
        symbols_file = run_make_cosy(console, env_dir, board_name, filename)
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Error running make cosy-output: {e}[/red]")
        return []

    symbols_path = os.path.join(env_dir, symbols_file)
    if not os.path.exists(symbols_path):
        console.print(f"[red]symbols.json not found, skipping[/red]")
        return []

    try:
        with open(symbols_path) as f:
            data = json.load(f)
    except Exception as e:
        console.print(f"[red]Error reading symbols.json: {e}[/red]")
        return []

    cat_type_sizes = process_symbols(data['symbols'], mappings, board_name)

    results = []
    for (cat, stype), size in cat_type_sizes.items():
        results.append({
            'benchmark': bench_name,
            'board': board_name,
            'environment': env_name,
            'category': cat,
            'type': stype.section,
            'size': size
        })

    # Delete symbols.json
    try:
        os.remove(symbols_path)
    except Exception as e:
        console.print(
            f"[yellow]Warning: Error deleting symbols.json: {e}[/yellow]")

    return results


def write_csv(results, out_path):
    try:
        os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
        with open(out_path, 'w', newline='') as f:
            writer = csv.DictWriter(
                f, fieldnames=['benchmark', 'board', 'environment', 'category', 'type', 'size'])
            writer.writeheader()
            writer.writerows(results)
        print(f"Results written to {out_path}")
    except Exception as e:
        raise RuntimeError(f"Error writing CSV: {e}")


def generate_figures(results, figures_dir, console, include_types=None, label_suffix=None):
    """Generate a faceted stacked bar chart.

    - Rows = boards, Columns = benchmarks. Within each facet cell we plot one bar per environment
    (x-axis), stacked by category (color) representing total size contributed by that category.
    - include_types: Optional set/list of section strings (e.g., ['.bss', '.data']) to include.
    - label_suffix: Optional short label appended to filename and chart title, e.g., 'RAM' or 'ROM'.
    """
    if not figures_dir:
        return
    if not results:
        console.print(
            "[yellow]No results to plot; skipping figure generation[/yellow]")
        return
    os.makedirs(figures_dir, exist_ok=True)

    # Build DataFrame for all results
    try:
        df = pl.DataFrame(results)
    except Exception as e:
        console.print(
            f"[red]Failed to build dataframe for plotting: {e}[/red]")
        return

    # Filter by types if provided
    if include_types:
        try:
            df = df.filter(pl.col("type").is_in(list(include_types)))
        except Exception as e:
            console.print(f"[red]Failed to filter by types: {e}[/red]")
            return
        if df.height == 0:
            console.print(
                "[yellow]No data after type filter; skipping figure generation[/yellow]")
            return

    # Stacked bar: one bar per environment inside each (board, benchmark) facet cell
    title = "Memory distribution by Board / Benchmark / Environment"
    if label_suffix:
        title += f" ({label_suffix})"

    chart = (
        alt.Chart(
            df)
        .mark_bar()
        .encode(
            x=alt.X('environment:N', title='Environment'),
            y=alt.Y('size:Q', stack='zero', title='Size (bytes)'),
            color=alt.Color('category:N', title='Category'),
            tooltip=[
                alt.Tooltip('type:N', title='Section'),
                alt.Tooltip('category:N'),
                alt.Tooltip('size:Q', title='Size (bytes)')
            ]
        )
        .facet(
            row=alt.Row('board:N', title='Board'),
            column=alt.Column('benchmark:N', title=title)
        )
        .resolve_scale(y='independent')
    )

    suffix = f"_{label_suffix.lower()}" if label_suffix else ""
    out_file = os.path.join(figures_dir, f"memory_distribution{suffix}.html")
    try:
        chart.save(out_file)
        console.print(
            f"[green]Saved faceted stacked bar chart -> {out_file}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to save stacked bar chart: {e}[/red]")


def main():
    console = Console()

    parser = argparse.ArgumentParser(
        description='Measure static memory sizes using cosy tool')
    parser.add_argument('--config', default='benchmark-config.yml',
                        help='Path to benchmark config YAML file')
    parser.add_argument('--mappings', help='YAML file with category mappings')
    parser.add_argument('--csv-out', default='./memory-sizes.csv',
                        help='Path to write the memory sizes CSV (default: ./memory-sizes.csv)')
    parser.add_argument('--figures', default=None,
                        help='Directory to write output figures (one HTML file per benchmark)')
    args = parser.parse_args()

    try:
        mappings = load_mappings(args.mappings)
        config = load_config(args.config)
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)

    results = []

    for bench in config['benchmarks']:
        bench_name = bench['name']
        filename = bench.get('filename', bench_name)

        for board in bench['boards']:
            board_name = board['board_name']

            for env in board['supported_environments']:
                env_name = env['name']

                combo_results = process_combination(
                    console, bench_name, filename, board_name, env_name, mappings)
                results.extend(combo_results)

    try:
        write_csv(results, args.csv_out)
        # Generate figures if requested: RAM (.bss + .data) and ROM (.text + .data)
        if args.figures:
            generate_figures(
                results, args.figures, console,
                include_types={'.bss', '.data'}, label_suffix='RAM')

            generate_figures(
                results, args.figures, console,
                include_types={'.text', '.data'}, label_suffix='ROM')
        console.print("[bold green]All processing complete![/bold green]")
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
