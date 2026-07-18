import os

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DB_HOST = os.getenv("PGHOST", "localhost")
DB_PORT = os.getenv("PGPORT", "5432")
DB_NAME = os.getenv("PGDATABASE", "ghcnd_etl")
DB_USER = os.getenv("PGUSER")
DB_PASSWORD = os.getenv("PGPASSWORD")


def get_engine():
    engine = create_engine(
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    return engine


def load_df(engine, df, table_name):
    """Writes only new or changed rows to table_name."""
    existing_df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
    merged = df.merge(existing_df, how="left", indicator=True)
    rows_to_write = merged[merged["_merge"] == "left_only"].drop(columns="_merge")

    rows_to_write.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000
    )
    print(f"Loaded {len(rows_to_write)} rows into {table_name}")
