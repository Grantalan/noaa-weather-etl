from etl.extract import extract
from etl.transform import transform
from etl.load import get_engine, upsert_daily

if __name__ == '__main__':
    engine = get_engine()

    for year in range(2021, 2026):
        historical_dly = extract(year)
        historical_dly = transform(historical_dly)
        upsert_daily(engine, historical_dly, "daily_historical")
