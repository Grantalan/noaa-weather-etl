import pandas as pd

# Source: https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt


def extract():
    """Extract raw 2020 year.csv with all daily values."""
    col_names = ['id', 'date', 'element', 'value',
                 'mflag', 'qflag', 'sflag', 'obs_time']

    twentytwenty_dly = pd.read_csv(
        'data/raw/2020.csv.gz',
        compression='gzip',
        header=None,
        names=col_names
    )
    return twentytwenty_dly


def extract_stations():
    """Get station IDs from URL to the official NOAA GHCN-Daily stations"""
    url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"

    # Define the exact character positions based on the NOAA README
    col_specs = [
        (0, 11),   # station_id
        (12, 20),  # latitude
        (21, 30),  # longitude
        (31, 37)   # elevation
    ]

    column_names = ['station_id', 'latitude', 'longitude', 'elevation']

    # Safely extract the data
    station_metadata = pd.read_fwf(
        url,
        colspecs=col_specs,
        header=None,
        names=column_names,
        na_values=[-999.9]
    )

    return station_metadata
