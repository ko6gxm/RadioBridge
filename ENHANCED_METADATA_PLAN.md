# Enhanced Radio Metadata Enhancement Plan

## Current State Analysis

Currently, RadioBridge tracks 5 basic dimensions for each radio:
1. **Manufacturer** (e.g., "Anytone", "Baofeng")
2. **Model** (e.g., "AT-D878UV II", "UV-5R")
3. **Radio Version** (e.g., "Plus", "Standard")
4. **Firmware Versions** (e.g., ["1.24", "1.23"])
5. **CPS Versions** (e.g., ["Anytone_CPS_3.00_3.08"])

## Proposed Enhanced Metadata Structure

### 1. Physical Specifications
```python
@dataclass
class PhysicalSpecs:
    form_factor: str  # "Handheld", "Mobile", "Base Station"
    dimensions_mm: Tuple[int, int, int]  # (W, H, D) in mm
    weight_grams: int
    display_type: str  # "LCD", "OLED", "LED", "None"
    display_size: Optional[str]  # "1.77 inch", "2.4 inch"
    keypad_type: str  # "Full", "Minimal", "PTT-Only"
    antenna_connector: str  # "SMA-Female", "BNC", "N-Type"
    power_source: List[str]  # ["7.4V Li-Ion", "12V DC", "Battery Pack"]
    ingress_rating: Optional[str]  # "IP54", "IP67", etc.
```

### 2. RF Capabilities
```python
@dataclass
class RFCapabilities:
    frequency_ranges: List[FrequencyRange]
    modulation_modes: List[str]  # ["FM", "DMR", "D-STAR", "P25"]
    power_levels: List[PowerLevel]
    channel_spacing: List[float]  # [12.5, 25.0] kHz
    sensitivity: Dict[str, float]  # {"VHF": -122, "UHF": -120} dBm
    spurious_rejection: Optional[float]  # dB
    frequency_stability: Optional[float]  # ppm
    antenna_impedance: int  # 50 ohms
    max_deviation: Dict[str, float]  # {"Narrow": 2.5, "Wide": 5.0} kHz
```

```python
@dataclass
class FrequencyRange:
    band_name: str  # "VHF", "UHF", "700MHz", "800MHz"
    min_freq_mhz: float
    max_freq_mhz: float
    step_size_khz: float
    rx_only: bool = False

@dataclass
class PowerLevel:
    name: str  # "Low", "Mid", "High"
    power_watts: float
    band: str  # "VHF", "UHF", "All"
```

### 3. Digital Mode Support
```python
@dataclass
class DigitalModeSupport:
    dmr: Optional[DMRSupport] = None
    dstar: Optional[DSTARSupport] = None
    p25: Optional[P25Support] = None
    nxdn: Optional[NXDNSupport] = None

@dataclass
class DMRSupport:
    tiers_supported: List[int]  # [1, 2]
    timeslots: int  # 2
    color_codes: range  # range(0, 16)
    talk_groups: int  # Max talk groups
    contacts: int  # Max contacts
    encryption: bool = False
```

### 4. Memory & Programming
```python
@dataclass
class MemoryCapabilities:
    total_channels: int
    zones: Optional[int] = None
    channels_per_zone: Optional[int] = None
    scan_lists: Optional[int] = None
    channels_per_scan_list: Optional[int] = None
    contacts: Optional[int] = None  # For digital radios
    talk_groups: Optional[int] = None
    roaming_channels: Optional[int] = None
```

### 5. Audio & Interface Features
```python
@dataclass
class AudioInterface:
    speaker_power: Optional[float]  # Watts
    audio_bandwidth: Optional[str]  # "300-3000 Hz"
    vox_support: bool = False
    dtmf: bool = False
    two_tone: bool = False
    five_tone: bool = False
    scrambler: bool = False
    compander: bool = False
    # Connectors
    mic_connector: Optional[str]  # "RJ45", "8-pin", "6-pin"
    speaker_connector: Optional[str]
    accessory_connector: Optional[str]
    programming_connector: Optional[str]  # "USB-C", "USB-A", "Serial"
```

### 6. Advanced Features
```python
@dataclass
class AdvancedFeatures:
    gps: bool = False
    bluetooth: bool = False
    wifi: bool = False
    recording: bool = False
    emergency_features: List[str] = field(default_factory=list)
    roaming: bool = False
    dual_watch: bool = False
    cross_band_repeat: bool = False
    wide_narrow_band: bool = True
    ctcss_dcs: bool = True
    voice_prompts: bool = False
    multiple_personalities: bool = False  # Can emulate other radios
```

