import pandas as pd

from etl.extract_forecast import extract_forecast
from etl.transform_forecast import transform_forecast
from etl.load import get_engine, upsert_daily

if __name__ == '__main__':
    engine = get_engine()

    stations = pd.read_sql('SELECT station_id, latitude, longitude, state FROM stations', engine)

    forecast = extract_forecast(stations, state="TN")
    forecast = transform_forecast(forecast)
    upsert_daily(engine, forecast, "daily_forecast")
