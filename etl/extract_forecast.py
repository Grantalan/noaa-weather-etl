import json
import time
import urllib.error
import urllib.parse
import urllib.request

import pandas as pd

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Open-Meteo's free tier allows <10,000 calls/day and 600/min. A batch this
# size keeps the request URL well under typical server URL-length limits and,
# with the sleep between batches below, keeps us far under either rate limit.
BATCH_SIZE = 250

MAX_RETRIES = 5
INITIAL_BACKOFF_SECONDS = 5


def _fetch_with_retry(url):
    """Open-Meteo's free tier occasionally throttles bursts of requests with a
    429 even when well under its documented rate limits. Retry with exponential
    backoff instead of failing the whole run over a transient block.
    """
    backoff = INITIAL_BACKOFF_SECONDS

    # Try the API request up to 5 times
    for attempt in range(MAX_RETRIES):
        try:

            # Reads the response bytes and parses them as JSON
            with urllib.request.urlopen(url) as response:
                return json.loads(response.read())
            
        # Catch HTTP errors returned by the API
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt == MAX_RETRIES - 1:
                raise
            time.sleep(backoff)

            # Use Exponential backoff if request hits rate limit
            backoff *= 2


def fetch_forecast_batch(station_ids, latitudes, longitudes):
    """Fetch daily TMAX/TMIN/PRCP forecasts for a batch of stations in one request.

    Open-Meteo accepts comma-separated latitude/longitude lists and returns one
    result object per location, in the same order -- so a single request covers
    the whole batch instead of one call per station.
    """
    params = {
        "latitude": ",".join(str(v) for v in latitudes),
        "longitude": ",".join(str(v) for v in longitudes),
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": "GMT",
    }
    url = f"{FORECAST_URL}?{urllib.parse.urlencode(params)}"

    results = _fetch_with_retry(url)

    # A single-location request returns one object instead of a list.
    if isinstance(results, dict):
        results = [results]

    frames = []
    for station_id, result in zip(station_ids, results):
        daily = pd.DataFrame(result["daily"]).rename(columns={
            "time": "date",
            "temperature_2m_max": "TMAX",
            "temperature_2m_min": "TMIN",
            "precipitation_sum": "PRCP",
        })
        daily.insert(0, "id", station_id)
        frames.append(daily)

    return pd.concat(frames, ignore_index=True)


def extract_forecast(stations_df, state, batch_size=BATCH_SIZE):
    """Pull daily forecasts for stations in one US state, batched to stay within URL/rate limits."""
    stations = stations_df[stations_df["state"] == state]

    batches = []
    for start in range(0, len(stations), batch_size):
        chunk = stations.iloc[start:start + batch_size]
        batches.append(fetch_forecast_batch(
            chunk["station_id"].tolist(),
            chunk["latitude"].tolist(),
            chunk["longitude"].tolist(),
        ))
        time.sleep(1)

    return pd.concat(batches, ignore_index=True)
