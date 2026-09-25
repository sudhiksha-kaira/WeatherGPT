import os
import requests
from dotenv import load_dotenv

from utils.location_search import search_location

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")


def geocode_location(location, state="", country=""):

    state_map = {
        "mp": "Madhya Pradesh",
        "ts": "Telangana",
        "ap": "Andhra Pradesh",
        "ka": "Karnataka",
        "mh": "Maharashtra",
        "tn": "Tamil Nadu",
        "kl": "Kerala",
        "up": "Uttar Pradesh",
        "rj": "Rajasthan",
        "gj": "Gujarat",
        "wb": "West Bengal",
        "od": "Odisha",
        "br": "Bihar",
        "jh": "Jharkhand",
        "pb": "Punjab",
        "hr": "Haryana",
        "dl": "Delhi"
    }

    state = state_map.get(
        state.lower().strip(),
        state.strip()
    )

    query_parts = [location.strip()]

    if state:
        query_parts.append(state)

    if country:
        query_parts.append(country.strip())

    query = ", ".join(query_parts)

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": query,
        "format": "jsonv2",
        "limit": 1,
        "addressdetails": 1
    }

    headers = {
        "User-Agent": "WeatherGPT/1.0"
    }

    try:

        response = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=10
        )

    except requests.RequestException:

        return None

    if response.status_code != 200:
        return None

    results = response.json()

    if not results:
        return None

    result = results[0]
    address = result.get("address", {})

    return {
        "name": (
            address.get("city")
            or address.get("town")
            or address.get("village")
            or address.get("municipality")
            or location
        ),
        "state": address.get("state", state),
        "country": address.get("country", country),
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"])
    }


def get_weather(location, state="", country=""):

    results = search_location(location)

    place = None

    # First try our LGD + coordinate database
    for result in results:

        if (
            "latitude" in result
            and "longitude" in result
        ):

            place = result
            break

    # If coordinates aren't available,
    # use geocoding as a fallback
    if not place:

        place = geocode_location(
            location,
            state,
            country
        )

        if not place:

            return None, (
                f"Coordinates for '{location}' "
                "are not available."
            )

        place["district"] = ""
        place["subdistrict"] = ""

    latitude = place["latitude"]
    longitude = place["longitude"]

    weather_url = (
        "https://api.openweathermap.org/"
        "data/2.5/weather"
    )

    weather_params = {
        "lat": latitude,
        "lon": longitude,
        "appid": API_KEY,
        "units": "metric"
    }

    try:

        response = requests.get(
            weather_url,
            params=weather_params,
            timeout=10
        )

    except requests.RequestException:

        return None, (
            "Unable to connect to "
            "weather service."
        )

    if response.status_code != 200:

        return None, (
            "Unable to get weather information."
        )

    data = response.json()

    weather = {
        "city": place["name"],
        "state": place.get("state", state or ""),
        "country": place.get("country", country or "India"),
        "district": place.get("district", ""),
        "subdistrict": place.get("subdistrict", ""),
        "temperature": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "wind_speed": data["wind"]["speed"],
        "condition": data["weather"][0]["description"],
        "latitude": latitude,
        "longitude": longitude
    }

    return weather, None

def get_forecast(latitude, longitude):

    forecast_url = (
        "https://api.openweathermap.org/"
        "data/2.5/forecast"
    )

    forecast_params = {
        "lat": latitude,
        "lon": longitude,
        "appid": API_KEY,
        "units": "metric"
    }

    try:

        response = requests.get(
            forecast_url,
            params=forecast_params,
            timeout=10
        )

    except requests.RequestException:

        return None, "Unable to connect to forecast service."

    if response.status_code != 200:

        return None, "Unable to get forecast information."

    data = response.json()

    forecast = []

    for item in data["list"]:

        forecast.append({
            "datetime": item["dt_txt"],
            "temperature": item["main"]["temp"],
            "feels_like": item["main"]["feels_like"],
            "humidity": item["main"]["humidity"],
            "wind_speed": item["wind"]["speed"],
            "condition": item["weather"][0]["description"],
            "rain_probability": item.get("pop", 0)
        })

    return forecast, None

def get_weather_by_coordinates(latitude, longitude):

    weather_url = (
        "https://api.openweathermap.org/"
        "data/2.5/weather"
    )

    weather_params = {
        "lat": latitude,
        "lon": longitude,
        "appid": API_KEY,
        "units": "metric"
    }

    try:

        response = requests.get(
            weather_url,
            params=weather_params,
            timeout=10
        )

    except requests.RequestException:

        return None, (
            "Unable to connect to "
            "weather service."
        )

    if response.status_code != 200:

        return None, (
            "Unable to get weather information."
        )

    data = response.json()

    weather = {
        "city": data.get(
            "name",
            "Current Location"
        ),

        "state": "",

        "country": data.get(
            "sys",
            {}
        ).get(
            "country",
            ""
        ),

        "district": "",

        "subdistrict": "",

        "temperature": data["main"]["temp"],

        "feels_like": data["main"]["feels_like"],

        "humidity": data["main"]["humidity"],

        "pressure": data["main"]["pressure"],

        "wind_speed": data["wind"]["speed"],

        "condition": data["weather"][0]["description"],

        "latitude": latitude,

        "longitude": longitude
    }

    return weather, None