import pandas as pd
from pydantic import TypeAdapter

from etl.models import DailyObservation

observation_list = TypeAdapter(list[DailyObservation])


def parse_forecast_dates(forecast_df):
    """Convert Open-Meteo's ISO date strings into Python dates."""
    forecast_df = forecast_df.copy()
    forecast_df['date'] = pd.to_datetime(forecast_df['date']).dt.date
    return forecast_df


def validate_forecast(forecast_df):
    """Raise if any row doesn't match the DailyObservation schema.

    Reuses the same schema as the GHCNd pipeline -- id/date/TMAX/TMIN/PRCP line
    up exactly, and SNOW/SNWD are simply absent here since Open-Meteo's daily
    forecast doesn't include them.
    """
    observation_list.validate_python(forecast_df.to_dict(orient="records"))
    return forecast_df


def transform_forecast(forecast_df):
    """Parse dates and validate; TMAX/TMIN/PRCP already arrive in °C/mm, no unit conversion needed."""
    dated = parse_forecast_dates(forecast_df)
    return validate_forecast(dated)
