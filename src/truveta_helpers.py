"""Shared helper functions used across the study notebooks.

The notebooks in ``notebooks/`` are deliberately **self-contained**: each one
re-defines the helpers it needs so that a single ``.ipynb`` can be uploaded to
the Truveta Studio workspace and executed without any other file present.

This module is the single readable reference copy of those helpers.  If your
Truveta workspace lets you upload plain ``.py`` files alongside notebooks you
can ``import truveta_helpers`` instead of using the inline copies -- but if you
edit a function here, mirror the change in the notebooks (and vice versa).

None of this code runs outside the Truveta Studio environment: it depends on
``truveta.study``, an active Spark session (``spark``) and ``pyspark.pandas``.
"""

from typing import overload

import numpy as np
import pandas as pd
import pyspark.pandas as ps
from pyspark.sql import DataFrame


# ---------------------------------------------------------------------------
# Concept decoding
# ---------------------------------------------------------------------------

@overload
def decode_concepts(df: pd.DataFrame, drop_concepts: bool = True,
                    columns: list[str] | None = None) -> pd.DataFrame: ...
@overload
def decode_concepts(df: ps.DataFrame, drop_concepts: bool = True,
                    columns: list[str] | None = None) -> ps.DataFrame: ...
@overload
def decode_concepts(df: DataFrame, drop_concepts: bool = True,
                    columns: list[str] | None = None) -> DataFrame: ...
def decode_concepts(df, drop_concepts: bool = True, columns: list[str] | None = None):
    """Replace ``*ConceptId`` columns with their human-readable concept names.

    Every integer/float column whose name ends in ``ConceptId`` is joined
    against the ``Concept`` table and replaced by a column with the
    ``ConceptId`` suffix stripped.

    Parameters
    ----------
    df
        pandas, pandas-on-Spark or Spark DataFrame.
    drop_concepts
        Drop the original ``*ConceptId`` columns (default ``True``).
    columns
        Decode exactly these columns instead of auto-detecting.

    Returns
    -------
    The same DataFrame type that was passed in, with decoded columns.
    """
    def should_decode(col: str, dtype: str) -> bool:
        if columns:
            return col in columns
        return col.endswith("ConceptId") and str(dtype) in (
            "int", "int32", "float64", "float32")

    column_names = set(df.columns)

    def target_col(col: str) -> str:
        name = col.removesuffix("ConceptId")
        if name == col and drop_concepts:
            return name
        while name in column_names:
            name = f"{name}Name"
        return name

    def safe_name(name: str) -> str:
        while name in column_names:
            name = f"{name}_tmp"
        return name

    final_order: list[str] = []

    # --- pandas -----------------------------------------------------------
    if isinstance(df, pd.DataFrame):
        lookup = None
        for col, dtype in zip(df.columns, df.dtypes):
            if should_decode(col, str(dtype)):
                name = target_col(col)
                column_names.add(name)
                if lookup is None:  # lazy: only pay for the lookup if needed
                    lookup = (spark.sql("SELECT ConceptId, ConceptName FROM Concept")
                              .toPandas().set_index("ConceptId").ConceptName)
                df[name] = df[col].map(lookup)
                if drop_concepts and name != col:
                    df = df.drop(columns=[col])
                else:
                    final_order.append(col)
                final_order.append(name)
            else:
                final_order.append(col)
        return df[final_order]

    # --- pandas-on-Spark / Spark -----------------------------------------
    return_pandas = False
    if isinstance(df, ps.DataFrame):
        return_pandas = True
        df = df.to_spark()

    concepts_s = spark.sql("SELECT ConceptId, ConceptName FROM Concept").cache()
    for col, dtype in df.dtypes:
        if should_decode(col, str(dtype)):
            name = target_col(col)
            column_names.add(name)
            if col == name and drop_concepts:
                tmp_name = safe_name(col)
                df = (df.withColumnRenamed(col, tmp_name)
                        .join(concepts_s.withColumnRenamed("ConceptId", tmp_name)
                                        .withColumnRenamed("ConceptName", name),
                              on=tmp_name, how="left")
                        .drop(tmp_name))
            else:
                df = df.join(concepts_s.withColumnRenamed("ConceptId", col)
                                       .withColumnRenamed("ConceptName", name),
                             on=col, how="left")
                if drop_concepts:
                    df = df.drop(col)
                else:
                    final_order.append(col)
            final_order.append(name)
        else:
            final_order.append(col)
    df = df.select(final_order)
    return df.pandas_api() if return_pandas else df


