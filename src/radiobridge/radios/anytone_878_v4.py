"""Formatter for Anytone AT-D878UV II with firmware/CPS version 4.00."""

from typing import List, Optional

from .base import BaseRadioFormatter
from ..lightweight_data import LightDataFrame
from .metadata import RadioMetadata
from .enhanced_metadata import (
    EnhancedRadioMetadata,
    FormFactor,
    BandCount,
    FrequencyRange,
    PowerLevel,
)


class Anytone878V4Formatter(BaseRadioFormatter):
    """Formatter for Anytone AT-D878UV II with firmware/CPS version 4.00.

    This formatter converts repeater data into the CSV format expected by
    the Anytone firmware and CPS version 4.00.
    """

    @property
    def radio_name(self) -> str:
        """Human-readable name of the radio."""
        return "Anytone AT-D878UV II (v4.0)"

    @property
    def description(self) -> str:
        """Description of the radio and its capabilities."""
        return "Dual-band DMR/Analog handheld with GPS and Bluetooth (FW/CPS 4.0)"

    @property
    def manufacturer(self) -> str:
        """Radio manufacturer."""
        return "Anytone"

    @property
    def model(self) -> str:
        """Radio model."""
        return "AT-D878UV II"

    @property
    def metadata(self) -> List[RadioMetadata]:
        """Radio metadata across five dimensions."""
        return [
            RadioMetadata(
                manufacturer="Anytone",
                model="AT-D878UV II Plus",
                radio_version="Plus",
                firmware_versions=["4.00"],
                cps_versions=[
                    "Anytone_CPS_4.00",
                ],
                formatter_key="anytone-878-v4",
            ),
        ]

    @property
    def enhanced_metadata(self) -> List[EnhancedRadioMetadata]:
        """Enhanced radio metadata with comprehensive specifications."""
        # Common frequency ranges for both variants
        frequency_ranges = [
            FrequencyRange(
                band_name="VHF",
                min_freq_mhz=136.0,
                max_freq_mhz=174.0,
                step_size_khz=12.5,
            ),
            FrequencyRange(
                band_name="UHF",
                min_freq_mhz=400.0,
                max_freq_mhz=520.0,
                step_size_khz=12.5,
            ),
        ]

        # Power levels for handheld radio
        power_levels = [
            PowerLevel(name="Low", power_watts=1.0, bands=["VHF", "UHF"]),
            PowerLevel(name="High", power_watts=7.0, bands=["VHF"]),
            PowerLevel(
                name="High", power_watts=6.0, bands=["UHF"]
            ),  # Slightly lower on UHF
        ]

        return [
            EnhancedRadioMetadata(
                manufacturer="Anytone",
                model="AT-D878UV II Plus",
                radio_version="Plus",
                firmware_versions=["4.00"],
                cps_versions=[
                    "Anytone_CPS_4.00",
                ],
                formatter_key="anytone-878-v4",
                # Enhanced metadata
                form_factor=FormFactor.HANDHELD,
                band_count=BandCount.DUAL_BAND,
                max_power_watts=7.0,
                frequency_ranges=frequency_ranges,
                power_levels=power_levels,
                modulation_modes=["FM", "DMR"],
                digital_modes=["DMR"],
                memory_channels=4000,
                gps_enabled=True,
                bluetooth_enabled=True,
                display_type="TFT Color LCD",
                antenna_connector="SMA-Female",
                dimensions_mm=(58, 96, 32),
                weight_grams=270,
                target_markets=["Amateur", "Commercial"],
            ),
        ]

    @property
    def required_columns(self) -> List[str]:
        """List of column names required in the input data."""
        return ["frequency"]  # Minimum required - frequency

    @property
    def output_columns(self) -> List[str]:
        """List of column names in the formatted output."""
        return [
            "Channel Number",
            "Channel Name",
            "Receive Frequency",
            "Transmit Frequency",
            "Channel Type",
            "Power",
            "Band Width",
            "CTCSS/DCS Decode",
            "CTCSS/DCS Encode",
            "Contact",
            "Contact Call Type",
            "Radio ID",
            "Busy Lock/TX Permit",
            "Squelch Mode",
            "Optional Signal",
            "DTMF ID",
            "2Tone ID",
            "5Tone ID",
            "PTT ID",
            "Color Code",
            "Slot",
            "Scan List",
            "Group List",
            "GPS System",
            "Roaming",  # New field in v4.0
            "Encryption",  # Enhanced in v4.0
        ]

    def format(
        self,
        data: LightDataFrame,
        start_channel: int = 1,
        cps_version: Optional[str] = None,
    ) -> LightDataFrame:
        """Format repeater data for Anytone 878 firmware/CPS 4.0.

        Args:
            data: Input LightDataFrame with repeater information
            start_channel: Starting channel number (default: 1)
            cps_version: CPS version to optimize output for (optional)

        Returns:
            Formatted LightDataFrame ready for Anytone firmware/CPS 4.0 import
        """
        self.validate_input(data)

        self.logger.info(f"Starting format operation for {len(data)} repeaters")
        if cps_version:
            self.logger.info(f"Optimizing output for CPS version: {cps_version}")
        self.logger.debug(f"Input columns: {list(data.columns)}")

        # CPS-specific optimizations for 4.0 version
        use_chirp_format = cps_version and "chirp" in cps_version.lower()
        if use_chirp_format:
            self.logger.debug("Using CHIRP-optimized formatting")

        formatted_data = []
        channel_names = []  # Collect names for conflict resolution

        for idx in range(len(data)):
            row = data.iloc(idx)
            channel = idx + start_channel

            # Get RX frequency (works with both basic and detailed downloader)
            rx_freq = self.clean_frequency(self.get_rx_frequency(row))
            if not rx_freq:
                self.logger.debug(f"Skipping row {idx}: no valid frequency found")
                continue

            # Get TX frequency - try detailed downloader first, then calculate from offset
            tx_freq_raw = self.get_tx_frequency(row)
            if tx_freq_raw:
                tx_freq = self.clean_frequency(tx_freq_raw)
            else:
                # Calculate TX frequency from offset (basic downloader)
                offset = self.clean_offset(self.get_offset_value(row))
                if offset and offset != "0.000000":
                    try:
                        rx_float = float(rx_freq)
                        offset_float = float(offset)
                        tx_freq = f"{rx_float + offset_float:.5f}"
                    except (ValueError, TypeError):
                        tx_freq = rx_freq
                else:
                    tx_freq = rx_freq

            # Get tone information
            tone_up, tone_down = self.get_tone_values(row)

            # Generate channel name using base class helper
            channel_name = self.build_channel_name(row, max_length=16, location_slice=8)
            if not channel_name:
                channel_name = f"CH{channel:03d}"

            channel_names.append(channel_name)

            # Determine channel type (Analog or Digital)
            channel_type = "Analog"  # Default to analog for compatibility

            # Set power level
            power = "High"  # Default to High power

            # Format for firmware/CPS 4.0 - includes new fields
            formatted_row = {
                "Channel Number": channel,
                "Channel Name": channel_name,
                "Receive Frequency": rx_freq,
                "Transmit Frequency": tx_freq,
                "Channel Type": channel_type,
                "Power": power,
                "Band Width": "25K",
                "CTCSS/DCS Decode": tone_down if tone_down else "Off",
                "CTCSS/DCS Encode": tone_up if tone_up else "Off",
                "Contact": "None",
                "Contact Call Type": "Group Call",
                "Radio ID": "None",
                "Busy Lock/TX Permit": "Always",
                "Squelch Mode": "Carrier",
                "Optional Signal": "Off",
                "DTMF ID": "None",
                "2Tone ID": "None",
                "5Tone ID": "None",
                "PTT ID": "Off",
                "Color Code": "1",
                "Slot": "1",
                "Scan List": "None",
                "Group List": "None",
                "GPS System": "GPS",
                "Roaming": "Off",  # New in v4.0
                "Encryption": "None",  # Enhanced in v4.0
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
            channel_names, max_length=16
        )

        # Update the channel names in formatted data
        for i, resolved_name in enumerate(resolved_names):
            formatted_data[i]["Channel Name"] = resolved_name

        result_df = LightDataFrame.from_records(formatted_data)
        self.logger.info(
            f"Format operation complete: {len(result_df)} channels formatted"
        )
        return result_df
