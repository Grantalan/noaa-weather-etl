CORE_ELEMENTS = ['TMAX', 'TMIN', 'PRCP', 'SNOW', 'SNWD']


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

    return pivoted
