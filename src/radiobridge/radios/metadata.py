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
            if (
                "CHIRP-next" in cps_version
                and "-" in cps_version
                and cps_version.count("-") >= 2
            ):
                # Handle version range like "CHIRP-next 20250101-20250301"
                parts = cps_version.split()
                if len(parts) >= 2 and "-" in parts[1]:
                    name = parts[0]
                    version_range = parts[1]
                    if "-" in version_range:
                        min_ver, max_ver = version_range.split("-", 1)
                        display_parts.append(f"{name} {min_ver}+")
                    else:
                        display_parts.append(cps_version)
                else:
                    display_parts.append(cps_version)
            else:
                display_parts.append(cps_version)

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
