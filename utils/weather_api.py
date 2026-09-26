import os
import csv
import requests
from dotenv import load_dotenv
from rapidfuzz import process, fuzz

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LGD_FILE = os.path.join(BASE_DIR, "data", "LGD", "villages_clean.csv")
COORDINATE_FILE = os.path.join(BASE_DIR, "data", "LGD", "village_coordinates.csv")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPENWEATHER_GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
ARCGIS_GEOCODING_URL = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

HEADERS = {"User-Agent": "WeatherGPT/1.0"}

def load_lgd_villages():
    villages = []
    if not os.path.exists(LGD_FILE):
        return villages
    try:
        with open(LGD_FILE, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row in reader:
                name = (row.get("Village Name ") or row.get("Village Name") or "").strip()
                district = (row.get("District Name") or "").strip()
                subdistrict = (row.get("Sub-District Name") or row.get("Sub District Name") or "").strip()
                village_code = (row.get("Village Code") or "").strip()
                if name:
                    villages.append({
                        "name": name,
                        "district": district,
                        "subdistrict": subdistrict,
                        "village_code": village_code
                    })
    except Exception:
        return []
    return villages

def load_lgd_coordinates():
    coordinates = {}
    if not os.path.exists(COORDINATE_FILE):
        return coordinates
    try:
        with open(COORDINATE_FILE, "r", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            for row in reader:
                code = (row.get("Village Code") or "").strip()
                try:
                    coordinates[code] = {
                        "latitude": float(row["Latitude"]),
                        "longitude": float(row["Longitude"])
                    }
                except (KeyError, TypeError, ValueError):
                    continue
    except Exception:
        return {}
    return coordinates

LGD_VILLAGES = load_lgd_villages()
LGD_COORDINATES = load_lgd_coordinates()
LGD_NAMES = [v["name"] for v in LGD_VILLAGES]

def search_lgd_location(query):
    if not query or not LGD_VILLAGES:
        return None
    matches = process.extract(
        query.strip(),
        LGD_NAMES,
        scorer=fuzz.WRatio,
        limit=5,
        score_cutoff=85
    )
    for match_name, score, _ in matches:
        for village in LGD_VILLAGES:
            if village["name"] == match_name:
                coordinate = LGD_COORDINATES.get(village["village_code"])
                if coordinate:
                    return {
                        "name": village["name"],
                        "state": "",
                        "country": "IN",
                        "district": village["district"],
                        "subdistrict": village["subdistrict"],
                        "latitude": coordinate["latitude"],
                        "longitude": coordinate["longitude"],
                        "source": "LGD",
                        "score": score
                    }
    return None

def _nominatim_result(result):
    try:
        latitude = float(result["lat"])
        longitude = float(result["lon"])
    except (KeyError, TypeError, ValueError):
        return None

    address = result.get("address", {})
    name = (
        address.get("village")
        or address.get("town")
        or address.get("city")
        or address.get("municipality")
        or address.get("hamlet")
        or address.get("suburb")
        or result.get("name")
        or ""
    )

    return {
        "name": name,
        "state": address.get("state", ""),
        "country": address.get("country_code", "").upper(),
        "district": (
            address.get("state_district")
            or address.get("county")
            or address.get("district")
            or ""
        ),
        "subdistrict": (
            address.get("subdistrict")
            or address.get("municipality")
            or ""
        ),
        "latitude": latitude,
        "longitude": longitude,
        "display_name": result.get("display_name", name),
        "source": "OpenStreetMap"
    }

def search_nominatim(query, state="", country=""):
    if not query:
        return None

    base = query.strip()
    parts = [base]

    if state and state.lower() not in base.lower():
        parts.append(state.strip())

    if country and country.lower() not in base.lower():
        parts.append(country.strip())

    search_variants = [
        ", ".join(parts),
        f"{base}, India",
        f"{base}, Arunachal Pradesh, India"
    ]

    seen = set()

    for search_query in search_variants:
        if search_query.lower() in seen:
            continue
        seen.add(search_query.lower())

        params = {
            "q": search_query,
            "format": "jsonv2",
            "limit": 10,
            "addressdetails": 1,
            "accept-language": "en"
        }

        try:
            response = requests.get(
                NOMINATIM_URL,
                params=params,
                headers=HEADERS,
                timeout=10
            )
            if response.status_code != 200:
                continue
            results = response.json()
        except (requests.RequestException, ValueError):
            continue

        if results:
            for result in results:
                parsed = _nominatim_result(result)
                if parsed:
                    return parsed

    return None

def search_arcgis(query, state="", country=""):
    if not query:
        return None

    parts = [query.strip()]
    if state and state.lower() not in query.lower():
        parts.append(state.strip())
    if country and country.lower() not in query.lower():
        parts.append(country.strip())

    search_query = ", ".join(parts)

    params = {
        "SingleLine": search_query,
        "f": "json",
        "outFields": "*",
        "maxLocations": 10,
        "forStorage": "false"
    }

    try:
        response = requests.get(
            ARCGIS_GEOCODING_URL,
            params=params,
            timeout=10
        )
        if response.status_code != 200:
            return None
        results = response.json().get("candidates", [])
    except (requests.RequestException, ValueError):
        return None

    if not results:
        return None

    for candidate in results:
        location = candidate.get("location", {})
        try:
            latitude = float(location["y"])
            longitude = float(location["x"])
        except (KeyError, TypeError, ValueError):
            continue

        attributes = candidate.get("attributes", {})

        return {
            "name": attributes.get("City") or attributes.get("Match_addr") or query.strip(),
            "state": attributes.get("Region", state),
            "country": attributes.get("Country", country),
            "district": "",
            "subdistrict": "",
            "latitude": latitude,
            "longitude": longitude,
            "display_name": candidate.get("address", search_query),
            "source": "ArcGIS"
        }

    return None

def search_openweather_geocoding(query, state="", country=""):
    if not query or not API_KEY:
        return None

    search_queries = [
        query.strip(),
        ", ".join(
            p for p in [query.strip(), state.strip(), country.strip()]
            if p
        )
    ]

    for search_query in search_queries:
        params = {
            "q": search_query,
            "limit": 10,
            "appid": API_KEY
        }

        try:
            response = requests.get(
                OPENWEATHER_GEOCODING_URL,
                params=params,
                timeout=10
            )
            if response.status_code != 200:
                continue
            results = response.json()
        except (requests.RequestException, ValueError):
            continue

        if not results:
            continue

        for result in results:
            try:
                latitude = float(result["lat"])
                longitude = float(result["lon"])
            except (KeyError, TypeError, ValueError):
                continue

            return {
                "name": result.get("name", query.strip()),
                "state": result.get("state", state),
                "country": result.get("country", country),
                "district": "",
                "subdistrict": "",
                "latitude": latitude,
                "longitude": longitude,
                "source": "OpenWeather"
            }

    return None

def resolve_location(query, state="", country=""):
    query = (query or "").strip()
    state = (state or "").strip()
    country = (country or "").strip()

    if not query:
        return None, "Please enter a location."

    location = search_lgd_location(query)
    if location:
        return location, None

    location = search_nominatim(query, state, country)
    if location:
        return location, None

    location = search_arcgis(query, state, country)
    if location:
        return location, None

    location = search_openweather_geocoding(query, state, country)
    if location:
        return location, None

    return None, (
        f"Could not find coordinates for '{query}'. "
        "Try the village name with its district and state."
    )

def _weather_from_data(data, location):
    main = data.get("main", {})
    wind = data.get("wind", {})
    weather_items = data.get("weather", [])
    condition = weather_items[0].get("description", "") if weather_items else ""

    return {
        "city": location.get("name") or data.get("name", "Unknown"),
        "state": location.get("state", ""),
        "country": location.get("country") or data.get("sys", {}).get("country", ""),
        "district": location.get("district", ""),
        "subdistrict": location.get("subdistrict", ""),
        "temperature": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "humidity": main.get("humidity"),
        "pressure": main.get("pressure"),
        "wind_speed": wind.get("speed"),
        "condition": condition,
        "latitude": location.get("latitude"),
        "longitude": location.get("longitude")
    }

def _forecast_from_data(data):
    forecast = []

    for item in data.get("list", []):
        main = item.get("main", {})
        wind = item.get("wind", {})
        weather_items = item.get("weather", [])
        condition = weather_items[0].get("description", "") if weather_items else ""

        try:
            rain_probability = float(item.get("pop", 0))
        except (TypeError, ValueError):
            rain_probability = 0.0

        forecast.append({
            "datetime": item.get("dt_txt", ""),
            "temperature": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "humidity": main.get("humidity"),
            "wind_speed": wind.get("speed"),
            "condition": condition,
            "rain_probability": rain_probability
        })

    return forecast

def get_weather(location, state="", country=""):
    requested_location = str(location).strip() if location is not None else ""
    place, error = resolve_location(
        requested_location,
        str(state).strip() if state is not None else "",
        str(country).strip() if country is not None else ""
    )
    if error:
        return None, error

    if requested_location:
        place["name"] = requested_location

    params = {
        "lat": place["latitude"],
        "lon": place["longitude"],
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(
            CURRENT_WEATHER_URL,
            params=params,
            timeout=10
        )
    except requests.RequestException:
        return None, "Unable to connect to weather service."

    if response.status_code != 200:
        try:
            message = response.json().get("message", "Unable to get weather information.")
        except ValueError:
            message = "Unable to get weather information."
        return None, f"Weather API error: {message}"

    try:
        data = response.json()
    except ValueError:
        return None, "Invalid response from weather service."

    return _weather_from_data(data, place), None

def get_forecast(location, state="", country=""):
    if isinstance(location, (int, float)) and isinstance(state, (int, float)):
        place = {
            "name": "Selected Location",
            "state": "",
            "country": "",
            "district": "",
            "subdistrict": "",
            "latitude": float(location),
            "longitude": float(state)
        }
        error = None
    else:
        requested_location = str(location).strip() if location is not None else ""
        place, error = resolve_location(
            requested_location,
            str(state).strip() if state is not None else "",
            str(country).strip() if country is not None else ""
        )
        if not error and requested_location:
            place["name"] = requested_location

    if error:
        return None, error

    params = {
        "lat": place["latitude"],
        "lon": place["longitude"],
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(
            FORECAST_URL,
            params=params,
            timeout=10
        )
    except requests.RequestException:
        return None, "Unable to connect to forecast service."

    if response.status_code != 200:
        try:
            message = response.json().get("message", "Unable to get forecast information.")
        except ValueError:
            message = "Unable to get forecast information."
        return None, f"Forecast API error: {message}"

    try:
        data = response.json()
    except ValueError:
        return None, "Invalid forecast response."

    return _forecast_from_data(data), None

def get_weather_by_coordinates(latitude, longitude):
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(
            CURRENT_WEATHER_URL,
            params=params,
            timeout=10
        )
    except requests.RequestException:
        return None, "Unable to connect to weather service."

    if response.status_code != 200:
        return None, "Unable to get weather information."

    try:
        data = response.json()
    except ValueError:
        return None, "Invalid weather response."

    location = {
        "name": data.get("name", "Current Location"),
        "state": "",
        "country": data.get("sys", {}).get("country", ""),
        "district": "",
        "subdistrict": "",
        "latitude": latitude,
        "longitude": longitude
    }

    return _weather_from_data(data, location), None

def get_forecast_by_coordinates(latitude, longitude):
    params = {
        "lat": latitude,
        "lon": longitude,
        "appid": API_KEY,
        "units": "metric"
    }

    try:
        response = requests.get(
            FORECAST_URL,
            params=params,
            timeout=10
        )
    except requests.RequestException:
        return None, "Unable to connect to forecast service."

    if response.status_code != 200:
        return None, "Unable to get forecast information."

    try:
        data = response.json()
    except ValueError:
        return None, "Invalid forecast response."

    return _forecast_from_data(data), None
