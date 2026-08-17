This is my very first ETL pipeline - open to recommendations, tips, and criticism.

![NOAA](./assets/noaa1.jpg)

## Data Source

This project uses the [NOAA Global Historical Climatology Network Daily (GHCNd)](https://www.ncei.noaa.gov/pub/data/ghcn/daily/) dataset, maintained by the National Centers for Environmental Information (NCEI).

Dataset documentation: https://www.ncei.noaa.gov/pub/data/ghcn/daily/readme.txt

Daily forecasts (TMAX/TMIN/PRCP) are pulled from the [Open-Meteo Forecast API](https://open-meteo.com/en/docs), a free weather forecast API.