def match_code(df, codes_df):
    """Decode concept ids on ``df`` and keep only rows whose ``Code`` is in the code set."""
    code_name = decode_concepts(df)
    case_names = codes_df.ConceptName.to_pandas().tolist()
    return code_name[code_name["Code"].isin(case_names)]


def load_condition_data(snapshot, codeset_url=None, code_set=None, codes="codes",
                        table_name="Condition", view_name="tbl_index_condition",
                        concept_map_table="ConditionCodeConceptMap",
                        concept_map_key="CodeConceptMapId", verbose=True):
    """Load one clinical table filtered to a code set and decode it to code names.

    Parameters
    ----------
    snapshot
        Truveta population snapshot.
    codeset_url
        Definition URL (``"/definitions/..."`` or a full library URL).  Used when
        ``code_set`` is not supplied.
    code_set
        An already-built code set, e.g. ``snapshot.codeset("ICD10CM", ...)``.
    codes
        Variable name to pull out of the prose definition (default ``"codes"``).
    table_name
        ``"Condition"`` or ``"Procedure"``.
    view_name
        Name of the temporary Spark view to materialise.
    concept_map_table, concept_map_key
        Concept-map table and join key for ``table_name``.

    Returns
    -------
    (matched_df, unique_person_count)
    """
    if code_set is None:
        if codeset_url is None:
            raise ValueError("Must provide either `codeset_url` or `code_set`")
        code_set = snapshot.codeset_from_prose(url=codeset_url, variable_name=codes)

    index_table = snapshot.load_filtered_table(table_name, code_set, view_name=view_name)
    if verbose:
        print(f"[{table_name}] Unique PersonId (after code filter):",
              index_table["PersonId"].nunique())

    df = ps.sql(f"""
        SELECT m.PersonId, m.RecordedDateTime, pm.*
        FROM {view_name} m
        JOIN {concept_map_table} pm ON m.{concept_map_key} = pm.Id
    """).to_pandas()

    matched_df = match_code(df, code_set)
    if verbose:
        print("Total matched rows:", len(matched_df))
        print("Unique PersonId (after match):", matched_df["PersonId"].nunique())

    return matched_df, matched_df["PersonId"].nunique()


# ---------------------------------------------------------------------------
# Condition timing flags
# ---------------------------------------------------------------------------

def mark_condition_in_pregnancy(condition_df, delivery_df, col_name):
    """Flag people whose condition was recorded between ``estimated_LMP`` and delivery.

    ``delivery_df`` must contain ``PersonId``, ``estimated_LMP`` and
    ``delivery_date``.  Returns ``delivery_df`` with a new boolean ``col_name``
    (``False`` where no qualifying record exists).
    """
    merged = condition_df.merge(
        delivery_df[["PersonId", "estimated_LMP", "delivery_date"]],
        on="PersonId", how="left")

    merged["in_pregnancy"] = (
        (merged["RecordedDateTime"] >= merged["estimated_LMP"]) &
        (merged["RecordedDateTime"] <= merged["delivery_date"])
    )

    flagged_ids = merged.loc[merged["in_pregnancy"], "PersonId"].drop_duplicates()
    condition_flag = pd.DataFrame({"PersonId": flagged_ids, col_name: True})

    delivery_df = delivery_df.merge(condition_flag, on="PersonId", how="left")
    delivery_df[col_name] = delivery_df[col_name].fillna(False)
    return delivery_df


def condition_before_pregnancy(condition_df, delivery_df, condition_col_name):
    """Flag people with a condition recorded strictly before ``estimated_LMP``."""
    merged = condition_df.merge(
        delivery_df[["PersonId", "estimated_LMP"]], on="PersonId", how="left")

    merged["pre_pregnancy"] = merged["RecordedDateTime"] < merged["estimated_LMP"]

    before_preg = merged[merged["pre_pregnancy"]].drop_duplicates(subset="PersonId")
    delivery_df[condition_col_name] = delivery_df["PersonId"].isin(
        before_preg["PersonId"].unique())
    return delivery_df


