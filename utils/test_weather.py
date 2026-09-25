from weather_api import get_weather

weather = get_weather("Hyderabad")

if weather:
    print("Weather information:")
    print(weather)
else:
    print("Unable to get weather information.")