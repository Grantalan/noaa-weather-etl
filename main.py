from etl.extract import extract, extract_stations
from etl.transform import transform
from etl.load import get_engine, load_df

engine = get_engine()

# Local file (data/raw/2020.csv.gz). Filters to 5 core elements + passed qflag, then pivots.
twentytwenty_dly = extract()
twentytwenty_dly = transform(twentytwenty_dly)
load_df(engine, twentytwenty_dly, "daily_2020")

# Live fetch from NOAA (needs network). Also saves a local CSV snapshot.
stations = extract_stations()
stations.to_csv('data/processed/stations.csv', index=False)
load_df(engine, stations, "stations")
