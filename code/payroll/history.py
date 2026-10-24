"""
history.py — Step 1 of the pipeline: a quarter of exports into one clean table.

Twelve weekly files become one DataFrame, and its text becomes numbers and dates.
Two lessons meet here:

- **Vectorized string methods (`.str`)** — `series.str.strip()` strips *every*
  value in the column at once. No `apply`, no loop: the method runs down the
  whole Series and hands back a new one.
- **Dates (`pd.to_datetime`, `.dt`)** — text like `"8/14/2026"` becomes a real
  date that knows its month, sorts correctly, and compares with `<` and `>`.

Assignment 04's lineage rule still holds for every function that returns a
row-level table:

    A pipeline step returns a WIDER copy of the frame it was given. It never
    changes a value it was handed, never removes or renames a column, and never
    modifies the caller's frame.

So the raw `" e004"` stays in `employeeid`, and `"E004"` goes in a new
`employee_id` column beside it.

The first three functions here take a **Series and return a Series** — one whole
column in, one whole column out, same length, same order. They are the `.str`
and `.dt` versions of Assignment 04's element functions.

This step is walked through line by line. The next two steps give you less.
"""

import pandas as pd


def clean_employee_id(ids: pd.Series) -> pd.Series:
    """Normalize hand-typed employee IDs to the roster's "E004" form."""
    digits = ids.str.strip().str.upper().str[1:].str.zfill(3)
    return "E" + digits


def clean_number(values: pd.Series) -> pd.Series:
    """Read money or hours written as text; return floats. Unreadable -> 0.0."""
    cleaned = (
        values.str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce").fillna(0.0)


def parse_pay_date(values: pd.Series) -> pd.Series:
    """Parse US or ISO pay dates into datetimes. Unreadable -> NaT."""
    us = pd.to_datetime(values, format="%m/%d/%Y", errors="coerce")
    iso = pd.to_datetime(values, format="%Y-%m-%d", errors="coerce")
    return us.fillna(iso)


def combine_exports(exports: list) -> pd.DataFrame:
    """Stack weekly exports into one DataFrame with a fresh index."""
    return pd.concat(exports, ignore_index=True)


def add_clean_columns(history: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of the history with five clean columns added."""
    out = history.copy()
    out["employee_id"] = clean_employee_id(out["employeeid"])
    out["pay_date"] = parse_pay_date(out["payrolldate"])
    out["hours_worked"] = clean_number(out["hours"])
    out["rate_usd"] = clean_number(out["rate"])
    out["gross_pay"] = clean_number(out["total"])
    return out


def add_date_parts(history: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with week_ending and month text columns from pay_date."""
    out = history.copy()
    out["week_ending"] = out["pay_date"].dt.strftime("%Y-%m-%d")
    out["month"] = out["pay_date"].dt.strftime("%Y-%m")
    return out
