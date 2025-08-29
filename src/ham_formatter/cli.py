"""Command-line interface for ham_formatter."""

import sys
from pathlib import Path
from typing import Optional

import click

from ham_formatter import __version__
from ham_formatter.csv_utils import read_csv, write_csv
from ham_formatter.downloader import download_repeater_data
from ham_formatter.radios import get_supported_radios, get_radio_formatter


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def main(ctx: click.Context) -> None:
    """Ham Formatter - Download and format amateur radio repeater lists.

    A tool for downloading repeater information from RepeaterBook.com and formatting
    it for various ham radio models including Anytone, Baofeng, and others.
    """
    ctx.ensure_object(dict)


@main.command()
@click.option(
    "--state",
    "-s",
    required=True,
    help="State/province code to download repeaters for (e.g., 'CA', 'TX')",
)
@click.option(
    "--country",
    "-c",
    default="United States",
    help="Country name (default: 'United States')",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: repeaters_<state>.csv)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def download(state: str, country: str, output: Optional[Path], verbose: bool) -> None:
    """Download repeater data from RepeaterBook.com."""
    if verbose:
        click.echo(f"Downloading repeater data for {state}, {country}...")

    try:
        data = download_repeater_data(state=state, country=country)

        if output is None:
            output = Path(f"repeaters_{state.lower()}.csv")

        write_csv(data, output)

        click.echo(f"Successfully downloaded {len(data)} repeaters to {output}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--radio",
    "-r",
    required=True,
    help="Target radio model (use 'list-radios' to see supported models)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Output file path (default: formatted_<radio>_<input_name>.csv)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def format(input_file: Path, radio: str, output: Optional[Path], verbose: bool) -> None:
    """Format repeater data for a specific radio model."""
    if verbose:
        click.echo(f"Formatting {input_file} for {radio}...")

    try:
        # Load the data
        data = read_csv(input_file)

        # Get the formatter for the specified radio
        formatter = get_radio_formatter(radio)
        if formatter is None:
            supported = ", ".join(get_supported_radios())
            click.echo(
                f"Error: Unsupported radio '{radio}'. Supported radios: {supported}",
                err=True,
            )
            sys.exit(1)

        # Format the data
        formatted_data = formatter.format(data)

        # Determine output path
        if output is None:
            input_stem = input_file.stem
            output = Path(f"formatted_{radio.lower()}_{input_stem}.csv")

        # Write the formatted data
        write_csv(formatted_data, output)

        click.echo(
            f"Successfully formatted {len(formatted_data)} entries for "
            f"{radio} to {output}"
        )

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("list-radios")
def list_radios() -> None:
    """List all supported radio models."""
    radios = get_supported_radios()

    if not radios:
        click.echo("No supported radios found.")
        return

    click.echo("Supported radio models:")
    for radio in sorted(radios):
        click.echo(f"  • {radio}")


if __name__ == "__main__":
    main()
