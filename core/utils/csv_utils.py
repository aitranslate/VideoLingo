"""
CSV utility functions for safe reading/writing with encoding handling.
Supports multiple encodings for Excel compatibility.
"""
import os
import pandas as pd
from typing import Optional, List


# Encodings to try, in order of preference
# Excel on Windows often saves as GBK/GB2312, while Unix systems use UTF-8
_READ_ENCODINGS = ['utf-8-sig', 'gbk', 'gb2312', 'utf-8']
_WRITE_ENCODING = 'utf-8-sig'  # Always write with BOM for Excel compatibility


def safe_read_csv(filepath: str, **kwargs) -> pd.DataFrame:
    """
    Safely read CSV file with multiple encoding attempts.

    Tries multiple encodings to handle files saved by different systems:
    - utf-8-sig: Standard UTF-8 with BOM (preferred)
    - gbk: Excel Windows Chinese default
    - gb2312: Simplified Chinese
    - utf-8: Standard UTF-8

    Args:
        filepath: Path to CSV file
        **kwargs: Additional arguments passed to pd.read_csv

    Returns:
        DataFrame with CSV data, or empty DataFrame if file doesn't exist
                  or all encodings fail

    Examples:
        >>> df = safe_read_csv('data.csv')
        >>> df = safe_read_csv('data.csv', usecols=['A', 'B'])
    """
    if not os.path.exists(filepath):
        return pd.DataFrame()

    for encoding in _READ_ENCODINGS:
        try:
            return pd.read_csv(filepath, encoding=encoding, **kwargs)
        except (UnicodeDecodeError, UnicodeError):
            continue

    # All encodings failed, return empty DataFrame
    return pd.DataFrame()


def safe_write_csv(df: pd.DataFrame, filepath: str, **kwargs) -> None:
    """
    Write DataFrame to CSV with UTF-8-sig encoding for Excel compatibility.

    Always uses utf-8-sig encoding to ensure Excel can open the file
    without encoding issues.

    Args:
        df: DataFrame to write
        filepath: Path to output CSV file
        **kwargs: Additional arguments passed to df.to_csv

    Examples:
        >>> safe_write_csv(df, 'output.csv')
        >>> safe_write_csv(df, 'output.csv', index=False)
    """
    # Set default encoding, but allow override
    kwargs.setdefault('encoding', _WRITE_ENCODING)
    df.to_csv(filepath, **kwargs)


def read_csv_with_columns(
    filepath: str,
    required_columns: List[str],
    **kwargs
) -> pd.DataFrame:
    """
    Read CSV and validate required columns exist.

    Args:
        filepath: Path to CSV file
        required_columns: List of required column names
        **kwargs: Additional arguments passed to safe_read_csv

    Returns:
        DataFrame with CSV data

    Raises:
        ValueError: If required columns are missing

    Examples:
        >>> df = read_csv_with_columns(
        ...     'data.csv',
        ...     required_columns=['Source', 'Trans', 'Note']
        ... )
    """
    df = safe_read_csv(filepath, **kwargs)

    if not df.empty:
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(
                f"CSV file '{filepath}' is missing required columns: {missing}. "
                f"Expected: {required_columns}, Found: {list(df.columns)}"
            )

    return df
