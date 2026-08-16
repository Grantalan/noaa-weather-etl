-- Base tables that main.py/backfill.py load into. These previously only
-- existed because pandas.to_sql auto-created them on first load against
-- production -- never captured as DDL, so a fresh database had no way to
-- get them. Numbered 000 (before 001) since 001's ALTER TABLE requires
-- daily_actual/daily_historical to already exist.

CREATE TABLE stations (
    station_id TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    elevation DOUBLE PRECISION,
    state TEXT,
    name TEXT,
    gsn_flag TEXT,
    hcn_crn_flag TEXT,
    wmo_id TEXT
);

CREATE TABLE daily_actual (
    id TEXT,
    date DATE,
    "PRCP" DOUBLE PRECISION,
    "SNOW" DOUBLE PRECISION,
    "SNWD" DOUBLE PRECISION,
    "TMAX" DOUBLE PRECISION,
    "TMIN" DOUBLE PRECISION
);

CREATE TABLE daily_historical (
    id TEXT,
    date DATE,
    "PRCP" DOUBLE PRECISION,
    "SNOW" DOUBLE PRECISION,
    "SNWD" DOUBLE PRECISION,
    "TMAX" DOUBLE PRECISION,
    "TMIN" DOUBLE PRECISION
);
