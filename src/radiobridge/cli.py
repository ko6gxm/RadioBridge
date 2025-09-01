"""Command-line interface for radiobridge."""

import sys
from pathlib import Path
from typing import Optional

import click

from radiobridge import __version__
from radiobridge.band_filter import (
    validate_bands,
    format_band_list,
)
from radiobridge.csv_utils import (
    read_csv,
    write_csv,
    write_csv_with_comments,
    read_csv_comments,
)

# Unused imports removed for linting compliance
from radiobridge.detailed_downloader import (
    download_with_details,
    download_with_details_by_county,
    download_with_details_by_city,
)
from radiobridge.logging_config import setup_logging, get_logger
from radiobridge.radios import (
    get_supported_radios,
    get_radio_formatter,
    list_radio_options,
    resolve_by_index,
)


@click.group()
@click.version_option(version=__version__)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging output")
@click.option("--log-file", type=click.Path(), help="Write logs to specified file")
@click.pass_context
def main(ctx: click.Context, verbose: bool, log_file: Optional[str]) -> None:
    """Professional Amateur Radio Repeater Programming.

    Bridge RepeaterBook data to popular radio models with advanced features
    including county/city targeting, detailed information collection, and
    intelligent rate limiting.
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

        location_desc = location
        band_desc = format_band_list(bands)
        click.echo(
            f"RadioBridge: Successfully downloaded {len(data)} repeaters "
            f"from {location_desc} ({band_desc}) to {output}"
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
@click.option(
    "--cps",
    help="Specify the CPS (Customer Programming Software) version to optimize output for",
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
    cps: Optional[str],
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
        # Try to resolve by index first if it's a number, otherwise by name
        formatter = None
        if radio.isdigit():
            radio_index = int(radio)
            formatter = resolve_by_index(radio_index)
            if formatter is None:
                max_options = len(list_radio_options())
                click.echo(
                    f"Error: Radio index '{radio_index}' is out of range "
                    f"(1-{max_options}). Use 'rb list-radios' to see valid options.",
                    err=True,
                )
                sys.exit(1)
        else:
            formatter = get_radio_formatter(radio)
            if formatter is None:
                supported = ", ".join(get_supported_radios())
                click.echo(
                    f"Error: Unsupported radio '{radio}'. "
                    f"Supported radios: {supported}. "
                    "Use 'rb list-radios' to see all options including numbers.",
                    err=True,
                )
                sys.exit(1)

        # Validate CPS version if specified
        if cps:
            if not formatter.validate_cps_version(cps):
                supported_versions = formatter.get_supported_cps_versions()
                click.echo(
                    f"Error: CPS version '{cps}' is not supported by {formatter.radio_name}. "
                    f"Supported CPS versions: {', '.join(supported_versions)}",
                    err=True,
                )
                sys.exit(1)
            logger.info(f"Using CPS version: {cps}")

        # Format the data with start channel and CPS version
        formatted_data = formatter.format(
            data, start_channel=start_channel, cps_version=cps
        )

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
                f"RadioBridge: Successfully formatted {len(formatted_data)} "
                f"repeaters for {formatter.radio_name} to {output}"
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
@click.option(
    "-o",
    "--output",
    type=click.Choice(["default", "wide"]),
    default="default",
    help="Output format: 'default' for standard view, 'wide' for enhanced metadata",
)
def list_radios(output: str) -> None:
    """List all supported radio models with numbered options.

    Use -o wide to display enhanced metadata including form factor and band support.
    """
    options = list_radio_options()

    if not options:
        click.echo("No supported radios found.")
        return

    if output == "wide":
        _display_radios_wide(options)
    else:
        _display_radios_default(options)

    # Usage examples
    click.echo("\n" + click.style("Usage Examples:", fg="cyan", bold=True))
    click.echo(
        click.style("  By number: ", fg="white", bold=True)
        + click.style("rb format input.csv --radio 1", fg="green")
    )
    click.echo(
        click.style("  By name:   ", fg="white", bold=True)
        + click.style("rb format input.csv --radio anytone-878", fg="green")
    )

    # Additional info
    click.echo(
        "\n"
        + click.style("💡 Tip: ", fg="yellow", bold=True)
        + "Use numbers for quick selection or names for scripts"
    )
    click.echo("")


def _display_radios_default(options) -> None:
    """Display radios in default format (original layout)."""
    # Print header with styling
    click.echo(
        click.style("\nRadioBridge - Supported Radio Models", fg="cyan", bold=True)
    )
    click.echo(click.style("=" * 50, fg="cyan"))

    # Table headers with better spacing
    header = f"{'#':<3} {'Mfg':<8} {'Model':<22} {'Ver':<9} {'Firmware':<16} {'CPS'}"
    click.echo(click.style(header, fg="yellow", bold=True))
    click.echo(click.style("-" * 85, fg="yellow"))

    # Table rows
    for index, metadata in options:
        # Format firmware versions (limit to first 2 for display)
        if metadata.firmware_versions:
            fw_display = ", ".join(metadata.firmware_versions[:2])
            if len(metadata.firmware_versions) > 2:
                fw_display += "+"
        else:
            fw_display = "Unknown"

        # Format CPS versions using the metadata's display formatting
        cps_display = metadata._format_cps_display()
        # Truncate if too long for display
        if len(cps_display) > 50:
            cps_display = cps_display[:47] + "..."

        # Color coding by manufacturer
        if metadata.manufacturer == "Anytone":
            mfg_color = "green"
        elif metadata.manufacturer == "Baofeng":
            mfg_color = "blue"
        else:
            mfg_color = "white"

        # Truncate model name intelligently
        model_display = metadata.model
        if len(model_display) > 20:
            # Try to keep the important parts
            model_display = model_display[:20] + "..."
        else:
            model_display = model_display[:20]

        # Format version intelligently
        version_display = metadata.radio_version
        if version_display == "Standard":
            version_display = "Std"
        elif version_display == "Plus":
            version_display = "Plus"
        version_display = version_display[:8]

        # Create the row with proper color formatting
        parts = [
            click.style(f"{index:<3}", fg="cyan", bold=True),
            click.style(f"{metadata.manufacturer:<8}", fg=mfg_color),
            f"{model_display:<22}",
            f"{version_display:<9}",
            f"{fw_display:<16}",
            f"{cps_display}",
        ]

        click.echo(" ".join(parts))


def _display_radios_wide(options) -> None:
    """Display radios in wide format with enhanced metadata."""
    import logging
    from radiobridge.radios import get_radio_formatter

    # Temporarily suppress INFO logging to avoid cluttering output
    logger = logging.getLogger("radiobridge.radios")
    original_level = logger.level
    logger.setLevel(logging.WARNING)

    try:
        # Print header with styling
        click.echo(
            click.style(
                "\nRadioBridge - Supported Radio Models (Enhanced View)",
                fg="cyan",
                bold=True,
            )
        )
        click.echo(click.style("=" * 90, fg="cyan"))

        # Wide table headers with enhanced metadata
        header = (
            f"{'#':<3} {'Mfg':<8} {'Model':<18} {'Ver':<4} "
            f"{'Form':<9} {'Bands':<11} {'Power':<6} {'Digital':<8}"
        )
        click.echo(click.style(header, fg="yellow", bold=True))
        click.echo(click.style("-" * 90, fg="yellow"))

        # Table rows with enhanced metadata
        for index, metadata in options:
            # Get formatter to access enhanced metadata
            formatter = get_radio_formatter(metadata.formatter_key)

            # Default values in case enhanced metadata is not available
            form_factor = "Unknown"
            band_count = "Unknown"
            max_power = "?"
            digital_modes = "-"

            # Try to get enhanced metadata if available
            if formatter and hasattr(formatter, "enhanced_metadata"):
                try:
                    enhanced = formatter.enhanced_metadata[0]  # Get first variant
                    form_factor = enhanced.form_factor.value
                    band_count = enhanced.band_count.value
                    # Use g format to remove trailing .0
                    max_power = f"{enhanced.max_power_watts:g}W"
                    if enhanced.digital_modes:
                        digital_modes = ",".join(enhanced.digital_modes)
                    else:
                        digital_modes = "Analog"
                except (AttributeError, IndexError):
                    # Fall back to defaults if enhanced metadata not available
                    pass

            # Color coding by manufacturer
            if metadata.manufacturer == "Anytone":
                mfg_color = "green"
            elif metadata.manufacturer == "Baofeng":
                mfg_color = "blue"
            else:
                mfg_color = "white"

            # Truncate model name for wide display
            model_display = metadata.model[:16]
            if len(metadata.model) > 16:
                model_display = metadata.model[:14] + ".."

            # Format version short
            version_display = metadata.radio_version
            if version_display == "Standard":
                version_display = "Std"
            elif version_display == "Plus":
                version_display = "Plus"
            version_display = version_display[:4]

            # Truncate form factor and band count for display
            form_factor_display = form_factor[:8]
            if form_factor == "Handheld":
                form_factor_display = "Handheld"
            elif form_factor == "Mobile":
                form_factor_display = "Mobile"
            elif form_factor == "Base Station":
                form_factor_display = "Base"

            band_display = band_count[:10]
            if band_count == "Single Band":
                band_display = "Single"
            elif band_count == "Dual Band":
                band_display = "Dual"
            elif band_count == "Tri Band":
                band_display = "Tri"
            elif band_count == "Multi Band":
                band_display = "Multi"

            # Truncate digital modes for display
            digital_display = digital_modes[:7]
            if len(digital_modes) > 7:
                digital_display = digital_modes[:6] + "+"

            # Create the row with proper color formatting
            parts = [
                click.style(f"{index:<3}", fg="cyan", bold=True),
                click.style(f"{metadata.manufacturer:<8}", fg=mfg_color),
                f"{model_display:<18}",
                f"{version_display:<4}",
                f"{form_factor_display:<9}",
                f"{band_display:<11}",
                f"{max_power:<6}",
                f"{digital_display:<8}",
            ]

            click.echo(" ".join(parts))

        # Add legend for wide format
        click.echo("\n" + click.style("Legend:", fg="cyan", bold=True))
        click.echo(
            click.style("  Form: ", fg="white", bold=True)
            + "Handheld, Mobile, Base (station)"
        )
        click.echo(
            click.style("  Bands: ", fg="white", bold=True)
            + "Single, Dual, Tri, Multi (band support)"
        )
        click.echo(
            click.style("  Digital: ", fg="white", bold=True)
            + "DMR, D-STAR, P25 or Analog-only"
        )
    finally:
        # Restore original logging level
        logger.setLevel(original_level)


if __name__ == "__main__":
    main()
