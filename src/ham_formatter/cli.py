"""Command-line interface for ham_formatter."""

import sys
from pathlib import Path
from typing import Optional

import click

from ham_formatter import __version__
from ham_formatter.csv_utils import read_csv, write_csv
from ham_formatter.downloader import (
    download_repeater_data,
    download_repeater_data_by_county,
    download_repeater_data_by_city,
)
from ham_formatter.logging_config import setup_logging, get_logger
from ham_formatter.radios import get_supported_radios, get_radio_formatter


@click.group()
@click.version_option(version=__version__)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging output")
@click.option("--log-file", type=click.Path(), help="Write logs to specified file")
@click.pass_context
def main(ctx: click.Context, verbose: bool, log_file: Optional[str]) -> None:
    """Ham Formatter - Download and format amateur radio repeater lists.

    A tool for downloading repeater information from RepeaterBook.com and formatting
    it for various ham radio models including Anytone, Baofeng, and others.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["log_file"] = log_file

    # Set up logging early
    setup_logging(verbose=verbose, log_file=log_file)


@main.command()
@click.option(
    "--state",
    "-s",
    help="State/province code (e.g., 'CA', 'TX') - required for all searches",
)
@click.option(
    "--county",
    help="County name to filter by (e.g., 'Los Angeles', 'Harris')",
)
@click.option(
    "--city",
    help="City name to filter by (e.g., 'Los Angeles', 'Austin')",
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
    help="Output file path (default: auto-generated based on search criteria)",
)
@click.pass_context
def download(
    ctx: click.Context,
    state: Optional[str],
    county: Optional[str],
    city: Optional[str],
    country: str,
    output: Optional[Path],
) -> None:
    """Download repeater data from RepeaterBook.com.

    You can download repeaters by:
    - State only: --state CA
    - County within state: --state CA --county "Los Angeles"
    - City within state: --state TX --city Austin

    Note: --state is required for all searches.
    """
    logger = get_logger(__name__)

    # Validate search criteria
    search_options = [bool(county), bool(city)]
    num_search_options = sum(search_options)

    if num_search_options > 1:
        click.echo("Error: Cannot specify both --county and --city", err=True)
        sys.exit(1)

    if not state:
        click.echo("Error: --state is required for all searches", err=True)
        sys.exit(1)

    if (county or city) and not state:
        click.echo("Error: --state is required when using --county or --city", err=True)
        sys.exit(1)

    # Determine search type and parameters
    if county:
        search_type = "county"
        logger.info(f"Starting download for {county} County, {state}, {country}")
    elif city:
        search_type = "city"
        logger.info(f"Starting download for {city}, {state}, {country}")
    else:
        search_type = "state"
        logger.info(f"Starting download for {state}, {country}")

    try:
        # Call appropriate download function
        if search_type == "county":
            data = download_repeater_data_by_county(
                state=state, county=county, country=country
            )
        elif search_type == "city":
            data = download_repeater_data_by_city(
                state=state, city=city, country=country
            )
        else:
            data = download_repeater_data(state=state, country=country)

        # Generate output filename if not provided
        if output is None:
            state_lower = state.lower()
            if search_type == "county":
                county_safe = county.replace(" ", "_").lower()
                output = Path(f"repeaters_{state_lower}_{county_safe}.csv")
            elif search_type == "city":
                city_safe = city.replace(" ", "_").lower()
                output = Path(f"repeaters_{state_lower}_{city_safe}.csv")
            else:
                output = Path(f"repeaters_{state_lower}.csv")

        write_csv(data, output)

        # Success message
        if search_type == "county":
            location = f"{county} County, {state}"
        elif search_type == "city":
            location = f"{city}, {state}"
        else:
            location = state

        click.echo(
            f"Successfully downloaded {len(data)} repeaters from {location} to {output}"
        )
        logger.info(f"Download completed: {len(data)} repeaters saved to {output}")

    except Exception as e:
        logger.error(f"Download failed: {e}")
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
@click.pass_context
def format(
    ctx: click.Context, input_file: Path, radio: str, output: Optional[Path]
) -> None:
    """Format repeater data for a specific radio model."""
    logger = get_logger(__name__)
    logger.info(f"Starting format operation: {input_file} for {radio}")

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
        logger.info(
            f"Format completed: {len(formatted_data)} entries for {radio} saved to {output}"
        )

    except Exception as e:
        logger.error(f"Format failed: {e}")
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
