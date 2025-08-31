"""Command-line interface for static frequency list generation.

DEPRECATED: This module is deprecated. Use the main CLI instead:
- radiobridge list-static
- radiobridge generate-static

This module is kept for backward compatibility.
"""

import argparse
import sys
import warnings
from typing import List, Optional

from radiobridge.static_commands import (
    list_available_static_lists,
    generate_static_lists,
    save_static_output,
    format_static_list_info,
)
from radiobridge.logging_config import get_logger


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for static frequency list CLI."""
    parser = argparse.ArgumentParser(
        description="Generate static frequency lists for amateur radio",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate all national calling frequencies
  python -m radiobridge.static_cli national_calling -o calling_freqs.csv

  # Generate only 2m and 70cm calling frequencies
  python -m radiobridge.static_cli national_calling --bands 2m 70cm \
    -o calling_freqs.csv

  # Generate emergency simplex frequencies
  python -m radiobridge.static_cli emergency_simplex -o emergency_freqs.csv

  # Generate multiple lists combined
  python -m radiobridge.static_cli national_calling emergency_simplex \
    -o combined_freqs.csv

  # List available static frequency lists
  python -m radiobridge.static_cli --list

Supported Bands:
  - 2m (146.52 MHz calling)
  - 1.25m (223.5 MHz calling)
  - 70cm (446.0 MHz calling)
        """,
    )

    # Main command - list of static lists to generate
    parser.add_argument(
        "lists",
        nargs="*",
        help="Static frequency lists to generate (national_calling, emergency_simplex)",
    )

    # Options
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available static frequency lists and exit",
    )

    parser.add_argument(
        "--bands",
        nargs="+",
        choices=["2m", "1.25m", "70cm"],
        help="Filter to specific amateur radio bands",
    )

    parser.add_argument(
        "--location",
        default="National",
        help="Location description for the frequencies (default: National)",
    )

    parser.add_argument(
        "-o", "--output", help="Output CSV file path (default: print to stdout)"
    )

    parser.add_argument(
        "--separate",
        action="store_true",
        help="Save each list to separate files (requires --output with {} placeholder)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    return parser


def list_available_lists() -> None:
    """Display available static frequency lists."""
    available = list_available_static_lists()

    print("Available Static Frequency Lists:")
    print("=" * 40)

    for list_name, info in available.items():
        print(f"\n{list_name}:")
        print(format_static_list_info(info))


def generate_lists(
    list_names: List[str],
    bands: Optional[List[str]] = None,
    location: str = "National",
    separate: bool = False,
) -> dict:
    """Generate specified static frequency lists.

    Args:
        list_names: Names of lists to generate
        bands: Optional band filtering
        location: Location description
        separate: Whether to return separate DataFrames

    Returns:
        Dictionary of list names to DataFrames
    """
    return generate_static_lists(list_names, bands, location)


def save_output(data: dict, output_path: Optional[str], separate: bool) -> None:
    """Save generated frequency data to files or stdout.

    Args:
        data: Dictionary of list names to DataFrames
        output_path: Output file path (may contain {} placeholder for separate files)
        separate: Whether to save separate files
    """
    save_static_output(data, output_path, separate)


def main() -> int:
    """Run the main CLI entry point."""
    # Issue deprecation warning
    warnings.warn(
        "The 'python -m radiobridge.static_cli' interface is deprecated. "
        "Use 'radiobridge list-static' and 'radiobridge generate-static' instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    parser = create_parser()
    args = parser.parse_args()

    # Configure logging
    logger = get_logger(__name__)
    if args.verbose:
        import logging

        logging.getLogger("radiobridge").setLevel(logging.DEBUG)

    try:
        # List available lists
        if args.list:
            list_available_lists()
            return 0

        # Validate arguments
        if not args.lists:
            parser.error(
                "Must specify at least one static frequency list or use --list"
            )

        # Generate frequency lists
        data = generate_lists(
            args.lists, bands=args.bands, location=args.location, separate=args.separate
        )

        # Save output
        save_output(data, args.output, args.separate)

        # Print summary
        total_freqs = sum(len(df) for df in data.values())
        logger.info(
            f"Generated {total_freqs} total frequencies from {len(data)} list(s)"
        )

        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
