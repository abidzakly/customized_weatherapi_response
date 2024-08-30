from typing import List, Dict, Optional
from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime, timedelta

app = FastAPI()

class MainData(BaseModel):
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    sea_level: int
    grnd_level: int
    humidity: int
    temp_kf: float

class WeatherData(BaseModel):
    id: int
    main: str
    description: str
    icon: str

class CloudsData(BaseModel):
    all: int

class WindData(BaseModel):
    speed: float
    deg: int
    gust: float

class SysData(BaseModel):
    pod: str

class WeatherEntry(BaseModel):
    dt: int
    main: MainData
    weather: List[WeatherData]
    clouds: CloudsData
    wind: WindData
    visibility: int
    pop: float
    rain: Optional[Dict[str, float]] = None
    sys: SysData
    dt_txt: str

class DayNightWeather(BaseModel):
    temp: float
    humidity: float
    windSpeed: float
    visibility: float
    weather_main: str
    weather_icon: str

class DailyWeatherResponse(BaseModel):
    day_averages: DayNightWeather
    night_averages: DayNightWeather

class WeatherResponse(BaseModel):
    date: str
    day_averages: DayNightWeather
    night_averages: DayNightWeather

class InputData(BaseModel):
    list: List[WeatherEntry]
    
class ForecastsResponse(BaseModel):
    forecasts: List[WeatherResponse]

@app.post("/weather/averages", response_model=ForecastsResponse)
async def get_weather_averages(input_data: InputData) -> ForecastsResponse:
    def calculate_averages(data_entries):
        if not data_entries:
            return DayNightWeather(
                temp=0.0,
                humidity=0.0,
                windSpeed=0.0,
                visibility=0.0,
                weather_main="",
                weather_icon=""
            )

        total_temp = 0.0
        total_humidity = 0.0
        total_wind_speed = 0.0
        total_visibility = 0.0
        weather_main = data_entries[0].weather[0].main
        weather_icon = data_entries[0].weather[0].icon

        for entry in data_entries:
            total_temp += entry.main.temp
            total_humidity += entry.main.humidity
            total_wind_speed += entry.wind.speed
            total_visibility += entry.visibility

        count = len(data_entries)
        return DayNightWeather(
            temp=total_temp / count,
            humidity=total_humidity / count,
            windSpeed=total_wind_speed / count,
            visibility=total_visibility / count,
            weather_main=weather_main,
            weather_icon=weather_icon
        )

    def format_date(date_str):
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        today = datetime.today().date()
        tomorrow = today + timedelta(days=1)

        if date_obj.date() == today:
            return "Today"
        elif date_obj.date() == tomorrow:
            return "Tomorrow"
        else:
            return date_obj.strftime("%b %d")  # Example: "Aug 26"

    # Group entries by date
    grouped_entries = {}
    for entry in input_data.list:
        date_str = entry.dt_txt.split(" ")[0]
        if date_str not in grouped_entries:
            grouped_entries[date_str] = []
        grouped_entries[date_str].append(entry)

    results = []

    for date, date_entries in grouped_entries.items():
        day_data = [entry for entry in date_entries if entry.sys.pod == 'd']
        night_data = [entry for entry in date_entries if entry.sys.pod == 'n']

        day_averages = calculate_averages(day_data)
        night_averages = calculate_averages(night_data)

        results.append(WeatherResponse(
            date=format_date(date),
            day_averages=day_averages,
            night_averages=night_averages
        ))

    return ForecastsResponse(forecasts=results)