# ---------------------------------------------------------------------------
# Demographics
# ---------------------------------------------------------------------------

def calculate_age(event_date, dob):
    """Age in years between a date of birth and an event date."""
    return (event_date - dob).days / 365.25


def combine_race_ethnicity(row):
    """Collapse Truveta ``Race`` + ``Ethnicity`` into a single analysis variable."""
    race = str(row["Race"]).strip().lower()
    ethnicity = str(row["Ethnicity"]).strip().lower()

    if pd.isna(race) or pd.isna(ethnicity):
        return "Unknown"

    if ethnicity == "hispanic or latino":
        return "Hispanic"

    if ethnicity == "not hispanic or latino":
        if race == "white":
            return "Non-Hispanic White"
        if race == "black or african american":
            return "Non-Hispanic Black"
        if race in ("asian", "american indian or alaska native",
                    "native hawaiian or other pacific islander", "other race"):
            return "Other"
        return "Unknown"

    return "Unknown"


def reclassify_income(bracket):
    """Collapse the SDOH annual-income bracket string into three analysis bands."""
    try:
        low = int(str(bracket).split("-")[0].replace(",", "").strip())
    except (ValueError, AttributeError):
        return "Unknown"
    if low <= 50000:
        return "≤50000"
    if low <= 80000:
        return "50001-80000"
    return ">80000"


# ---------------------------------------------------------------------------
# Gestational weight gain (IOM / NASEM 2009 recommendations)
# ---------------------------------------------------------------------------

def bmi_category(bmi):
    """WHO pre-pregnancy BMI category."""
    if pd.isna(bmi):
        return np.nan
    if bmi < 18.5:
        return "Underweight"
    if bmi < 25.0:
        return "Normal weight"
    if bmi < 30.0:
        return "Overweight"
    return "Obese"


def gwg_bounds(bmi, weeks):
    """Recommended (low, high) total gestational weight gain in kg.

    Uses the IOM/NASEM 2009 first-trimester allowance (0.5-2.0 kg) plus the
    BMI-specific weekly rate applied from week 13 onwards.
    """
    if pd.isna(bmi) or pd.isna(weeks):
        return (np.nan, np.nan)

    delta_weeks = max(weeks - 13, 0)  # no weekly accrual before week 13

    if bmi < 18.5:                    # Underweight
        low, high = 0.5 + 0.44 * delta_weeks, 2.0 + 0.58 * delta_weeks
    elif bmi < 25.0:                  # Normal weight
        low, high = 0.5 + 0.35 * delta_weeks, 2.0 + 0.50 * delta_weeks
    elif bmi < 30.0:                  # Overweight
        low, high = 0.5 + 0.23 * delta_weeks, 2.0 + 0.33 * delta_weeks
    else:                             # Obese
        low, high = 0.5 + 0.17 * delta_weeks, 2.0 + 0.27 * delta_weeks

    return (low, high)


def categorize_gwg(gwg, low, high):
    """Classify observed gestational weight gain against the recommended band."""
    if pd.isna(gwg) or pd.isna(low) or pd.isna(high):
        return np.nan
    if gwg < low:
        return "Inadequate"
    if gwg <= high:
        return "Adequate"
    return "Excessive"


def add_gwg_category(df, bmi_col="PrePregnancyBMI", weeks_col="gestational_week",
                     gwg_col="gestation_weight"):
    """Add ``bmi_category``, ``gwg_low_bound``, ``gwg_high_bound`` and ``gwg_category``."""
    df = df.copy()
    df["bmi_category"] = df[bmi_col].apply(bmi_category)

    bounds = df.apply(lambda row: gwg_bounds(row[bmi_col], row[weeks_col]), axis=1)
    df[["gwg_low_bound", "gwg_high_bound"]] = pd.DataFrame(
        bounds.tolist(), index=df.index)

    df["gwg_category"] = df.apply(
        lambda row: categorize_gwg(row[gwg_col],
                                   row["gwg_low_bound"],
                                   row["gwg_high_bound"]), axis=1)
    df["gwg_category"] = pd.Categorical(
        df["gwg_category"],
        categories=["Inadequate", "Adequate", "Excessive"], ordered=True)
    return df
