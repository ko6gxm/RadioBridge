"""Formatter for Baofeng K5 Plus handheld radio."""

from typing import List, Optional

from radiobridge.lightweight_data import LightDataFrame, LightSeries, is_null
from .base import BaseRadioFormatter
from .metadata import RadioMetadata
from .enhanced_metadata import (
    EnhancedRadioMetadata,
    FormFactor,
    BandCount,
    FrequencyRange,
    PowerLevel,
)


class BaofengK5PlusFormatter(BaseRadioFormatter):
    """Formatter for Baofeng K5 Plus handheld radio.

    This formatter converts repeater data into the CSV format expected by
    the Baofeng K5 Plus programming software.
    """

    @property
    def radio_name(self) -> str:
        """Human-readable name of the radio."""
        return "Baofeng K5 Plus"

    @property
    def description(self) -> str:
        """Description of the radio and its capabilities."""
        return "Compact tri-band analog handheld radio (VHF/UHF/220MHz)"

    @property
    def manufacturer(self) -> str:
        """Radio manufacturer."""
        return "Baofeng"

    @property
    def model(self) -> str:
        """Radio model."""
        return "K5 Plus"

    @property
    def metadata(self) -> List[RadioMetadata]:
        """Radio metadata across five dimensions."""
        return [
            RadioMetadata(
                manufacturer="Baofeng",
                model="K5 Plus",
                radio_version="Standard",
                firmware_versions=[],  # K5 Plus firmware is not upgradable
                cps_versions=[
                    "CHIRP_next_20240301_20250401",
                    "K5_CPS_2.0.3_2.1.8",
                ],
                formatter_key="baofeng-k5",
            ),
        ]

    @property
    def enhanced_metadata(self) -> List[EnhancedRadioMetadata]:
        """Enhanced radio metadata with comprehensive specifications."""
        # Frequency ranges for K5 Plus (tri-band radio)
        frequency_ranges = [
            FrequencyRange(
                band_name="VHF High",
                min_freq_mhz=136.0,
                max_freq_mhz=174.0,
                step_size_khz=12.5,
            ),  # 2m band
            FrequencyRange(
                band_name="UHF",
                min_freq_mhz=400.0,
                max_freq_mhz=520.0,
                step_size_khz=12.5,
            ),  # 70cm band
            FrequencyRange(
                band_name="220MHz",
                min_freq_mhz=200.0,
                max_freq_mhz=260.0,
                step_size_khz=12.5,
            ),  # 1.25m band
        ]

        # Power levels for tri-band handheld radio
        power_levels = [
            PowerLevel(
                name="Low", power_watts=1.0, bands=["VHF High", "UHF", "220MHz"]
            ),
            PowerLevel(
                name="High", power_watts=5.0, bands=["VHF High", "UHF", "220MHz"]
            ),
        ]

        return [
            EnhancedRadioMetadata(
                manufacturer="Baofeng",
                model="K5 Plus",
                radio_version="Standard",
                firmware_versions=[],  # K5 Plus firmware is not upgradable
                cps_versions=[
                    "CHIRP_next_20240301_20250401",
                    "K5_CPS_2.0.3_2.1.8",
                ],
                formatter_key="baofeng-k5",
                # Enhanced metadata
                form_factor=FormFactor.HANDHELD,
                band_count=BandCount.TRI_BAND,  # VHF, UHF, and 220MHz
                max_power_watts=5.0,
                frequency_ranges=frequency_ranges,
                power_levels=power_levels,
                modulation_modes=["FM"],
                digital_modes=[],  # Analog only
                memory_channels=999,
                gps_enabled=False,
                bluetooth_enabled=False,
                display_type="LCD",
                antenna_connector="SMA-Female",
                dimensions_mm=(58, 105, 30),
                weight_grams=200,
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
            "Channel",
            "Channel Name",
            "RX Frequency",
            "TX Frequency",
            "TX Power",
            "Bandwidth",
            "RX CTCSS/DCS",
            "TX CTCSS/DCS",
            "Busy Lock",
            "Scrambler",
            "Compander",
            "RX Only",
        ]

    def format(
        self,
        data: LightDataFrame,
        start_channel: int = 1,
        cps_version: Optional[str] = None,
    ) -> LightDataFrame:
        """Format repeater data for Baofeng K5 Plus.

        Args:
            data: Input LightDataFrame with repeater information
            start_channel: Starting channel number (default: 1)

        Returns:
            Formatted LightDataFrame ready for K5 Plus programming software
        """
        # Normalize input data to handle both LightDataFrame and pandas DataFrame
        data = self._normalize_input_data(data)
        self.validate_input(data)

        self.logger.info(f"Starting format operation for {len(data)} repeaters")
        if cps_version:
            self.logger.info(f"Optimizing output for CPS version: {cps_version}")
        self.logger.debug(f"Input columns: {list(data.columns)}")

        # CPS-specific optimizations
        use_chirp_format = cps_version and "chirp" in cps_version.lower()
        if use_chirp_format:
            self.logger.debug("Using CHIRP-optimized formatting")
            # CHIRP prefers simpler column names and formatting

        use_k5_cps = cps_version and "k5_cps" in cps_version.lower()
        if use_k5_cps:
            self.logger.debug("Using K5-CPS optimized formatting")

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

            # Get TX frequency - try detailed downloader first,
            # then calculate from offset
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
                        tx_freq = f"{rx_float + offset_float:.6f}"
                    except (ValueError, TypeError):
                        tx_freq = rx_freq
                else:
                    tx_freq = rx_freq

            # Get tone information (supports both new tone_up/tone_down and
            # legacy tone columns)
            tone_up, tone_down = self.get_tone_values(row)

            # Generate channel name using base class helper (CallSign-Location format)
            # K5 Plus has very limited display (12 chars max)
            channel_name = self.build_channel_name(row, max_length=12, location_slice=6)
            if not channel_name:
                channel_name = f"CH{channel:03d}"

            channel_names.append(channel_name)

            # Determine power based on frequency band
            rx_float = float(rx_freq)
            if 136.0 <= rx_float <= 174.0:  # VHF (2m)
                tx_power = "High"  # 5W on VHF
            elif 400.0 <= rx_float <= 520.0:  # UHF (70cm)
                tx_power = "High"  # 5W on UHF
            elif 200.0 <= rx_float <= 260.0:  # 220MHz (1.25m)
                tx_power = "High"  # 5W on 220MHz
            else:
                tx_power = "Low"

            formatted_row = {
                "Channel": channel,
                "Channel Name": channel_name,
                "RX Frequency": rx_freq,
                "TX Frequency": tx_freq,
                "TX Power": tx_power,
                "Bandwidth": "Wide",  # K5 Plus defaults to wide (25kHz)
                "RX CTCSS/DCS": tone_down if tone_down else "Off",
                "TX CTCSS/DCS": tone_up if tone_up else "Off",
                "Busy Lock": "Off",
                "Scrambler": "Off",
                "Compander": "Off",
                "RX Only": "Off",
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
            channel_names, max_length=12
        )

        # Update the channel names in formatted data
        for i, resolved_name in enumerate(resolved_names):
            formatted_data[i]["Channel Name"] = resolved_name

        # Convert to LightDataFrame
        output_data = {col: [] for col in self.output_columns}
        for row in formatted_data:
            for col in self.output_columns:
                output_data[col].append(row.get(col, ""))
        
        result_df = self.create_output_dataframe(output_data)
        self.logger.info(
            f"Format operation complete: {len(result_df)} channels formatted"
        )
        return result_df
