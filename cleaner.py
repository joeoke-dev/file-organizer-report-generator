"""Clean a messy sales CSV with pandas.

clean_sales() takes the raw DataFrame and returns (clean_df, summary), where
summary counts exactly what was fixed or removed, so the cleaning is auditable.
"""

import re

import pandas as pd

REQUIRED_COLUMNS = [
    "order_id", "date", "customer", "region",
    "product_category", "quantity", "unit_price",
]
TEXT_COLUMNS = ["customer", "region", "product_category"]
MISSING_MARKERS = {"", "n/a", "na", "none", "null", "nan", "-", "?"}


def standardize_columns(df):
    """' Order ID ' -> 'order_id'"""
    df = df.copy()
    df.columns = [re.sub(r"[^0-9a-z]+", "_", str(c).strip().lower()).strip("_") for c in df.columns]
    return df


def _mark_missing(series):
    """Turn placeholders like 'N/A' or '-' into real missing values."""
    s = series.astype("string").str.strip()
    return s.mask(s.str.lower().isin(MISSING_MARKERS))


def _clean_text(series):
    """Trim, collapse repeated spaces, and use Title Case."""
    s = _mark_missing(series).str.replace(r"\s+", " ", regex=True)
    return s.str.title()


def _to_number(series):
    """'$1,200.50' -> 1200.5; anything unreadable becomes NaN."""
    s = series.astype("string").str.replace(r"[^0-9.\-]", "", regex=True)
    return pd.to_numeric(s, errors="coerce")


def _to_date(series):
    """Parse mixed date formats; unreadable dates become NaT.

    Each format is tried explicitly, so the result doesn't depend on the pandas
    version: ISO dates (2024-05-02), day/month/year (02/05/2024), then month
    names (May 02, 2024).
    """
    s = _mark_missing(series)
    iso = pd.to_datetime(s, format="ISO8601", errors="coerce")
    day_first = pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
    month_names = pd.to_datetime(s, format="mixed", errors="coerce")
    return iso.fillna(day_first).fillna(month_names)


def clean_sales(raw):
    df = standardize_columns(raw)
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    df = df[REQUIRED_COLUMNS].copy()

    summary = {"rows_in": len(df)}

    # 1. Standardize text (and count how many values actually changed)
    changed = 0
    for col in TEXT_COLUMNS:
        before = df[col].astype("string")
        cleaned = _clean_text(df[col])
        changed += int(((before != cleaned) & cleaned.notna()).sum())
        df[col] = cleaned
    summary["text_values_standardized"] = changed

    # 2. Convert types
    df["order_id"] = _mark_missing(df["order_id"]).str.upper()
    df["date"] = _to_date(df["date"])
    df["quantity"] = _to_number(df["quantity"])
    df["unit_price"] = _to_number(df["unit_price"])

    # 3. Remove duplicates (after standardizing, so near-duplicates are caught)
    n = len(df)
    df = df.drop_duplicates()
    summary["exact_duplicates_removed"] = n - len(df)

    n = len(df)
    df = df[df["order_id"].isna() | ~df["order_id"].duplicated()]
    summary["duplicate_order_ids_removed"] = n - len(df)

    # 4. Remove rows we can't analyze
    def drop_where(mask, key):
        nonlocal df
        summary[key] = int(mask.sum())
        df = df[~mask]

    drop_where(df["order_id"].isna(), "dropped_missing_order_id")
    drop_where(df["date"].isna(), "dropped_missing_or_invalid_date")
    drop_where(df["quantity"].isna() | df["unit_price"].isna(), "dropped_missing_quantity_or_price")
    drop_where((df["quantity"] <= 0) | (df["unit_price"] <= 0), "dropped_non_positive_values")

    # 5. Fill gaps in descriptive columns
    summary["missing_text_filled_unknown"] = int(df[TEXT_COLUMNS].isna().sum().sum())
    df[TEXT_COLUMNS] = df[TEXT_COLUMNS].fillna("Unknown")

    # 6. Final types and a total column
    df["quantity"] = df["quantity"].round().astype("int64")
    df["unit_price"] = df["unit_price"].astype("float64").round(2)
    df["total"] = (df["quantity"] * df["unit_price"]).round(2)
    for col in ["order_id"] + TEXT_COLUMNS:
        df[col] = df[col].astype("object")

    df = df.sort_values("date").reset_index(drop=True)
    summary["rows_out"] = len(df)
    return df, summary
