import pandas as pd
from pydantic import TypeAdapter

from etl.models import DailyObservation

CORE_ELEMENTS = ['TMAX', 'TMIN', 'PRCP', 'SNOW', 'SNWD']
observation_list = TypeAdapter(list[DailyObservation])


def transform(twentytwenty_dly):
    """Keep core elements and quality-passed rows, then pivot to wide format"""
    filtered = twentytwenty_dly[
        twentytwenty_dly['element'].isin(CORE_ELEMENTS)
        & twentytwenty_dly['qflag'].isna()
    ]

    pivoted = filtered.pivot(
        index=['id', 'date'],
        columns='element',
        values='value'
    ).reset_index()

    pivoted['date'] = pd.to_datetime(pivoted['date'].astype(str), format='%Y%m%d').dt.date

    observation_list.validate_python(pivoted.to_dict(orient="records"))

    return pivoted
