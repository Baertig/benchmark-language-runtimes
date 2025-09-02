#!/usr/bin/env python3

import os
import json
import yaml
import csv
import argparse
import subprocess
import sys

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

import altair as alt
import polars as pl


def load_config(config_file):
    try:
        with open(config_file) as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"Error loading {config_file}: {e}")


def load_mappings(mappings_file):
    if not mappings_file:
        return {}
    try:
        with open(mappings_file) as f:
            data = yaml.safe_load(f)
            mappings = {}
            for m in data['mappings']:
                prefix = tuple(m['prefix'])
                mappings[prefix] = m['category']
            return mappings
    except Exception as e:
        raise RuntimeError(f"Error loading mappings file: {e}")


def process_symbols(symbols, mappings):
    categories = {}
    for sym in symbols:
        path = sym.get('path', [])
        if not path:
            continue
        size = sym.get('size', 0)
        if size == 0:
            continue

        # Check mappings
        matched = False
        for prefix, cat in mappings.items():
            if path[:len(prefix)] == list(prefix):
                cat_name = cat
                matched = True
                break

        if not matched:
            cat_name = path[0] if path else 'unknown'

        if cat_name not in categories:
            categories[cat_name] = 0
        categories[cat_name] += size
    return categories


def run_make_cosy(console, env_dir, board_name, filename):
    # Set environment variables locally for the subprocess
    env = os.environ.copy()
    env['BOARD'] = board_name
    env['BENCHMARK'] = filename

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
        f"[bold green]Processing {bench_name} on {board_name} with {env_name}[/bold green]")

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

    categories = process_symbols(data['symbols'], mappings)

    results = []
    for cat, size in categories.items():
        results.append({
            'benchmark': bench_name,
            'board': board_name,
            'environment': env_name,
            'category': cat,
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
                f, fieldnames=['benchmark', 'board', 'environment', 'category', 'size'])
            writer.writeheader()
            writer.writerows(results)
        print(f"Results written to {out_path}")
    except Exception as e:
        raise RuntimeError(f"Error writing CSV: {e}")


def generate_figures(results, figures_dir, console):
    """Generate a single faceted stacked bar chart.

    Rows = boards, Columns = benchmarks. Within each facet cell we plot one bar per environment
    (x-axis), stacked by category (color) representing total size contributed by that category.
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

    # Stacked bar: one bar per environment inside each (board, benchmark) facet cell
    chart = (
        alt.Chart(
            df, title="Memory distribution by Board / Benchmark / Environment")
        .mark_bar()
        .encode(
            x=alt.X('environment:N', title='Environment'),
            y=alt.Y('size:Q', stack='zero', title='Size (bytes)'),
            color=alt.Color('category:N', title='Category'),
            tooltip=[
                alt.Tooltip('board:N'),
                alt.Tooltip('benchmark:N'),
                alt.Tooltip('environment:N'),
                alt.Tooltip('category:N'),
                alt.Tooltip('size:Q', title='Size (bytes)')
            ]
        )
        .facet(
            row=alt.Row('board:N', title='Board'),
            column=alt.Column('benchmark:N', title='Benchmark')
        )
        .resolve_scale(y='independent')
    )

    out_file = os.path.join(figures_dir, "memory_distribution.html")
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
        generate_figures(results, args.figures, console)
        console.print("[bold green]All processing complete![/bold green]")
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()
