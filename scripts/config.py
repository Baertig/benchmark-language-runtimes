import yaml
import sys
from typing import List, Dict, Any
from dataclasses import dataclass, field
from rich.console import Console

console = Console()


@dataclass
class BenchmarkBoard:
    """Represents a single benchmark configuration for a specific board.

    One object corresponds to a (benchmark x board) combination parsed from YAML.
    """

    # Benchmark-level fields
    name: str
    filename: str
    scale_factor: int
    iterations: int

    # Board-level fields
    board_name: str
    supported_environments: List[Dict[str, Any]] = field(default_factory=list)


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
                scale_factor = bench.get('scale_factor', 1)
                scale_factor = int(scale_factor)

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
                    envs: List[Dict[str, Any]] = []
                    for e in envs_raw:
                        if isinstance(e, dict):
                            envs.append(e)
                        else:
                            envs.append({'name': str(e).strip()})

                    combos.append(
                        BenchmarkBoard(
                            name=b_name,
                            filename=filename,
                            scale_factor=scale_factor,
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
