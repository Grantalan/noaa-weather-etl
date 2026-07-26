from etl.extract import extract
from etl.transform import transform
from etl.load import get_engine

if __name__ == '__main__':
    engine = get_engine()

    for year in range(2021, 2026):
        historical_dly = extract(year)
        historical_dly = transform(historical_dly)
        historical_dly.to_sql(
            "daily_historical", engine, if_exists="append",
            index=False, method="multi", chunksize=1000
        )
        print(f"Loaded {len(historical_dly)} rows for {year} into daily_historical")
