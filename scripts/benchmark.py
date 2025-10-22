#!/usr/bin/env python3
"""
Benchmark execution script for RIOT OS virtualization benchmarks.

This script executes benchmarks based on a YAML configuration file and collects
runtime data from various virtualization environments.
"""

import argparse
import csv
import os
import re
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text
from rich.table import Table
from rich.markdown import Markdown
import polars as pl
from rich.prompt import Confirm

from config import BenchmarkBoard, Config

console = Console()

def print_dict_as_table(console: Console,
                        data: dict,
                        title: str = "Dictionary Contents",
                        key_label: str = "Key",
                        value_label: str = "Value"
                        ) -> None:
    table = Table(title=title)
    table.add_column(key_label, style="bold")
    table.add_column(value_label)
    for key, value in data.items():
        table.add_row(str(key), str(value))
    console.print(table)


class BenchmarkRunner:
    """Main class for running benchmarks and collecting results."""

    def __init__(self, config_file: str, board: str, port: Optional[str] = None):
        """Initialize the benchmark runner.

        Args:
            config_file: Path to the YAML configuration file
            board: RIOT board target
            port: Optional serial port for flashing
        """
        self.config_file = config_file
        self.board = board
        self.port = port
        self.config = Config.from_yml(config_file)
        self.results = []

    def _run_command(self, command: List[str], cwd: str, monitor_benchmark: bool = False, env: Dict = {}) -> Dict[str, Any]:
        """Run a shell command in the specified directory with real-time output monitoring.

        Args:
            command: Command to execute as a list of strings
            cwd: Working directory for the command
            monitor_benchmark: Whether to monitor for benchmark markers and parse output

        Returns:
            Dictionary containing return code, captured output, and benchmark data if applicable
        """
        console.print(f"Running: {' '.join(command)} in {cwd}")
        print_dict_as_table(
            console, env, title="Command Env", key_label="Variable")

        env = {k: str(v) for k, v in env.items()}
        # If a key exists in both, the value from env (the right-hand side) overwrites the value from os.environ.copy().
        env = os.environ.copy() | env

        result = {
            'returncode': 0,
            'stdout': '',
            'stderr': '',
            'benchmark_data': []
        }

        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                start_new_session=True,
            )

            start_marker = "=== Benchmark Begins ==="
            end_marker = "=== Benchmark End ==="
            in_benchmark = False
            benchmark_lines = []
            all_output = []

            # Create a panel for command output
            command_title = f"Output: {' '.join(command)}"

            with Live(Panel("Starting command...", title=command_title), console=console, refresh_per_second=4) as live:
                pgid = None
                keyboard_interrupted = False
                try:
                    # Monitor output line by line
                    while True:
                        line = process.stdout.readline()
                        if not line:
                            break

                        line = line.rstrip('\n\r')
                        all_output.append(line)

                        # Remove timestamp prefix
                        cleaned_line = re.sub(
                            r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} # ', '', line)
                        if cleaned_line.startswith('#'):
                            cleaned_line = cleaned_line[1:].strip()

                        # Update the live display with recent output (last 15 lines)
                        recent_lines = all_output[-15:]
                        display_text = "\n".join(recent_lines)
                        live.update(
                            Panel(Text(display_text), title=command_title))

                        if monitor_benchmark:
                            cleaned_line_stripped = cleaned_line.strip()

                            if start_marker in cleaned_line_stripped:
                                in_benchmark = True
                                console.print(
                                    "[green]Found benchmark start marker[/green]"
                                )
                                continue
                            elif end_marker in cleaned_line_stripped and in_benchmark:
                                console.print(
                                    "[green]Found benchmark end marker - terminating process[/green]"
                                )
                                # Terminate the process when we find the end marker
                                process.terminate()
                                break
                            elif in_benchmark and cleaned_line_stripped:
                                benchmark_lines.append(cleaned_line_stripped)

                    pgid = os.getpgid(process.pid)
                    # Wait for process to finish and get return code
                    return_code = process.wait(
                        timeout=30
                    )  # Give it some time to clean up

                    console.print(f"return_code = {return_code}")

                except subprocess.TimeoutExpired:
                    console.print(
                        "[yellow]Process cleanup timed out, force killing...[/yellow]"
                    )
                    process.kill()
                    process.wait()

                except KeyboardInterrupt:
                    console.print("Received Keyboard interrupt")
                    keyboard_interrupted = True

                finally:
                    if process is not None and pgid is not None:
                        try:
                            # This gives pyterm a chance to reset the terminal settings.
                            os.killpg(pgid, signal.SIGTERM)

                            print("Cleanup: Waiting 2s for polite shutdown...")
                            time.sleep(2)

                            # 5. Send SIGKILL to the *entire group*
                            # For a benchmark, it's safest to be aggressive.
                            # SIGTERM is polite, SIGKILL is guaranteed.
                            os.killpg(pgid, signal.SIGKILL)
                            console.print("Process group killed.")

                        except ProcessLookupError:
                            # This is not an error. It just means the process
                            # group was already gone when we tried to kill it.
                            console.print("Process group already gone.")

                        # reap the process
                        process.wait()

                    if keyboard_interrupted:
                        console.print("Received keyboard interrupt, Exiting...")
                        sys.exit(0)

            result['returncode'] = process.returncode
            result['stdout'] = '\n'.join(all_output)

            # Process benchmark data if we were monitoring
            if monitor_benchmark and benchmark_lines:
                result['benchmark_data'] = self._parse_benchmark_lines(
                    benchmark_lines)

        except Exception as e:
            console.print(f"Error running command: {e}", markup=False)
            result['returncode'] = -1
            raise

        return result

    def _parse_benchmark_lines(self, benchmark_lines: List[str]) -> List[Dict[str, str]]:
        """Parse benchmark lines to extract CSV data.

        Args:
            benchmark_lines: List of benchmark output lines between markers

        Returns:
            List of dictionaries containing parsed benchmark data
        """
        csv_lines = []
        header_line = None

        for line in benchmark_lines:
            if not header_line and 'iteration' in line.lower():
                header_line = line
            elif header_line and ';' in line:
                csv_lines.append(line)

        if not header_line or not csv_lines:
            console.print(
                "Warning: No valid benchmark data found in output", style="yellow")
            return []

        # Parse CSV data
        results = []
        try:
            # Use semicolon as delimiter
            reader = csv.DictReader([header_line] + csv_lines, delimiter=';')
            for row in reader:
                results.append(dict(row))
        except Exception as e:
            console.print(f"Error parsing CSV data: {e}", markup=False)
            return []

        return results

    def _run_benchmark_for_environment(self, benchmark: BenchmarkBoard, env_entry: Dict[str, Any]) -> bool:
        """Run a benchmark for a specific environment.

        Args:
            benchmark: Benchmark configuration
            env_entry: Environment entry dict

        Returns:
            True if benchmark completed successfully, False otherwise
        """
        env_name = env_entry['name']
        env_label = env_entry.get('label', env_name)
        env_vars = env_entry.get('env', {})
        env_dir = Path(env_name)
        if not env_dir.exists():
            console.print(
                f"Warning: Environment directory '{env_name}' does not exist. Skipping.", style="yellow")
            return False

        benchmark_header = Markdown(
            f"# Running benchmark '{benchmark.name}' in environment '{env_label}'"
        )
        console.print(benchmark_header)

        try:
            console.print("Building...")

            command_env = {
                'BOARD': self.board,
                'BENCHMARK': benchmark.filename,
                'SCALE_FACTOR': benchmark.scale_factor,
                'ITERATIONS': benchmark.iterations,
                **({'PORT': self.port} if self.port else {}),
                **env_vars
            }

            build_result = self._run_command(
                ['make', 'all'],
                str(env_dir),
                env=command_env)

            if build_result['returncode'] != 0:
                console.print(
                    f"Build failed for {env_label}", style="bold red")
                return False

            # Step 2: Flash (only if board is not native)
            if self.board.lower() != 'native':
                console.print("Flashing...", style="bold")
                flash_result = self._run_command(
                    ['make', 'flash'], str(env_dir), env=command_env)

                if flash_result['returncode'] != 0:
                    console.print(
                        f"Flash failed for {env_label}", style="bold red")
                    return False

            time.sleep(1)  # sometimes
            # Step 3: Run and capture output with real-time monitoring

            # Retry loop: re-run terminal and prompt user on failure
            max_attempts = int(os.environ.get("BENCH_MAX_ATTEMPTS", "3"))
            attempt = 1
            benchmark_data = []
            while attempt <= max_attempts:
                console.print(
                    f"Running benchmark and monitoring output... (attempt {attempt}/{max_attempts})",
                    style="bold",
                )

                term_result = self._run_command(
                    ["make", "term"],
                    str(env_dir),
                    monitor_benchmark=True,
                    env=command_env,
                )

                # Use benchmark data from real-time monitoring
                benchmark_data = term_result.get("benchmark_data", [])

                if benchmark_data:
                    break

                console.print(
                    f"No valid benchmark data extracted from {env_label}.",
                    style="yellow",
                )

                if attempt >= max_attempts:
                    # Either reached max attempts or cannot prompt
                    return False

                retry = Confirm.ask(
                    "Retry running this benchmark?",
                    default=True,
                )
                if not retry:
                    return False

                attempt += 1

            # Add benchmark name and environment to each row
            for row in benchmark_data:
                row['benchmark'] = benchmark.name
                row['environment'] = env_label
                row['board'] = benchmark.board_name
                row['scale_factor'] = benchmark.scale_factor
                self.results.append(row)

            console.print(
                f"Successfully collected {len(benchmark_data)} data points from {env_label}")
            return True

        except Exception as e:
            console.print(
                f"Error running benchmark in {env_label}: {e}", markup=False)
            return False

    def run_benchmarks(self) -> None:
        """Run all benchmarks defined in the configuration."""
        for bench in self.config.benchmarks:
            # Only run combos matching the selected board
            if bench.board_name.lower() != self.board.lower():
                continue

            supported_envs = bench.supported_environments or []

            if not supported_envs:
                console.print(
                    f"Warning: No supported environments for board '{self.board}' in benchmark '{bench.name}'. Skipping.")
                continue

            console.print(
                f"\n=== Processing benchmark: {bench.name} (board: {self.board}) ===")

            for env_entry in supported_envs:
                if env_entry.get('disabled', False):
                    continue
                env_name = env_entry['name']
                env_label = env_entry.get('label', env_name)

                success = self._run_benchmark_for_environment(bench, env_entry)
                if not success:
                    console.print(
                        f"Failed to run benchmark '{bench.name}' in environment '{env_label}'")

    def write_results_to_csv(self, output_file: str) -> None:
        """Write collected results to a CSV file.

        Args:
            output_file: Path to the output CSV file
        """
        if not self.results:
            console.print("No results to write.", style="yellow")
            return

        try:
            # Get all possible field names from all results
            fieldnames = set()
            for result in self.results:
                fieldnames.update(result.keys())
            fieldnames = sorted(list(fieldnames))

            with open(output_file, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.results)

            console.print(f"\nResults written to: {output_file}")
            console.print(f"Total data points: {len(self.results)}")

        except Exception as e:
            console.print(f"Error writing results to CSV: {e}", markup=False)
            sys.exit(1)

    def display_aggregated_results(self) -> None:
        """Display aggregated benchmark statistics in a rich table.

        Groups results by (board, benchmark, environment) and computes mean and
        standard deviation for execution_time_us, init_runtime_us, and load_program_us.
        """
        if not self.results:
            console.print(
                "No results collected yet. Run benchmarks first.", style="yellow")
            return

        # Convert list of dicts to Polars DataFrame
        try:
            df = pl.DataFrame(self.results)
        except Exception as e:
            console.print(f"Failed creating DataFrame: {e}", style="red")
            return

        # Ensure numeric columns are correct dtypes if present
        numeric_cols = [
            "execution_time_us",
            "init_runtime_us",
            "load_program_us",
        ]

        for col in numeric_cols:
            df = df.with_columns(pl.col(col).cast(pl.Float64))

        required_cols = {"board", "benchmark", "environment"}
        if not required_cols.issubset(set(df.columns)):
            console.print(
                "Missing required columns for aggregation.", style="red")
            return

        # Perform aggregation
        agg_exprs = []
        for col in numeric_cols:
            if col in df.columns:
                agg_exprs.extend([
                    pl.col(col).mean().alias(f"{col}_mean"),
                    pl.col(col).std().alias(f"{col}_std"),
                ])

        if not agg_exprs:
            console.print(
                "No numeric timing columns found to aggregate.", style="yellow")
            return

        grouped = (
            # type: ignore[arg-type]
            df.group_by(["board", "benchmark", "environment"])
              .agg(agg_exprs)
              .sort(["board", "benchmark", "environment"])
        )

        # Build rich table
        table = Table(title="Aggregated Benchmark Results", show_lines=False)
        table.add_column("Board", style="bold")
        table.add_column("Benchmark", style="bold")
        table.add_column("Environment", style="bold")

        for col in numeric_cols:
            if f"{col}_mean" in grouped.columns:
                table.add_column(f"{col} (mean)", justify="right")
                table.add_column(f"{col} (std)", justify="right")

        # Add rows
        for row in grouped.iter_rows(named=True):  # type: ignore
            cells = [
                str(row.get("board", "")),
                str(row.get("benchmark", "")),
                str(row.get("environment", "")),
            ]
            for col in numeric_cols:
                mean_key = f"{col}_mean"
                std_key = f"{col}_std"
                if mean_key in row:
                    mean_val = row[mean_key]
                    std_val = row[std_key]
                    cells.append(
                        f"{mean_val:.2f}" if mean_val is not None else "-")
                    cells.append(
                        f"{std_val:.2f}" if std_val is not None else "-")
            table.add_row(*cells)

        console.print(table)


def main():
    """Main entry point for the benchmark script."""
    parser = argparse.ArgumentParser(
        description="Run RIOT OS virtualization benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--config',
        required=True,
        help='Path to the YAML configuration file'
    )

    parser.add_argument(
        '--board',
        required=True,
        help='RIOT board target (e.g., native, esp32, etc.)'
    )

    parser.add_argument(
        '--port',
        help='Serial port for flashing (optional)'
    )

    parser.add_argument(
        '--write-csv',
        required=True,
        dest='output_csv',
        help='Path to write the results CSV file'
    )

    args = parser.parse_args()

    # Validate configuration file exists
    if not os.path.exists(args.config):
        console.print(f"Error: Configuration file '{args.config}' not found.")
        sys.exit(1)

    # Create output directory if needed
    output_dir = os.path.dirname(args.output_csv)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Run benchmarks
    runner = BenchmarkRunner(args.config, args.board, args.port)
    runner.run_benchmarks()
    runner.display_aggregated_results()
    runner.write_results_to_csv(args.output_csv)


if __name__ == '__main__':
    main()
