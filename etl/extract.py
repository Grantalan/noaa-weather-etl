import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd
from pydantic import TypeAdapter

from etl.models import Station

# Source: https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-stations.txt

station_list = TypeAdapter(list[Station])

RAW_DIR = Path("data/raw")


def fetch(url):
    """Download url into data/raw/, reusing the cached copy if NOAA says it's unchanged.

    NOAA serves an ETag on these files, so a run that finds nothing new pays a
    single conditional request instead of a full re-download. That matters here --
    the files arrive at roughly 190 KB/s, which makes downloading, not parsing,
    the bulk of the pipeline's runtime.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)  # Create data/raw if it doesn't exist; raw files are gitignored.
    path = RAW_DIR / url.rsplit("/", 1)[-1]      
    etag_path = path.with_suffix(path.suffix + ".etag")
    
    # If we have a cached copy and its ETag, attach it for a conditional request.
    request = urllib.request.Request(url)
    if path.exists() and etag_path.exists():
        request.add_header("If-None-Match", etag_path.read_text())  # Read etag for server comparison.

    try:
        with urllib.request.urlopen(request) as response:  # Send request to NOAA.
            path.write_bytes(response.read())
            etag = response.headers.get("ETag")
            if etag:
                etag_path.write_text(etag)
    except urllib.error.HTTPError as exc:
        # 304 means the cached copy is still current; anything else is a real error.
        if exc.code != 304:
            raise

    return path


def extract(year):
    """Pull a given year's daily values directly from NOAA."""
    col_names = ['id', 'date', 'element', 'value',
                 'mflag', 'qflag', 'sflag', 'obs_time']

    url = f"https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_year/{year}.csv.gz"

    dly = pd.read_csv(
        fetch(url),
        compression='gzip',
        header=None,
        names=col_names
    )
    return dly


def extract_current_year():
    """Pull the current year's daily values directly from NOAA."""
    col_names = ['id', 'date', 'element', 'value',
                 'mflag', 'qflag', 'sflag', 'obs_time']

    year = date.today().year
    url = f"https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_year/{year}.csv.gz"

    current_dly = pd.read_csv(
        fetch(url),
        compression='gzip',
        header=None,
        names=col_names
    )
    return current_dly


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
        'hcn_crn_flag': str, 
        'wmo_id': str
    }

    # Safely extract the data
    station_metadata = pd.read_fwf(
        fetch(url),
        colspecs=col_specs,
        header=None,
        names=column_names,
        dtype=column_types,
        keep_default_na=False
    )

    station_list.validate_python(station_metadata.to_dict(orient="records"))

    return station_metadata
