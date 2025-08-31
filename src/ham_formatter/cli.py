"""Command-line interface for ham_formatter."""

import sys
from pathlib import Path
from typing import Optional

import click

from ham_formatter import __version__
from ham_formatter.band_filter import (
    validate_bands,
    format_band_list,
)
from ham_formatter.csv_utils import (
    read_csv,
    write_csv,
    write_csv_with_comments,
    read_csv_comments,
)
from ham_formatter.downloader import (
    download_repeater_data,
    download_repeater_data_by_county,
    download_repeater_data_by_city,
)
from ham_formatter.detailed_downloader import (
    download_with_details,
    download_with_details_by_county,
    download_with_details_by_city,
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
@click.option(
    "--band",
    "-b",
    multiple=True,
    help="Amateur radio band(s) to include (e.g., 2m, 70cm, all). "
    "Can be specified multiple times.",
)
# Detailed downloads are now the default and only option
@click.option(
    "--rate-limit",
    type=float,
    default=1.0,
    help="Minimum seconds between requests when using --detailed (default: 1.0)",
)
@click.option(
    "--temp-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Directory for temporary files during detailed collection "
    "(default: system temp)",
)
@click.option(
    "--nohammer",
    "-n",
    is_flag=True,
    help="Use random rate limiting (1-10 seconds) to be extra respectful to servers",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging to show all collected data from each detail page",
)
@click.pass_context
def download(
    ctx: click.Context,
    state: Optional[str],
    county: Optional[str],
    city: Optional[str],
    country: str,
    output: Optional[Path],
    band: tuple,
    # detailed parameter removed - always True
    rate_limit: float,
    temp_dir: Optional[Path],
    nohammer: bool,
    debug: bool,
) -> None:
    """Download repeater data from RepeaterBook.com.

    You can download repeaters by:
    - State only: --state CA
    - County within state: --state CA --county "Los Angeles"
    - City within state: --state TX --city Austin

    Band filtering:
    - All bands (default): no --band option or --band all
    - Single band: --band 2m
    - Multiple bands: --band 2m --band 70cm
    - Supported bands: 6m, 4m, 2m, 70cm, 33cm, 23cm

    All downloads include detailed information from individual repeater pages.
    - Use --rate-limit to control request frequency (default: 1.0 seconds)
    - Use --temp-dir to specify where temporary files are stored
    - Use --nohammer to enable random rate limiting (1-10s) for extra server respect

    Note: --state is required for all searches.
    """
    # Reconfigure logging if debug mode is requested
    if debug:
        setup_logging(verbose=True, log_file=ctx.obj.get("log_file"))

    logger = get_logger(__name__)

    # Validate and process band filtering
    try:
        bands = validate_bands(list(band)) if band else ["all"]
        logger.debug(f"Requested bands: {list(band)} -> normalized: {bands}")
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

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

    # Handle nohammer option - log it but don't change rate_limit here
    if nohammer:
        logger.info(
            "No-hammer mode enabled: will use random delays (1-10s) "
            "for each detail request"
        )

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
        # All downloads now use detailed scraping for comprehensive data
        if nohammer:
            logger.info(
                "Using detailed scraping with no-hammer mode " "(random delays 1-10s)"
            )
        else:
            logger.info(f"Using detailed scraping with rate limit: {rate_limit}s")

        if search_type == "county":
            data = download_with_details_by_county(
                state=state,
                county=county,
                country=country,
                bands=bands,
                rate_limit=rate_limit,
                temp_dir=temp_dir,
                nohammer=nohammer,
                debug=debug,
            )
        elif search_type == "city":
            data = download_with_details_by_city(
                state=state,
                city=city,
                country=country,
                bands=bands,
                rate_limit=rate_limit,
                temp_dir=temp_dir,
                nohammer=nohammer,
                debug=debug,
            )
        else:
            data = download_with_details(
                state=state,
                country=country,
                bands=bands,
                rate_limit=rate_limit,
                temp_dir=temp_dir,
                nohammer=nohammer,
                debug=debug,
            )

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

        # Build metadata comments for the CSV file
        metadata_comments = {
            "country": country,
            "state": state,
        }

        if search_type == "county":
            metadata_comments["county"] = county
        elif search_type == "city":
            metadata_comments["city"] = city

        if bands != ["all"]:
            metadata_comments["bands"] = ", ".join(bands)

        metadata_comments["download_type"] = "detailed"
        metadata_comments["total_repeaters"] = str(len(data))

        # Write CSV with metadata comments
        write_csv_with_comments(data, output, comments=metadata_comments)

        # Success message
        if search_type == "county":
            location = f"{county} County, {state}"
        elif search_type == "city":
            location = f"{city}, {state}"
        else:
            location = state

        band_desc = format_band_list(bands)
        click.echo(
            f"Successfully downloaded {len(data)} repeaters from {location} "
            f"({band_desc}) to {output}"
        )
        logger.info(
            f"Download completed: {len(data)} repeaters from {band_desc} "
            f"saved to {output}"
        )

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
@click.option(
    "--start-channel",
    "-s",
    type=int,
    default=1,
    help="Starting channel number for the output (default: 1)",
)
@click.option(
    "--zones",
    is_flag=True,
    help="Generate zone file alongside channel file (if radio supports it)",
)
@click.option(
    "--zone-strategy",
    type=click.Choice(["location", "band", "service", "mixed"]),
    default="location",
    help="Strategy for creating zones (default: location)",
)
@click.option(
    "--max-zones",
    type=int,
    default=250,
    help="Maximum number of zones to create (default: 250)",
)
@click.option(
    "--max-channels-per-zone",
    type=int,
    default=64,
    help="Maximum channels per zone (default: 64)",
)
@click.pass_context
def format(
    ctx: click.Context,
    input_file: Path,
    radio: str,
    output: Optional[Path],
    start_channel: int,
    zones: bool,
    zone_strategy: str,
    max_zones: int,
    max_channels_per_zone: int,
) -> None:
    """Format repeater data for a specific radio model."""
    logger = get_logger(__name__)
    logger.info(f"Starting format operation: {input_file} for {radio}")

    try:
        # Read CSV comments for metadata
        csv_metadata = read_csv_comments(input_file)
        logger.debug(f"CSV metadata: {csv_metadata}")

        # Load the data (comments will be ignored)
        data = read_csv(input_file, comment="#")

        # Get the formatter for the specified radio
        formatter = get_radio_formatter(radio)
        if formatter is None:
            supported = ", ".join(get_supported_radios())
            click.echo(
                f"Error: Unsupported radio '{radio}'. Supported radios: {supported}",
                err=True,
            )
            sys.exit(1)

        # Format the data with start channel
        formatted_data = formatter.format(data, start_channel=start_channel)

        if start_channel != 1:
            logger.info(f"Using custom start channel: {start_channel}")

        # Determine output path
        if output is None:
            input_stem = input_file.stem
            output = Path(f"formatted_{radio.lower()}_{input_stem}.csv")

        # Write the formatted data
        write_csv(formatted_data, output)

        files_created = [str(output)]

        # Generate zone file if requested
        if zones:
            if formatter.supports_zone_files():
                logger.info(f"Generating zone file using strategy: {zone_strategy}")

                try:
                    zone_data = formatter.format_zones(
                        formatted_data,
                        csv_metadata=csv_metadata,
                        zone_strategy=zone_strategy,
                        max_zones=max_zones,
                        max_channels_per_zone=max_channels_per_zone,
                    )

                    # Create zone file name
                    zone_output = (
                        output.with_suffix("")
                        .with_name(output.stem + "_zones")
                        .with_suffix(".csv")
                    )
                    write_csv(zone_data, zone_output)
                    files_created.append(str(zone_output))

                    logger.info(
                        f"Zone file created: {zone_output} with {len(zone_data)} zones"
                    )

                except Exception as e:
                    logger.warning(f"Failed to generate zone file: {e}")
                    click.echo(f"Warning: Failed to generate zone file: {e}", err=True)
            else:
                logger.warning(f"{radio} does not support zone file generation")
                click.echo(
                    f"Warning: {radio} does not support zone file generation", err=True
                )

        # Success message
        if len(files_created) == 1:
            click.echo(
                f"Successfully formatted {len(formatted_data)} entries for "
                f"{radio} to {output}"
            )
        else:
            click.echo(
                f"Successfully formatted {len(formatted_data)} entries for "
                f"{radio} to {len(files_created)} files: {', '.join(files_created)}"
            )

        logger.info(
            f"Format completed: {len(formatted_data)} entries for "
            f"{radio} saved to {len(files_created)} file(s)"
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
