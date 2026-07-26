from datetime import date

from pydantic import BaseModel


class DailyObservation(BaseModel):
    id: str
    date: date
    TMAX: float | None = None
    TMIN: float | None = None
    PRCP: float | None = None
    SNOW: float | None = None
    SNWD: float | None = None


class Station(BaseModel):
    station_id: str
    latitude: float
    longitude: float
    elevation: float
    state: str
    name: str
    gsn_flag: str
    hcn_crn_flag: str
    wmo_id: str
