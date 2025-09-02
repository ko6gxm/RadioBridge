"""DEPRECATED: Pandas-based radio formatter base class.

This module has been deprecated as pandas has been removed from RadioBridge.
Please use radiobridge.radios.base instead, which provides the same interface
but uses lightweight data structures.

This module now redirects to the non-pandas version for backward compatibility.
"""

import warnings
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

# Issue deprecation warning
warnings.warn(
    "radios.base_pandas is deprecated. Use radiobridge.radios.base instead.",
    DeprecationWarning,
    stacklevel=2
)

# Redirect to the non-pandas version  
from .base import BaseRadioFormatter
from radiobridge.logging_config import get_logger
from .metadata import RadioMetadata

# All functionality is now provided by the import above
