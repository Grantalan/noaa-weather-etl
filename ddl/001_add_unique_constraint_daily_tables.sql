-- upsert_daily() relies on ON CONFLICT (id, date), which requires a real
-- UNIQUE constraint on those columns to target. Plain pandas.to_sql table
-- creation has no way to know (id, date) should be unique, so this has
-- to be added by hand. Already applied to production directly; this file
-- just captures it so a fresh database can be brought to the same state.

ALTER TABLE daily_actual ADD CONSTRAINT daily_actual_id_date_uniq UNIQUE (id, date);
ALTER TABLE daily_historical ADD CONSTRAINT daily_historical_id_date_uniq UNIQUE (id, date);
