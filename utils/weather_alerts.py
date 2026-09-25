def generate_weather_alerts(forecast):

    alerts = []

    if not forecast:
        return alerts

    for item in forecast:

        temperature = item["temperature"]
        wind_speed = item["wind_speed"]
        rain_probability = item["rain_probability"]
        condition = item["condition"].lower()
        datetime = item["datetime"]

        # Heavy rain alert
        if rain_probability >= 0.70:
            alerts.append({
                "type": "🌧️ Heavy Rain Alert",
                "datetime": datetime,
                "message": (
                    f"High chance of rain ({rain_probability * 100:.0f}%). "
                    "Carry an umbrella and plan outdoor activities carefully."
                )
            })

        # High temperature alert
        if temperature >= 40:
            alerts.append({
                "type": "🌡️ High Temperature Alert",
                "datetime": datetime,
                "message": (
                    f"Temperature may reach {temperature} °C. "
                    "Stay hydrated and avoid prolonged exposure to heat."
                )
            })

        # Strong wind alert
        if wind_speed >= 15:
            alerts.append({
                "type": "💨 Strong Wind Alert",
                "datetime": datetime,
                "message": (
                    f"Wind speed may reach {wind_speed} m/s. "
                    "Take care outdoors and secure loose objects."
                )
            })

        # Thunderstorm alert
        if (
            "thunderstorm" in condition
            or "storm" in condition
        ):
            alerts.append({
                "type": "⛈️ Thunderstorm Alert",
                "datetime": datetime,
                "message": (
                    "Thunderstorm conditions are forecast. "
                    "Avoid exposed outdoor areas during the storm."
                )
            })

        # Snow alert
        if "snow" in condition:
            alerts.append({
                "type": "❄️ Snow Alert",
                "datetime": datetime,
                "message": (
                    "Snow is forecast during this period. "
                    "Take appropriate precautions while travelling."
                )
            })

    return alerts