### 7. Certification & Compliance
```python
@dataclass
class CertificationInfo:
    fcc_id: Optional[str] = None
    ic_id: Optional[str] = None  # Industry Canada
    ce_marking: bool = False
    part_90: bool = False  # Commercial use
    part_97: bool = False  # Amateur radio
    type_accepted: bool = False
    intrinsically_safe: bool = False
    hazloc_certified: bool = False
```

### 8. Market & Support Info
```python
@dataclass
class MarketInfo:
    launch_date: Optional[date] = None
    discontinued_date: Optional[date] = None
    msrp_usd: Optional[float] = None
    target_market: List[str] = field(default_factory=list)  # ["Amateur", "Commercial", "Public Safety"]
    availability_regions: List[str] = field(default_factory=list)
    warranty_months: Optional[int] = None
    support_status: str = "Active"  # "Active", "Limited", "EOL"
```

## Enhanced RadioMetadata Class

```python
@dataclass
class EnhancedRadioMetadata:
    # Core identification (existing)
    manufacturer: str
    model: str
    radio_version: str
    firmware_versions: List[str]
    cps_versions: List[str]
    formatter_key: str

    # Enhanced metadata (new)
    physical_specs: PhysicalSpecs
    rf_capabilities: RFCapabilities
    digital_modes: DigitalModeSupport
    memory_capabilities: MemoryCapabilities
    audio_interface: AudioInterface
    advanced_features: AdvancedFeatures
    certification: CertificationInfo
    market_info: MarketInfo

    # Optional fields for backwards compatibility
    legacy_description: Optional[str] = None

    # Computed properties
    @property
    def max_frequency_mhz(self) -> float:
        return max(r.max_freq_mhz for r in self.rf_capabilities.frequency_ranges)

    @property
    def min_frequency_mhz(self) -> float:
        return min(r.min_freq_mhz for r in self.rf_capabilities.frequency_ranges)

    @property
    def supported_bands(self) -> List[str]:
        return [r.band_name for r in self.rf_capabilities.frequency_ranges]

    @property
    def is_digital(self) -> bool:
        return any([
            self.digital_modes.dmr is not None,
            self.digital_modes.dstar is not None,
            self.digital_modes.p25 is not None,
            self.digital_modes.nxdn is not None
        ])

    @property
    def max_power_watts(self) -> float:
        return max(p.power_watts for p in self.rf_capabilities.power_levels)
```

## Implementation Phases

### Phase 1: Core Structure Enhancement
- [ ] Create new enhanced metadata dataclasses
- [ ] Maintain backward compatibility with existing RadioMetadata
- [ ] Add migration utilities
- [ ] Update base formatter to support both old and new metadata

### Phase 2: Data Population
- [ ] Research and populate enhanced metadata for existing radios
- [ ] Create metadata validation system
- [ ] Add metadata completeness scoring
- [ ] Implement data sources (manufacturer specs, user contributions)

### Phase 3: CLI & Display Enhancements
- [ ] Enhanced `list-radios` command with filtering
- [ ] Radio comparison features
- [ ] Detailed radio information display
- [ ] Export capabilities (JSON, CSV, markdown)

### Phase 4: API & Integration
- [ ] REST API endpoints for radio metadata
- [ ] Integration with external radio databases
- [ ] Metadata synchronization system
- [ ] Community contribution system

### Phase 5: Advanced Features
- [ ] Compatibility matrix between radios
- [ ] Programming software compatibility checking
- [ ] Feature-based radio recommendations
- [ ] Historical tracking of firmware/CPS updates

## Data Sources for Population

1. **Manufacturer Specifications**
   - Official datasheets and manuals
   - CPS software requirements
   - Firmware release notes

2. **Regulatory Databases**
   - FCC Equipment Authorization database
   - Industry Canada database
   - European conformity databases

3. **Community Sources**
   - RadioLabs.com
   - Amateur radio communities
   - User manuals and reviews
   - Programming software documentation

4. **Third-party Databases**
   - CHIRP radio database
   - RT Systems compatibility lists
   - Vendor compatibility matrices

## Benefits of Enhanced Metadata

1. **Better User Experience**
   - Smart radio recommendations based on requirements
   - Compatibility warnings and suggestions
   - Feature-based filtering and search

2. **Improved Software Quality**
   - Better testing coverage with known limitations
   - CPS-specific optimizations
   - Format validation against radio capabilities

3. **Community Value**
   - Centralized, accurate radio information
   - Historical tracking of radio evolution
   - Platform for sharing radio knowledge

4. **Commercial Opportunities**
   - API licensing for radio databases
   - Integration with equipment vendors
   - Enhanced support for commercial users

This enhanced metadata system will position RadioBridge as the definitive source for radio programming compatibility information.
