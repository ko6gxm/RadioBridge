"""Lightweight data structures to replace pandas dependency.

This module provides minimal DataFrame-like functionality using only built-in Python
data structures, eliminating the heavy pandas dependency for faster startup times.
"""

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Iterator, Tuple


class LightDataFrame:
    """Lightweight DataFrame replacement using built-in data structures."""
    
    def __init__(self, data: Optional[Dict[str, List[Any]]] = None, columns: Optional[List[str]] = None):
        """Initialize with column-oriented data.
        
        Args:
            data: Dictionary mapping column names to lists of values
            columns: List of column names (optional if data provided)
        """
        if data is None:
            data = {}
            
        self._data = data
        self._columns = columns or list(data.keys())
        
        # Ensure all columns have same length
        if self._data:
            lengths = [len(values) for values in self._data.values()]
            if lengths and not all(length == lengths[0] for length in lengths):
                raise ValueError("All columns must have the same length")
            self._length = lengths[0] if lengths else 0
        else:
            self._length = 0
    
    @property
    def columns(self) -> List[str]:
        """Get column names."""
        return self._columns.copy()
    
    @property
    def empty(self) -> bool:
        """Check if DataFrame is empty."""
        return self._length == 0
    
    def __len__(self) -> int:
        """Get number of rows."""
        return self._length
    
    def __getitem__(self, column: str) -> List[Any]:
        """Get column data."""
        if column not in self._data:
            raise KeyError(f"Column '{column}' not found")
        return self._data[column].copy()
    
    def __setitem__(self, column: str, values: List[Any]):
        """Set column data."""
        if len(values) != self._length and self._length > 0:
            raise ValueError(f"Expected {self._length} values, got {len(values)}")
        
        self._data[column] = values.copy()
        if column not in self._columns:
            self._columns.append(column)
        
        if self._length == 0:
            self._length = len(values)
    
    def get(self, column: str, default: Any = None) -> List[Any]:
        """Get column data with default."""
        return self._data.get(column, [default] * self._length)
    
    def iloc(self, row_index: int) -> 'LightSeries':
        """Get row by integer position."""
        if row_index >= self._length or row_index < -self._length:
            raise IndexError(f"Row index {row_index} out of range")
        
        if row_index < 0:
            row_index = self._length + row_index
            
        row_data = {}
        for col in self._columns:
            if col in self._data:
                row_data[col] = self._data[col][row_index]
            else:
                row_data[col] = None
        
        return LightSeries(row_data)
    
    def copy(self) -> 'LightDataFrame':
        """Create a copy of the DataFrame."""
        data_copy = {col: values.copy() for col, values in self._data.items()}
        return LightDataFrame(data_copy, self._columns.copy())
    
    def to_dict(self, orient: str = 'list') -> Dict[str, Any]:
        """Convert to dictionary."""
        if orient == 'list':
            return self._data.copy()
        elif orient == 'records':
            records = []
            for i in range(self._length):
                record = {}
                for col in self._columns:
                    record[col] = self._data.get(col, [None] * self._length)[i]
                records.append(record)
            return records
        else:
            raise ValueError(f"Unsupported orient: {orient}")
    
    def apply_to_column(self, column: str, func) -> List[Any]:
        """Apply function to a column."""
        if column not in self._data:
            return [None] * self._length
        return [func(value) for value in self._data[column]]
    
    def replace_empty_strings(self, replacement: Any = None):
        """Replace empty strings with replacement value."""
        for col in self._columns:
            if col in self._data:
                self._data[col] = [replacement if value == "" else value 
                                  for value in self._data[col]]
    
    def strip_strings(self):
        """Strip whitespace from string values."""
        for col in self._columns:
            if col in self._data:
                self._data[col] = [value.strip() if isinstance(value, str) else value 
                                  for value in self._data[col]]
    
    @classmethod
    def from_records(cls, records: List[Dict[str, Any]]) -> 'LightDataFrame':
        """Create LightDataFrame from list of record dictionaries.
        
        Args:
            records: List of dictionaries, each representing a row
            
        Returns:
            LightDataFrame with the data
        """
        if not records:
            return cls()
        
        # Get all unique column names
        columns = set()
        for record in records:
            columns.update(record.keys())
        columns = sorted(list(columns))
        
        # Convert to column-oriented data
        data = {}
        for col in columns:
            data[col] = [record.get(col) for record in records]
        
        return cls(data, columns)
    
    def iterrows(self) -> Iterator[Tuple[int, 'LightSeries']]:
        """Iterate over DataFrame rows as (index, Series) pairs.
        
        Yields:
            Tuples of (index, LightSeries) for each row
        """
        for i in range(self._length):
            yield i, self.iloc(i)


class LightSeries:
    """Lightweight Series replacement for single row data."""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize with row data.
        
        Args:
            data: Dictionary mapping column names to values
        """
        self._data = data
    
    def __getitem__(self, key: str) -> Any:
        """Get value by column name."""
        return self._data[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if column exists."""
        return key in self._data
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value with default."""
        return self._data.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self._data.copy()


def is_null(value: Any) -> bool:
    """Check if value is null/missing."""
    return value is None or (isinstance(value, str) and value.strip() == "")


def read_csv_light(
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    dtype: Optional[Dict[str, type]] = None,
    comment: Optional[str] = None,
) -> LightDataFrame:
    """Read CSV file into LightDataFrame.
    
    Args:
        file_path: Path to CSV file
        encoding: File encoding
        dtype: Dictionary mapping column names to types (for compatibility)
        comment: Comment character to ignore lines (basic support)
        
    Returns:
        LightDataFrame with CSV data
    """
    data = {}
    
    with open(file_path, 'r', encoding=encoding, newline='') as file:
        # Skip comment lines if specified
        if comment:
            lines = []
            for line in file:
                if not line.strip().startswith(comment):
                    lines.append(line)
            csv_content = ''.join(lines)
            reader = csv.DictReader(csv_content.splitlines())
        else:
            reader = csv.DictReader(file)
        
        # Initialize columns
        columns = reader.fieldnames or []
        for col in columns:
            data[col] = []
        
        # Read data
        for row in reader:
            for col in columns:
                value = row.get(col, "")
                # Convert empty strings to None for consistency
                if value == "":
                    value = None
                data[col].append(value)
    
    return LightDataFrame(data, columns)


def write_csv_light(
    data: Union[LightDataFrame, Any],
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    index: bool = False,
) -> None:
    """Write LightDataFrame to CSV file.

    Args:
        data: LightDataFrame to write (or pandas DataFrame for compatibility)
        file_path: Output file path
        encoding: File encoding
        index: Whether to write index (ignored for compatibility)
    """
    # Handle pandas DataFrame compatibility
    if hasattr(data, 'to_dict') and hasattr(data, 'columns') and not isinstance(data, LightDataFrame):
        # This looks like a pandas DataFrame
        records = data.to_dict(orient='records')
        columns = list(data.columns)
        if records:
            # Convert to column-oriented data
            col_data = {}
            for col in columns:
                col_data[col] = [record.get(col) for record in records]
            data = LightDataFrame(col_data, columns)
        else:
            data = LightDataFrame()
            
    if data.empty:
        raise ValueError("Cannot write empty DataFrame to CSV")

    # Ensure directory exists
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding=encoding, newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data.columns)
        writer.writeheader()

        # Write rows
        for i in range(len(data)):
            row_dict = {}
            for col in data.columns:
                value = data._data.get(col, [None] * len(data))[i]
                # Convert None to empty string for CSV
                row_dict[col] = "" if value is None else str(value)
            writer.writerow(row_dict)
