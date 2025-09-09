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
import subprocess
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.text import Text


console = Console()


@dataclass
class BenchmarkBoard:
    """Represents a single benchmark configuration for a specific board.

    One object corresponds to a (benchmark x board) combination parsed from YAML.
    """

    # Benchmark-level fields
    name: str
    filename: str
    global_scale_factor: int
    iterations: int

    # Board-level fields
    board_name: str
    supported_environments: List[str] = field(default_factory=list)


class Config:
    """Configuration class that loads and provides access to benchmark configuration."""

    def __init__(self, benchmarks: List[BenchmarkBoard]):
        """Initialize config with parsed data.

        Args:
            benchmarks: List of (benchmark x board) configuration objects
        """
        self.benchmarks: List[BenchmarkBoard] = benchmarks

    @classmethod
    def from_yml(cls, config_file: str) -> 'Config':
        """Load configuration from a YAML file.

        Args:
            config_file: Path to the YAML configuration file

        Returns:
            Config object with loaded configuration

        Raises:
            SystemExit: If file not found or YAML parsing fails
        """
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)

            if not isinstance(config_data, dict) or 'benchmarks' not in config_data:
                console.print(
                    "Error: No 'benchmarks' section found in configuration file.", style="bold red")
                sys.exit(1)

            combos: List[BenchmarkBoard] = []

            for bench in config_data.get('benchmarks', []) or []:
                b_name = str(bench.get('name', '')).strip()
                if not b_name:
                    # Skip unnamed benchmarks
                    continue

                filename = str(bench.get('filename', b_name)).strip() or b_name
                gsf = bench.get('global_scale_factor', 1)
                gsf = int(gsf)

                iterations = int(bench.get('iterations', 1))

                boards = bench.get('boards', []) or []
                for board in boards:
                    board_name = str((board or {}).get(
                        'board_name', '')).strip()
                    if not board_name:
                        # Skip board entries without a name
                        continue
                    envs_raw = (board or {}).get(
                        'supported_environments', []) or []
                    envs: List[str] = []
                    for e in envs_raw:
                        if isinstance(e, dict):
                            ename = e.get('name')
                        else:
                            ename = e

                        if ename:
                            envs.append(str(ename).strip())

                    combos.append(
                        BenchmarkBoard(
                            name=b_name,
                            filename=filename,
                            global_scale_factor=gsf,
                            iterations=iterations,
                            board_name=board_name,
                            supported_environments=envs,
                        )
                    )

            return cls(benchmarks=combos)

        except FileNotFoundError:
            console.print(
                f"Error: Configuration file '{config_file}' not found.", style="bold red")
            sys.exit(1)
        except yaml.YAMLError as e:
            console.print(
                f"Error parsing YAML configuration: {e}", markup=False)
            sys.exit(1)


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
        env = os.environ.copy() | env
        env['BOARD'] = self.board
        if self.port:
            env['PORT'] = self.port

        console.print(f"Running: {' '.join(command)} in {cwd}")

        # Initialize result structure
        result = {
            'returncode': 0,
            'stdout': '',
            'stderr': '',
            'benchmark_data': []
        }

        try:
            # Start the process
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Real-time monitoring variables
            start_marker = "=== Benchmark Begins ==="
            end_marker = "=== Benchmark End ==="
            in_benchmark = False
            benchmark_lines = []
            all_output = []

            # Create a panel for command output
            command_title = f"Output: {' '.join(command)}"

            with Live(Panel("Starting command...", title=command_title), console=console, refresh_per_second=4) as live:
                try:
                    # Monitor output line by line
                    while True:
                        line = process.stdout.readline()
                        if not line:
                            break

                        line = line.rstrip('\n\r')
                        all_output.append(line)

                        # Clean the line for display and parsing
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
                                    f"[green]Found benchmark start marker[/green]")
                                continue
                            elif end_marker in cleaned_line_stripped and in_benchmark:
                                console.print(
                                    f"[green]Found benchmark end marker - terminating process[/green]")
                                # Terminate the process when we find the end marker
                                process.terminate()
                                break
                            elif in_benchmark and cleaned_line_stripped:
                                benchmark_lines.append(cleaned_line_stripped)

                    # Wait for process to finish and get return code
                    process.wait(timeout=30)  # Give it some time to clean up

                except subprocess.TimeoutExpired:
                    console.print(
                        "[yellow]Process cleanup timed out, force killing...[/yellow]")
                    process.kill()
                    process.wait()

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

    def _run_benchmark_for_environment(self, benchmark: BenchmarkBoard, env_name: str) -> bool:
        """Run a benchmark for a specific environment.

        Args:
            benchmark: Benchmark configuration
            env_name: Environment name (directory name)

        Returns:
            True if benchmark completed successfully, False otherwise
        """
        env_dir = Path(env_name)
        if not env_dir.exists():
            console.print(
                f"Warning: Environment directory '{env_name}' does not exist. Skipping.", style="yellow")
            return False

        console.print(
            f"\n--- Running benchmark '{benchmark.name}' in environment '{env_name}' ---")

        try:
            console.print("Building...")

            command_env = {
                'BOARD': self.board,
                'BENCHMARK': benchmark.filename,
                **({'PORT': self.port} if self.port else {})
            }

            build_result = self._run_command(
                ['make', 'all'],
                str(env_dir),
                env=command_env)

            if build_result['returncode'] != 0:
                console.print(f"Build failed for {env_name}", style="bold red")
                return False

            # Step 2: Flash (only if board is not native)
            if self.board.lower() != 'native':
                console.print("Flashing...", style="bold")
                flash_result = self._run_command(
                    ['make', 'flash'], str(env_dir), env=command_env)

                if flash_result['returncode'] != 0:
                    console.print(
                        f"Flash failed for {env_name}", style="bold red")
                    return False

            # Step 3: Run and capture output with real-time monitoring
            console.print(
                "Running benchmark and monitoring output...", style="bold")
            term_result = self._run_command(
                ['make', 'term'], str(env_dir), monitor_benchmark=True, env=command_env)

            # Use benchmark data from real-time monitoring
            benchmark_data = term_result['benchmark_data']

            if not benchmark_data:
                console.print(
                    f"No valid benchmark data extracted from {env_name}", style="yellow")
                return False

            # Add benchmark name and environment to each row
            for row in benchmark_data:
                row['benchmark'] = benchmark.name
                row['environment'] = env_name
                row['board'] = benchmark.board_name
                self.results.append(row)

            console.print(
                f"Successfully collected {len(benchmark_data)} data points from {env_name}")
            return True

        except Exception as e:
            console.print(
                f"Error running benchmark in {env_name}: {e}", markup=False)
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
                env_name = env_entry
                if not env_name:
                    console.print("Warning: Encountered environment entry without a name. Skipping.")
                    continue
                success = self._run_benchmark_for_environment(bench, env_name)
                if not success:
                    console.print(
                        f"Failed to run benchmark '{bench.name}' in environment '{env_name}'")

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
    runner.write_results_to_csv(args.output_csv)


if __name__ == '__main__':
    main()
