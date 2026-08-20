-- Daily forecast pulled from Open-Meteo, kept separate from daily_actual/
-- daily_historical since it's a different kind of thing (a forecast snapshot,
-- not an observation) and isn't tied to a GHCNd station ID at the source.
-- Same (id, date) shape and UNIQUE constraint as the other daily tables so it
-- can reuse upsert_daily() as-is.

CREATE TABLE daily_forecast (
    id TEXT NOT NULL,
    date DATE NOT NULL,
    "TMAX" DOUBLE PRECISION,
    "TMIN" DOUBLE PRECISION,
    "PRCP" DOUBLE PRECISION,
    CONSTRAINT daily_forecast_id_date_uniq UNIQUE (id, date)
);
