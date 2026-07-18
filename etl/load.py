import os

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
    """Writes df to table_name, replacing it entirely if it already exists."""
    df.to_sql(
        table_name, 
        engine, 
        if_exists="replace", 
        index=False,
        method="multi",
        chunksize=10000
    )
    print(f"Loaded {len(df)} rows into {table_name}")
