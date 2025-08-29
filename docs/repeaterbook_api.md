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
