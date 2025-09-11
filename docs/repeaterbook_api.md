# RepeaterBook.com API Investigation

## Base Information
- Base URL: `https://www.repeaterbook.com`
- Main search endpoint: `/repeaters/index.php`
- County search: `/repeaters/county.php`

## Current State-Level Parameters
Based on existing implementation:
- `state_id`: State/province code (e.g., 'CA', 'TX')
- `loc`: Country name (default: 'United States')
- `band`: Frequency band filter (default: 'All')
- `freq`: Specific frequency filter (default: empty)
- `band6`: Additional band filter (default: empty)
- `use`: Usage type filter (default: 'All')
- `sort`: Sort order (default: 'Distance')

## County and City Query Parameters
Based on investigation, RepeaterBook.com likely supports:

### County Searches
- URL: `/repeaters/index.php`
- Additional parameters:
  - `county` or `county_id`: County name or ID
  - Requires `state_id` and `loc` parameters as well

### City Searches
- URL: `/repeaters/index.php`
- Additional parameters:
  - `city`: City name
  - Requires `state_id` and `loc` parameters as well

## JSON Export API
- Endpoint: `/api/export.php`
- Typical parameters:
  - `state_id` (required for US): Numeric state code (e.g., CA → 06). Prefer this over two-letter `state`.
  - `country`: Country name (e.g., `United States`)
  - `county` (optional): County name
  - `city` (optional): City name
  - `band` (optional): One of `All`, `6m`, `4m`, `2m`, `440`, `900`, `1200`
    - CLI mapping: `70cm` → `440`, `33cm` → `900`, `23cm` → `1200`
    - When multiple bands (or `all`) are requested at the CLI, the API call omits `band`
      and RadioBridge applies client-side frequency filtering after fetch

### Notes on HTTP 400 errors
- Passing multiple bands like `2m,70cm` as a single `band` parameter will cause HTTP 400
- Passing two-letter `state` can result in HTTP 400; use `state_id`
- RadioBridge’s CLI now automatically uses `state_id`, maps bands, and omits `band` when needed

## CSV Export
- CSV export endpoint: `/repeaters/downloads/index.php`
- Parameters for CSV:
  - `state_id`: State code
  - `county`: County name (if filtering by county)
  - `city`: City name (if filtering by city)
  - `country`: Country name
  - `format`: "csv"

## HTML Table Structure
RepeaterBook.com uses consistent table structures across state/county/city searches:
- Tables typically have class `w3-table`
- Alternative table ID: `repeaters`
- Common columns: Frequency, Offset, Tone, Call Sign, Location, City, County, State, Use, Operational Status

## Implementation Notes
1. All county and city searches require a state context
2. HTML parsing remains consistent regardless of search level
3. CSV export may not be available for all county/city combinations
4. URL structure is consistent, only parameters change
