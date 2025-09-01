"""Radio metadata for tracking radio specifications.

This module defines the RadioMetadata dataclass for tracking radio specifications
across five key dimensions: manufacturer, model, version, firmware, and CPS.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class RadioMetadata:
    """Metadata for radio specifications across five dimensions.

    Tracks:
    1. Radio Manufacturer (e.g., "Anytone", "Baofeng")
    2. Radio Model (marketing name, e.g., "AT-D878UV II Plus")
    3. Radio Version (hardware revision or sub-model, e.g., "v1", "Plus")
    4. Firmware Version(s) (supported firmware versions, e.g., ["1.24", "1.23"])
    5. CPS Version(s) (Customer Programming Software versions, e.g., ["1.24"])
    """

    manufacturer: str
    model: str
    radio_version: str
    firmware_versions: List[str]
    cps_versions: List[str]
    formatter_key: str  # Internal registry key for backward compatibility

    def __str__(self) -> str:
        """Human-readable string representation.

        Format: "Manufacturer – Model (Version) | FW: fw1, fw2 | CPS: cps1, cps2"
        """
        fw_str = (
            ", ".join(self.firmware_versions) if self.firmware_versions else "Unknown"
        )
        cps_str = self._format_cps_display() if self.cps_versions else "Unknown"

        return (
            f"{self.manufacturer} – {self.model} ({self.radio_version}) | "
            f"FW: {fw_str} | CPS: {cps_str}"
        )

    def _format_cps_display(self) -> str:
        """Format CPS versions for display, handling ranges intelligently."""
        if not self.cps_versions:
            return "Unknown"

        display_parts = []

        for cps_version in self.cps_versions:
            # Convert underscores to spaces for display readability
            display_version = cps_version.replace("_", " ")

            if "CHIRP next" in display_version:
                # Handle CHIRP-next version ranges like "CHIRP_next_20250101_20250301"
                parts = display_version.split()
                if len(parts) >= 3:  # CHIRP next YYYYMMDD YYYYMMDD
                    name = f"{parts[0]}-{parts[1]}"  # "CHIRP-next"
                    min_ver = parts[2]  # Start date
                    display_parts.append(f"{name} {min_ver}+")
                else:
                    display_parts.append(display_version)
            else:
                # Handle CPS version ranges like "Anytone_CPS_3.00_3.08" or "DM_32UV_CPS_2.08_2.12"
                if "CPS" in display_version:
                    parts = display_version.split()

                    # Find the CPS token position
                    cps_index = -1
                    for i, part in enumerate(parts):
                        if part == "CPS":
                            cps_index = i
                            break

                    if cps_index >= 1:
                        # Reconstruct manufacturer name (everything before CPS)
                        manufacturer = " ".join(parts[:cps_index])
                        cps_label = parts[cps_index]  # "CPS"

                        # Check if we have version range (two versions after CPS)
                        if len(parts) >= cps_index + 3:
                            version_start = parts[cps_index + 1]
                            version_end = parts[cps_index + 2]
                            display_parts.append(
                                f"{manufacturer}-{cps_label} {version_start}-{version_end}"
                            )
                        elif len(parts) >= cps_index + 2:
                            # Single version after CPS
                            version = parts[cps_index + 1]
                            display_parts.append(
                                f"{manufacturer}-{cps_label} {version}"
                            )
                        else:
                            # Fallback: just replace CPS spacing
                            display_version = display_version.replace(" CPS ", "-CPS ")
                            display_parts.append(display_version)
                    else:
                        # Fallback: just replace CPS spacing
                        display_version = display_version.replace(" CPS ", "-CPS ")
                        display_parts.append(display_version)
                else:
                    display_parts.append(display_version)

        return ", ".join(display_parts)

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            f"RadioMetadata(manufacturer='{self.manufacturer}', "
            f"model='{self.model}', radio_version='{self.radio_version}', "
            f"firmware_versions={self.firmware_versions}, "
            f"cps_versions={self.cps_versions}, "
            f"formatter_key='{self.formatter_key}')"
        )

    @property
    def full_model_name(self) -> str:
        """Get the full model name including version.

        Returns:
            Combined model and version string
        """
        return f"{self.model} ({self.radio_version})"

    @property
    def latest_firmware(self) -> str:
        """Get the latest firmware version.

        Assumes firmware versions are listed with latest first.

        Returns:
            Latest firmware version string, or "Unknown" if none available
        """
        return self.firmware_versions[0] if self.firmware_versions else "Unknown"

    @property
    def latest_cps(self) -> str:
        """Get the latest CPS version.

        Assumes CPS versions are listed with latest first.

        Returns:
            Latest CPS version string, or "Unknown" if none available
        """
        return self.cps_versions[0] if self.cps_versions else "Unknown"
