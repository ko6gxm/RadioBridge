"""Formatter for Baofeng UV-25 handheld radio."""

from typing import List, Optional

from ..lightweight_data import LightDataFrame
from .base import BaseRadioFormatter
from .metadata import RadioMetadata
from .enhanced_metadata import (
    EnhancedRadioMetadata,
    FormFactor,
    BandCount,
    FrequencyRange,
    PowerLevel,
)


class BaofengUV25Formatter(BaseRadioFormatter):
    """Formatter for Baofeng UV-25 handheld radio.

    This formatter converts repeater data into the CSV format expected by
    the Baofeng UV-25 programming software or CHIRP.

    The UV-25 is a compact tri-band handheld radio that supports VHF (136-174 MHz),
    UHF (400-520 MHz), and 220MHz (200-260 MHz) bands with analog FM operation and updated features.
    """

    @property
    def radio_name(self) -> str:
        """Human-readable name of the radio."""
        return "Baofeng UV-25"

    @property
    def description(self) -> str:
        """Description of the radio and its capabilities."""
        return "Compact tri-band handheld radio with updated features and VHF/UHF/220MHz support"

    @property
    def manufacturer(self) -> str:
        """Radio manufacturer."""
        return "Baofeng"

    @property
    def model(self) -> str:
        """Radio model."""
        return "UV-25"

    @property
    def metadata(self) -> List[RadioMetadata]:
        """Radio metadata across five dimensions."""
        return [
            RadioMetadata(
                manufacturer="Baofeng",
                model="UV-25",
                radio_version="Standard",
                firmware_versions=["UV25-V1.0", "UV25-V1.1", "UV25-V1.2"],  # Common UV-25 firmware versions
                cps_versions=[
                    "CHIRP_next_20240301_20250401",
                    "Baofeng_UV25_CPS_1.0_1.5",
                    "RT_Systems_UV25_v2.0",
                ],
                formatter_key="baofeng-uv25",
            ),
        ]

    @property
    def enhanced_metadata(self) -> List[EnhancedRadioMetadata]:
        """Enhanced radio metadata with comprehensive specifications."""
        # Frequency ranges for UV-25 (tri-band handheld radio)
        frequency_ranges = [
            FrequencyRange(
                band_name="VHF",
                min_freq_mhz=136.0,
                max_freq_mhz=174.0,
                step_size_khz=12.5,
            ),  # 2m band
            FrequencyRange(
                band_name="220MHz",
                min_freq_mhz=200.0,
                max_freq_mhz=260.0,
                step_size_khz=12.5,
            ),  # 1.25m band
            FrequencyRange(
                band_name="UHF",
                min_freq_mhz=400.0,
                max_freq_mhz=520.0,
                step_size_khz=12.5,
            ),  # 70cm band
        ]

        # Power levels for tri-band handheld radio
        power_levels = [
            PowerLevel(name="Low", power_watts=1.0, bands=["VHF", "220MHz", "UHF"]),
            PowerLevel(name="High", power_watts=8.0, bands=["VHF", "220MHz", "UHF"]),
        ]

        return [
            EnhancedRadioMetadata(
                manufacturer="Baofeng",
                model="UV-25",
                radio_version="Standard",
                firmware_versions=[],  # UV-25 firmware is not upgradable
                cps_versions=[
                    "CHIRP_next_20240301_20250401",
                    "Baofeng_UV25_CPS_1.0_1.5",
                ],
                formatter_key="baofeng-uv25",
                # Enhanced metadata
                form_factor=FormFactor.HANDHELD,
                band_count=BandCount.TRI_BAND,  # VHF, 220MHz, and UHF
                max_power_watts=8.0,
                frequency_ranges=frequency_ranges,
                power_levels=power_levels,
                modulation_modes=["FM"],
                digital_modes=[],  # Analog only
                memory_channels=999,
                gps_enabled=False,
                bluetooth_enabled=False,
                display_type="LCD",
                antenna_connector="SMA-Female",
                dimensions_mm=(58, 110, 32),
                weight_grams=220,
                target_markets=["Amateur"],
            ),
        ]

    @property
    def required_columns(self) -> List[str]:
        """List of column names required in the input data."""
        return []  # Accept both basic and detailed downloader formats

    @property
    def output_columns(self) -> List[str]:
        """List of column names in the formatted output."""
        return [
            "Location",
            "Name",
            "Frequency",
            "Duplex",
            "Offset",
            "Tone",
            "rToneFreq",
            "cToneFreq",
            "DtcsCode",
            "DtcsPolarity",
            "Mode",
            "TStep",
            "Skip",
            "Comment",
            "URCALL",
            "RPT1CALL",
            "RPT2CALL",
            "DVCODE",
        ]

    def format(
        self,
        data: LightDataFrame,
        start_channel: int = 1,
        cps_version: Optional[str] = None,
    ) -> LightDataFrame:
        """Format repeater data for Baofeng UV-25.

        Args:
            data: Input DataFrame with repeater information
            start_channel: Starting channel number (default: 1)
            cps_version: CPS version to optimize output for (optional)

        Returns:
            Formatted DataFrame ready for UV-25 programming software
        """
        self.validate_input(data)

        self.logger.info(f"Starting format operation for {len(data)} repeaters")
        if cps_version:
            self.logger.info(f"Optimizing output for CPS version: {cps_version}")
        self.logger.debug(f"Input columns: {list(data.columns)}")

        # CPS-specific optimizations
        use_chirp_format = cps_version and "chirp" in cps_version.lower()
        if use_chirp_format:
            self.logger.debug("Using CHIRP-optimized formatting")

        use_rt_systems = cps_version and "rt_systems" in cps_version.lower()
        if use_rt_systems:
            self.logger.debug("Using RT Systems-optimized formatting")

        formatted_data = []
        channel_names = []  # Collect names for conflict resolution

        for idx, row in data.iterrows():
            channel = idx + start_channel

            # Get RX frequency (works with both basic and detailed downloader)
            rx_freq = self.clean_frequency(self.get_rx_frequency(row))
            if not rx_freq:
                self.logger.debug(f"Skipping row {idx}: no valid frequency found")
                continue

            # Get TX frequency - try detailed downloader first,
            # then calculate from offset
            tx_freq_raw = self.get_tx_frequency(row)
            offset_mhz = "0.000000"
            duplex = ""

            if tx_freq_raw:
                tx_freq = self.clean_frequency(tx_freq_raw)
                # Calculate offset and duplex
                try:
                    rx_float = float(rx_freq)
                    tx_float = float(tx_freq)
                    offset_val = tx_float - rx_float

                    if abs(offset_val) < 0.001:  # Simplex
                        duplex = ""
                        offset_mhz = "0.000000"
                    elif offset_val > 0:  # Positive offset
                        duplex = "+"
                        offset_mhz = f"{offset_val:.6f}"
                    else:  # Negative offset
                        duplex = "-"
                        offset_mhz = f"{abs(offset_val):.6f}"

                except (ValueError, TypeError):
                    duplex = ""
                    offset_mhz = "0.000000"
            else:
                # Calculate TX frequency from offset (basic downloader)
                offset = self.clean_offset(self.get_offset_value(row))
                if offset and offset != "0.000000":
                    try:
                        offset_float = float(offset)
                        if abs(offset_float) >= 0.001:
                            if offset_float > 0:
                                duplex = "+"
                            else:
                                duplex = "-"
                            offset_mhz = f"{abs(offset_float):.6f}"
                        else:
                            duplex = ""
                            offset_mhz = "0.000000"
                    except (ValueError, TypeError):
                        duplex = ""
                        offset_mhz = "0.000000"
                else:
                    duplex = ""
                    offset_mhz = "0.000000"

            # Get tone information (supports both new tone_up/tone_down and
            # legacy tone columns)
            tone_up, tone_down = self.get_tone_values(row)

            # Generate channel name using base class helper
            # UV-25 has good display capabilities (8-10 chars)
            channel_name = self.build_channel_name(row, max_length=10, location_slice=5)
            if not channel_name or channel_name == "Unknown":
                channel_name = f"CH{channel:03d}"

            channel_names.append(channel_name)

            # Format tone values for UV-25 format
            tone_mode = "None"
            rtone_freq = "88.5"
            ctone_freq = "88.5"
            dtcs_code = "023"
            dtcs_pol = "NN"

            if tone_down or tone_up:
                if tone_down and tone_down.replace(".", "").isdigit():
                    # CTCSS tone
                    tone_mode = "Tone"
                    rtone_freq = tone_down
                    if tone_up and tone_up.replace(".", "").isdigit():
                        ctone_freq = tone_up
                    else:
                        ctone_freq = tone_down
                elif tone_down and tone_down.startswith("D"):
                    # DCS tone
                    tone_mode = "DTCS"
                    dtcs_code = tone_down[1:] if len(tone_down) > 1 else "023"

            # Determine frequency step based on frequency
            rx_float = float(rx_freq)
            if 136.0 <= rx_float <= 174.0:  # VHF
                tstep = "5.00"
            elif 400.0 <= rx_float <= 520.0:  # UHF
                tstep = "12.50"
            else:
                tstep = "5.00"

            formatted_row = {
                "Location": channel,
                "Name": channel_name,
                "Frequency": rx_freq,
                "Duplex": duplex,
                "Offset": offset_mhz,
                "Tone": tone_mode,
                "rToneFreq": rtone_freq,
                "cToneFreq": ctone_freq,
                "DtcsCode": dtcs_code,
                "DtcsPolarity": dtcs_pol,
                "Mode": "FM",  # UV-25 only supports FM
                "TStep": tstep,
                "Skip": "",
                "Comment": "",
                "URCALL": "",
                "RPT1CALL": "",
                "RPT2CALL": "",
                "DVCODE": "",
            }

            formatted_data.append(formatted_row)
            self.logger.debug(
                f"Formatted channel {channel}: {channel_name} @ {rx_freq}"
            )

        if not formatted_data:
            self.logger.error("No valid repeater data found after formatting")
            raise ValueError("No valid repeater data found after formatting")

        # Resolve channel name conflicts
        resolved_names = self.resolve_channel_name_conflicts(
            channel_names, max_length=10
        )

        # Update the channel names in formatted data
        for i, resolved_name in enumerate(resolved_names):
            formatted_data[i]["Name"] = resolved_name

        # Build ordered LightDataFrame matching output_columns
        ordered_cols = self.output_columns
        data_dict = {col: [] for col in ordered_cols}
        for rec in formatted_data:
            for col in ordered_cols:
                data_dict[col].append(rec.get(col))
        result_df = LightDataFrame(data_dict, ordered_cols)
        self.logger.info(
            f"Format operation complete: {len(result_df)} channels formatted"
        )
        return result_df
