# NOAA GHCNd Weather ETL

A daily ETL pipeline that pulls NOAA Global Historical Climatology Network (GHCNd)
weather observations and Open-Meteo forecasts, reshapes them into analysis-ready
tables, and loads them into Postgres — with Metabase, running in Docker, for
visualization.

![NOAA](./assets/noaa1.jpg)

My first ETL pipeline — open to recommendations, tips, and criticism.

---

## What it does

```
NOAA GHCNd  →  extract  →  transform  →  load  →  Postgres  →  Metabase
              (cached)     (reshape)    (COPY)              (Docker)
```

1. **Extract** — downloads the current year's observations and the station
   metadata file. Downloads are cached in `data/raw/` and revalidated with HTTP
   ETags, so a run that finds nothing new pays one conditional request instead
   of re-downloading ~83 MB.
2. **Transform** — keeps the five core elements that passed NOAA's quality
   control, resolves duplicate readings, and pivots from one row per
   measurement to one row per station-day.
3. **Load** — bulk-loads into a staging table with Postgres `COPY`, then upserts
   into the target on `(id, date)`.
4. **Visualize** — Metabase, running in Docker, connects to Postgres so the
   loaded data can be explored and charted without writing SQL by hand.

---

## Requirements

- Python 3.13
- [uv](https://docs.astral.sh/uv/)
- A Postgres database you can write to
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — optional, only needed to run Metabase for visualization

---

## Setup

**1. Clone and install**

```bash
git clone https://github.com/Grantalan/noaa-weather-etl.git
cd noaa-weather-etl
uv sync
```

`uv sync` creates `.venv/` and installs the exact versions pinned in `uv.lock`.
No manual virtualenv activation is needed — use `uv run` to execute anything.

**2. Get a Postgres database**

Any Postgres 16+ instance works. If you don't already have one, the fastest
way is a throwaway Docker container:

```bash
docker run --name ghcnd-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:16
```

**3. Configure the database connection**

Create a `.env` file in the project root with:

```
PGHOST=localhost
PGPORT=5432
PGDATABASE=ghcnd_etl
PGUSER=postgres
PGPASSWORD=postgres
```

Adjust the values to match your actual database. `.env` is gitignored and
should never be committed.

**4. Create the schema**

Apply the DDL in order:

```bash
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -f ddl/000_create_base_tables.sql
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -f ddl/001_add_unique_constraint_daily_tables.sql
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE -f ddl/002_create_daily_forecast_table.sql
```

`000` has to run first — `001`'s `ALTER TABLE` requires `daily_actual`/
`daily_historical` to already exist. The `UNIQUE (id, date)` constraint `001`
adds is not optional either: the loader's `ON CONFLICT (id, date)` upsert has
nothing to target without it, and the staging table is built with
`CREATE TABLE (LIKE daily_actual)`, which requires the target table to
already exist.

**5. Verify**

```bash
uv run pytest
```

---

## Usage

**Daily load** — current year's observations plus refreshed station metadata:

```bash
uv run python main.py
```

**Historical backfill** — loads 2021–2025 into `daily_historical`:

```bash
uv run python backfill.py
```

**Daily forecast** — pulls Open-Meteo forecasts into `daily_forecast`:

```bash
uv run python forecast_daily.py
```

Note that the first run downloads roughly 83 MB for the current year and 11 MB
of station metadata. Subsequent runs reuse the cached copies in `data/raw/`
unless NOAA reports the files have changed.

---

## Visualizing with Metabase

Metabase runs in Docker, pointed at your existing Postgres — not a second,
empty containerized database.

```bash
docker compose up -d metabase
uv run python scripts/configure_metabase.py
```

The script replaces Metabase's browser setup wizard: it creates the admin
account and connects your Postgres database via Metabase's REST API in one
step. It's safe to re-run — it detects an existing setup/connection and skips
instead of erroring or duplicating.

Log in at http://localhost:3000 with these variables, added to `.env`:

| Variable | Description |
|---|---|
| `MB_ADMIN_EMAIL` | Admin account email |
| `MB_ADMIN_PASSWORD` | Admin account password |
| `MB_ADMIN_FIRST_NAME` / `MB_ADMIN_LAST_NAME` | Admin account name |
| `MB_SITE_NAME` | Metabase instance name |

Postgres itself keeps running natively, unchanged. Metabase reaches it over
`host.docker.internal` — Docker Desktop's DNS name for "the host machine" —
not `localhost`, which from inside the container would mean the container
itself.

---

## Schema

### `daily_actual` / `daily_historical`

One row per station per day. All measurement columns are nullable — a station
reporting temperature but not snowfall produces `NULL` for `SNOW`.

| Column | Type | Description |
|---|---|---|
| `id` | `TEXT` | GHCNd station identifier |
| `date` | `DATE` | Observation date |
| `TMAX` | `DOUBLE PRECISION` | Maximum temperature |
| `TMIN` | `DOUBLE PRECISION` | Minimum temperature |
| `PRCP` | `DOUBLE PRECISION` | Precipitation |
| `SNOW` | `DOUBLE PRECISION` | Snowfall |
| `SNWD` | `DOUBLE PRECISION` | Snow depth |

Unique on `(id, date)`.

### `stations`

| Column | Type | Description |
|---|---|---|
| `station_id` | `TEXT` | GHCNd station identifier — joins to `daily_actual.id` |
| `latitude` | `DOUBLE PRECISION` | Decimal degrees |
| `longitude` | `DOUBLE PRECISION` | Decimal degrees |
| `elevation` | `DOUBLE PRECISION` | Meters |
| `state` | `TEXT` | US state / territory code, blank for non-US |
| `name` | `TEXT` | Station name |
| `gsn_flag` | `TEXT` | GCOS Surface Network flag |
| `hcn_crn_flag` | `TEXT` | US Historical Climatology Network flag |
| `wmo_id` | `TEXT` | World Meteorological Organization ID, where assigned |

> The join key is named `id` on the observation tables and `station_id` on
> `stations`.

### `daily_forecast`

Same shape as `daily_actual`/`daily_historical`, minus `SNOW`/`SNWD` — Open-Meteo's
daily forecast doesn't include them. Unique on `(id, date)`.

---

## How it works

### Caching (`etl/extract.py`)

`fetch()` stores each download in `data/raw/` alongside a `.etag` sidecar file.
On the next run it sends the stored ETag as `If-None-Match`; NOAA answers `304
Not Modified` when nothing has changed and the cached copy is reused.

NOAA rebuilds the current-year file daily as new observations arrive, so the
daily run will usually get a fresh download. The cache pays off on the station
metadata file (stable for weeks), on retries after a mid-pipeline failure, and
during development.

### Transformation (`etl/transform.py`)

- **Quality filter** — keeps only `TMAX`, `TMIN`, `PRCP`, `SNOW`, `SNWD`, and
  only rows where NOAA's quality flag is blank.
- **Duplicate handling** — when a station reports the same element twice on the
  same day, the most extreme reading wins: highest for `TMAX`/`PRCP`/`SNOW`/
  `SNWD`, lowest for `TMIN`. Averaging would hide genuine extremes, and pivoting
  without resolving duplicates raises.
- **Pivot** — one row per `(id, date)` with elements as columns.
- **Validation** — every row is checked against a Pydantic model before loading.

### Loading (`etl/load.py`)

Rows are streamed into a staging table with `COPY ... FROM STDIN`, then upserted:

```sql
INSERT INTO daily_actual (...)
SELECT ... FROM daily_upsert
ON CONFLICT (id, date) DO UPDATE SET
    col = COALESCE(EXCLUDED.col, daily_actual.col);
```

The `COALESCE` means an incoming `NULL` never overwrites a value already stored —
so a later load with missing readings can't blank out good data.

The staging table is created with `CREATE TABLE (LIKE daily_actual)` rather than
letting pandas infer types, because inference produces `TEXT` for the date column
and Postgres will not implicitly cast text to date in the `INSERT ... SELECT`.

---

## Project layout

```
etl/
  extract.py             NOAA downloads + ETag caching
  extract_forecast.py    Open-Meteo forecast fetch
  transform.py           filtering, deduplication, pivot, validation
  transform_forecast.py  date parsing + validation for forecast data
  load.py                engine, COPY bulk load, upsert
  models.py              Pydantic schemas
main.py                  daily pipeline
backfill.py              historical load
forecast_daily.py        daily forecast pipeline
ddl/                     schema migrations, applied in filename order
scripts/
  configure_metabase.py  Metabase admin + database setup via its REST API
docker-compose.yml       runs Metabase, pointed at your native Postgres
tests/                   pytest suite
data/raw/                cached downloads (gitignored)
data/processed/          intermediate output (gitignored)
```

---

## Testing

```bash
uv run pytest
```

---

## Data notes

- **Units.** GHCNd stores temperatures in tenths of degrees Celsius and
  precipitation in tenths of millimetres. Check whether values are converted
  before charting them.
- **Quality flags.** Only observations with a blank quality flag are loaded;
  anything NOAA marked as suspect is dropped.
- **Late arrivals.** NOAA backfills observations into past dates as stations
  report late, and rebuilds prior-year files. Data for a given day can change
  after you first load it — which is why the upsert is designed to be safe to
  re-run.

---

## Data sources

[NOAA Global Historical Climatology Network Daily (GHCNd)](https://www.ncei.noaa.gov/pub/data/ghcn/daily/),
maintained by the National Centers for Environmental Information (NCEI), for
observed/historical data.

Dataset documentation: https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt

Daily forecasts (TMAX/TMIN/PRCP) are pulled from the
[Open-Meteo Forecast API](https://open-meteo.com/en/docs), a free weather
forecast API, into `daily_forecast`.
