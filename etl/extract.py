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
    """Get station IDs from URL of official NOAA GHCN-Daily stations"""
    url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt"

    # Define the exact character positions based on the NOAA README
    col_specs = [
        (0, 11),   # station_id
        (12, 20),  # latitude
        (21, 30),  # longitude
        (31, 37),  # elevation
        (38, 40),  # state           
        (41, 71),  # name            
        (72, 75),  # gsn_flag        
        (76, 79),  # hcn_crn_flag
        (80, 85),  # wmo_id
    ]

    column_names = [
        'station_id', 'latitude', 'longitude', 'elevation',
        'state', 'name', 'gsn_flag', 'hcn_crn_flag', 'wmo_id'
    ]

    column_types = {
        'station_id': str, 
        'state': str, 
        'gsn_flag': str, 
        'wmo_id': str
    }

    # Safely extract the data
    station_metadata = pd.read_fwf(
        url,
        colspecs=col_specs,
        header=None,
        names=column_names,
        dtype=column_types,
        keep_default_na=False
    )

    return station_metadata
