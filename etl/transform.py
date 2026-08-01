import pandas as pd
from pydantic import TypeAdapter

from etl.models import DailyObservation

CORE_ELEMENTS = ['TMAX', 'TMIN', 'PRCP', 'SNOW', 'SNWD']
MAX_ELEMENTS = {'TMAX', 'PRCP', 'SNOW', 'SNWD'}
MIN_ELEMENTS = {'TMIN'}

observation_list = TypeAdapter(list[DailyObservation])


def filter_quality_observations(dly):
    """Keep only the 5 core elements that passed quality control (qflag is blank)."""
    return dly[
        dly['element'].isin(CORE_ELEMENTS)
        & dly['qflag'].isna()
    ]


def combine_duplicate_observations(dly):
    """When a station reports more than one value for the same element on the
    same day, keep the most extreme reading -- the highest for TMAX/PRCP/SNOW/SNWD,
    the lowest for TMIN -- instead of crashing (pivot) or averaging them away.
    """
    take_max = dly[dly['element'].isin(MAX_ELEMENTS)]
    take_min = dly[dly['element'].isin(MIN_ELEMENTS)]

    combined_max = take_max.groupby(['id', 'date', 'element'], as_index=False)['value'].max()
    combined_min = take_min.groupby(['id', 'date', 'element'], as_index=False)['value'].min()

    return pd.concat([combined_max, combined_min], ignore_index=True)


def pivot_to_wide(dly):
    """Reshape one row per id/date/element into one row per id/date, elements as columns.

    Requires id/date/element to already be unique -- run
    combine_duplicate_observations() first, or this raises ValueError.
    """
    return dly.pivot(
        index=['id', 'date'],
        columns='element',
        values='value'
    ).reset_index()


def parse_observation_dates(dly):
    """Convert the NOAA YYYYMMDD date column into a Python date."""
    dly = dly.copy()
    dly['date'] = pd.to_datetime(dly['date'].astype(str), format='%Y%m%d').dt.date
    return dly


def validate_observations(dly):
    """Raise if any row doesn't match the DailyObservation schema."""
    observation_list.validate_python(dly.to_dict(orient="records"))
    return dly


def transform(twentytwenty_dly):
    """Keep core, quality-passed elements; combine duplicate readings; pivot to wide format."""
    filtered = filter_quality_observations(twentytwenty_dly)
    combined = combine_duplicate_observations(filtered)
    pivoted = pivot_to_wide(combined)
    dated = parse_observation_dates(pivoted)
    return validate_observations(dated)
