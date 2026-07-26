from etl.extract import extract_current_year, extract_stations
from etl.transform import transform
from etl.load import get_engine, load_df

if __name__ == '__main__':
    engine = get_engine()

    current_dly = extract_current_year()
    current_dly = transform(current_dly)
    load_df(engine, current_dly, "daily_actual")

    stations = extract_stations()
    stations.to_csv('data/processed/stations.csv', index=False)
    load_df(engine, stations, "stations")

