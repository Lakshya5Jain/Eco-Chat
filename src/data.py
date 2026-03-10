"""Data layer — FRED API integration for economic data fetching."""

import os
from datetime import datetime, timedelta

import pandas as pd
from fredapi import Fred

from dotenv import load_dotenv

load_dotenv(override=True)

_fred: Fred | None = None

# Streamlit caching (graceful fallback if streamlit is not available)
try:
    import streamlit as st
    _cache_data = st.cache_data(ttl=300)
except Exception:
    def _cache_data(fn):
        return fn


def _get_fred() -> Fred:
    """Lazy-init the FRED client."""
    global _fred
    if _fred is None:
        api_key = os.getenv("FRED_API_KEY")
        if not api_key:
            raise RuntimeError("FRED_API_KEY is not set in .env")
        _fred = Fred(api_key=api_key)
    return _fred


def _parse_date(value: str | None) -> datetime | None:
    """Safely parse an ISO date string, returning None on failure."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Common FRED series lookup — helps the LLM pick the right series_id
# ---------------------------------------------------------------------------
COMMON_SERIES = {
    "gdp": ("GDP", "Gross Domestic Product"),
    "real gdp": ("GDPC1", "Real Gross Domestic Product"),
    "inflation": ("CPIAUCSL", "Consumer Price Index for All Urban Consumers"),
    "cpi": ("CPIAUCSL", "Consumer Price Index for All Urban Consumers"),
    "unemployment": ("UNRATE", "Unemployment Rate"),
    "unemployment rate": ("UNRATE", "Unemployment Rate"),
    "interest rate": ("FEDFUNDS", "Federal Funds Effective Rate"),
    "federal funds rate": ("FEDFUNDS", "Federal Funds Effective Rate"),
    "fed funds": ("FEDFUNDS", "Federal Funds Effective Rate"),
    "10 year treasury": ("DGS10", "10-Year Treasury Constant Maturity Rate"),
    "treasury yield": ("DGS10", "10-Year Treasury Constant Maturity Rate"),
    "sp500": ("SP500", "S&P 500"),
    "s&p 500": ("SP500", "S&P 500"),
    "housing starts": ("HOUST", "Housing Starts: Total"),
    "retail sales": ("RSXFS", "Advance Retail Sales: Retail and Food Services"),
    "industrial production": ("INDPRO", "Industrial Production Index"),
    "pce": ("PCE", "Personal Consumption Expenditures"),
    "core pce": ("PCEPILFE", "PCE Excluding Food and Energy (Core PCE)"),
    "consumer sentiment": ("UMCSENT", "University of Michigan Consumer Sentiment"),
    "nonfarm payrolls": ("PAYEMS", "All Employees, Total Nonfarm"),
    "jobs": ("PAYEMS", "All Employees, Total Nonfarm"),
    "m2 money supply": ("M2SL", "M2 Money Stock"),
    "trade balance": ("BOPGSTB", "Trade Balance: Goods and Services"),
    "wage growth": ("CES0500000003", "Average Hourly Earnings of All Employees"),
}


@_cache_data
def search_fred_series(query: str, limit: int = 10) -> str:
    """Search FRED for series matching a query string.

    Returns a formatted string of matching series with their IDs and titles.
    """
    try:
        # First check our common lookup
        key = query.lower().strip()
        if key in COMMON_SERIES:
            series_id, title = COMMON_SERIES[key]
            return f"Best match: {series_id} — {title}\n(This is a commonly requested series.)"

        results = _get_fred().search(query)
        if results.empty:
            return f"No FRED series found for '{query}'. Try a different search term."

        # Sort by popularity (higher is better)
        results = results.sort_values("popularity", ascending=False).head(limit)
        lines = []
        for series_id, row in results.iterrows():
            title = row.get("title", "N/A")
            freq = row.get("frequency_short", "?")
            lines.append(f"• {series_id}: {title} (frequency: {freq})")

        return f"Top results for '{query}':\n" + "\n".join(lines)
    except Exception as e:
        return f"Error searching FRED: {e}"


@_cache_data
def fetch_fred_data(
    series_id: str,
    start_date: str | None = None,
    end_date: str | None = None,
    years_back: int | None = None,
) -> tuple[pd.DataFrame, dict]:
    """Fetch a FRED series and return (DataFrame, metadata).

    Parameters
    ----------
    series_id : str
        FRED series identifier (e.g., "CPIAUCSL").
    start_date : str, optional
        ISO date string "YYYY-MM-DD". Overrides *years_back*.
    end_date : str, optional
        ISO date string "YYYY-MM-DD". Defaults to today.
    years_back : int, optional
        Convenience param — fetch data from N years ago to today.

    Returns
    -------
    (df, meta) where *df* has columns ["date", "value"] and *meta* is a dict
    with series_id, title, units, and frequency.
    """
    fred = _get_fred()

    # Validate years_back
    if years_back is not None and (not isinstance(years_back, int) or years_back <= 0):
        years_back = 5

    # Resolve dates with safe parsing
    end = _parse_date(end_date) or datetime.today()
    start_parsed = _parse_date(start_date)
    if start_parsed:
        start = start_parsed
    elif years_back:
        start = end - timedelta(days=365 * years_back)
    else:
        start = end - timedelta(days=365 * 5)  # default 5 years

    try:
        info = fred.get_series_info(series_id)
        meta = {
            "series_id": series_id,
            "title": info.get("title", series_id),
            "units": info.get("units", ""),
            "frequency": info.get("frequency", ""),
        }
    except Exception:
        meta = {
            "series_id": series_id,
            "title": series_id,
            "units": "",
            "frequency": "",
        }

    try:
        series = fred.get_series(series_id, observation_start=start, observation_end=end)
    except ValueError as e:
        raise ValueError(f"Bad series ID '{series_id}': {e}") from e
    except Exception as e:
        raise RuntimeError(f"FRED API error for '{series_id}': {e}") from e

    if series is None or series.empty:
        raise ValueError(
            f"No data returned for series '{series_id}' in the requested date range."
        )

    df = series.dropna().reset_index()
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])

    return df, meta


def fetch_multiple_series(
    series_ids: list[str],
    start_date: str | None = None,
    end_date: str | None = None,
    years_back: int | None = None,
) -> tuple[pd.DataFrame, list[dict]]:
    """Fetch multiple FRED series and merge them into one wide DataFrame.

    Returns (df, list_of_meta).  The DataFrame has a 'date' column plus one
    column per series (named by series_id).
    """
    merged: pd.DataFrame | None = None
    all_meta: list[dict] = []

    for sid in series_ids:
        df, meta = fetch_fred_data(
            sid, start_date=start_date, end_date=end_date, years_back=years_back
        )
        all_meta.append(meta)
        df = df.rename(columns={"value": sid})
        if merged is None:
            merged = df
        else:
            merged = pd.merge(merged, df, on="date", how="outer")

    if merged is not None:
        merged = merged.sort_values("date").reset_index(drop=True)

    return merged, all_meta


def resolve_series_id(user_query: str) -> str | None:
    """Try to resolve a plain-English concept to a FRED series ID."""
    key = user_query.lower().strip()
    if key in COMMON_SERIES:
        return COMMON_SERIES[key][0]
    return None
