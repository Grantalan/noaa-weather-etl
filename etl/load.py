import os
import tempfile

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

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
    try:
        existing_df = pd.read_sql(f"SELECT * FROM {table_name}", engine)
    except Exception:
        existing_df = df.iloc[0:0]

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


def copy_into_staging(engine, df, staging_table, target_table):
    """Bulk-load df into a fresh staging_table using COPY.

    The staging table is built with CREATE TABLE (LIKE target_table) instead of
    letting pandas infer the types. pandas infers from values, so it hands back
    TEXT for the object-dtype date column, and Postgres won't implicitly cast
    text to date in the INSERT ... SELECT that follows.

    COPY replaces to_sql(method="multi"), which sent every row as generated
    INSERT ... VALUES text: 348s of a 423s full-year load, against 18s here.
    """
    columns = ", ".join(f'"{c}"' for c in df.columns)

    with engine.begin() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {staging_table}"))
        conn.execute(text(f"CREATE TABLE {staging_table} (LIKE {target_table})"))

    # NaN becomes an empty field, which COPY ... FORMAT csv reads as NULL --
    # which is what the COALESCE in the upsert below expects.
    raw_conn = engine.raw_connection()
    try:
        with tempfile.TemporaryFile(mode="w+", newline="") as buffer:
            df.to_csv(buffer, index=False, header=False)
            buffer.seek(0)
            with raw_conn.cursor() as cur:
                cur.copy_expert(
                    f"COPY {staging_table} ({columns}) FROM STDIN WITH (FORMAT csv)",
                    buffer,
                )
        raw_conn.commit()
    finally:
        raw_conn.close()


def upsert_daily(engine, df, target_table, staging_table="daily_upsert"):
    """Load df into a staging table, then upsert into target_table on (id, date).

    Each column takes the incoming value unless it's null, in which case
    the existing value is kept -- so a later load with missing data never
    blanks out a value that was already there. Requires target_table to
    already exist, with a UNIQUE (id, date) constraint.
    """
    copy_into_staging(engine, df, staging_table, target_table)

    value_cols = [c for c in df.columns if c not in ("id", "date")]
    col_list = ", ".join(f'"{c}"' for c in df.columns)
    set_clause = ", ".join(
        f'"{c}" = COALESCE(EXCLUDED."{c}", {target_table}."{c}")' for c in value_cols
    )

    upsert_sql = f"""
        INSERT INTO {target_table} ({col_list})
        SELECT {col_list} FROM {staging_table}
        ON CONFLICT (id, date) DO UPDATE SET {set_clause};
    """

    with engine.begin() as conn:
        conn.execute(text(upsert_sql))

    print(f"Upserted {len(df)} rows into {target_table} via {staging_table}")
