from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
import webbrowser
from threading import Timer

app = Flask(__name__)


# ============================================================
# OPEN-METEO API
# ============================================================

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


# ============================================================
# WEATHER CODE MAPPING
# WMO WEATHER CODES
# ============================================================

WEATHER_CODES = {
    0: {"main": "Clear", "description": "Clear sky", "icon": "☀️"},
    1: {"main": "Clear", "description": "Mainly clear", "icon": "🌤️"},
    2: {"main": "Clouds", "description": "Partly cloudy", "icon": "⛅"},
    3: {"main": "Clouds", "description": "Overcast", "icon": "☁️"},
    45: {"main": "Fog", "description": "Fog", "icon": "🌫️"},
    48: {"main": "Fog", "description": "Depositing rime fog", "icon": "🌫️"},
    51: {"main": "Drizzle", "description": "Light drizzle", "icon": "🌦️"},
    53: {"main": "Drizzle", "description": "Moderate drizzle", "icon": "🌦️"},
    55: {"main": "Drizzle", "description": "Dense drizzle", "icon": "🌧️"},
    56: {
        "main": "Freezing Drizzle",
        "description": "Light freezing drizzle",
        "icon": "🌧️",
    },
    57: {
        "main": "Freezing Drizzle",
        "description": "Dense freezing drizzle",
        "icon": "🌧️",
    },
    61: {"main": "Rain", "description": "Slight rain", "icon": "🌦️"},
    63: {"main": "Rain", "description": "Moderate rain", "icon": "🌧️"},
    65: {"main": "Rain", "description": "Heavy rain", "icon": "🌧️"},
    66: {"main": "Freezing Rain", "description": "Light freezing rain", "icon": "🌧️"},
    67: {"main": "Freezing Rain", "description": "Heavy freezing rain", "icon": "🌧️"},
    71: {"main": "Snow", "description": "Slight snowfall", "icon": "🌨️"},
    73: {"main": "Snow", "description": "Moderate snowfall", "icon": "❄️"},
    75: {"main": "Snow", "description": "Heavy snowfall", "icon": "❄️"},
    77: {"main": "Snow", "description": "Snow grains", "icon": "❄️"},
    80: {"main": "Rain", "description": "Slight rain showers", "icon": "🌦️"},
    81: {"main": "Rain", "description": "Moderate rain showers", "icon": "🌧️"},
    82: {"main": "Rain", "description": "Violent rain showers", "icon": "⛈️"},
    85: {"main": "Snow", "description": "Slight snow showers", "icon": "🌨️"},
    86: {"main": "Snow", "description": "Heavy snow showers", "icon": "❄️"},
    95: {"main": "Thunderstorm", "description": "Thunderstorm", "icon": "⛈️"},
    96: {
        "main": "Thunderstorm",
        "description": "Thunderstorm with slight hail",
        "icon": "⛈️",
    },
    99: {
        "main": "Thunderstorm",
        "description": "Thunderstorm with heavy hail",
        "icon": "⛈️",
    },
}


def get_weather_info(code):
    """
    Convert Open-Meteo WMO weather code
    into readable weather information.
    """

    return WEATHER_CODES.get(
        int(code), {"main": "Unknown", "description": "Unknown weather", "icon": "🌍"}
    )


# ============================================================
# CITY GEOCODING
# ============================================================


def get_city_coordinates(city):

    try:

        params = {"name": city, "count": 1, "language": "en", "format": "json"}

        response = requests.get(GEOCODING_URL, params=params, timeout=10)

        if response.status_code != 200:
            return None

        data = response.json()

        results = data.get("results", [])

        if not results:
            return None

        location = results[0]

        return {
            "name": location.get("name", city),
            "country": location.get("country", ""),
            "country_code": location.get("country_code", ""),
            "latitude": location.get("latitude"),
            "longitude": location.get("longitude"),
            "timezone": location.get("timezone", "auto"),
            "admin1": location.get("admin1", ""),
        }

    except requests.exceptions.Timeout:

        print("Geocoding timeout")

        return None

    except requests.exceptions.ConnectionError:

        print("Geocoding connection error")

        return None

    except Exception as e:

        print("Geocoding error:", e)

        return None


# ============================================================
# WEATHER INSIGHTS
# ============================================================


def generate_insights(current, daily):

    insights = []

    temperature = current.get("temperature", 0)
    feels_like = current.get("feels_like", 0)
    humidity = current.get("humidity", 0)
    wind_speed = current.get("wind_speed", 0)
    rain_probability = current.get("rain_probability", 0)
    uv_index = current.get("uv_index", 0)
    visibility = current.get("visibility", 0)
    weather_main = current.get("weather_main", "")

    # Temperature
    if temperature >= 35:

        insights.append(
            {
                "type": "warning",
                "title": "Very hot",
                "message": "High temperature detected. Stay hydrated and avoid prolonged direct sunlight.",
            }
        )

    elif temperature >= 30:

        insights.append(
            {
                "type": "info",
                "title": "Warm weather",
                "message": "It is warm outside. Drink enough water and consider light clothing.",
            }
        )

    elif temperature <= 10:

        insights.append(
            {
                "type": "info",
                "title": "Cold weather",
                "message": "Temperatures are low. Consider wearing warm clothing.",
            }
        )

    else:

        insights.append(
            {
                "type": "success",
                "title": "Comfortable temperature",
                "message": "The current temperature is relatively comfortable.",
            }
        )

    # Rain
    if rain_probability >= 70:

        insights.append(
            {
                "type": "warning",
                "title": "High rain chance",
                "message": f"There is a {rain_probability}% chance of precipitation. Carry an umbrella.",
            }
        )

    elif rain_probability >= 40:

        insights.append(
            {
                "type": "info",
                "title": "Possible rain",
                "message": f"Rain is possible today with approximately {rain_probability}% probability.",
            }
        )

    # Humidity
    if humidity >= 80:

        insights.append(
            {
                "type": "info",
                "title": "High humidity",
                "message": "Humidity is high. The temperature may feel warmer than it actually is.",
            }
        )

    elif humidity <= 30:

        insights.append(
            {
                "type": "info",
                "title": "Dry air",
                "message": "Humidity is relatively low. Stay hydrated.",
            }
        )

    # Wind
    if wind_speed >= 40:

        insights.append(
            {
                "type": "warning",
                "title": "Strong winds",
                "message": "Strong winds are currently expected. Take care when outdoors.",
            }
        )

    elif wind_speed >= 25:

        insights.append(
            {
                "type": "info",
                "title": "Windy",
                "message": "Moderately strong winds are present.",
            }
        )

    # UV
    if uv_index >= 8:

        insights.append(
            {
                "type": "warning",
                "title": "Very high UV",
                "message": "UV levels are high. Sunscreen, sunglasses and shade are recommended.",
            }
        )

    elif uv_index >= 5:

        insights.append(
            {
                "type": "info",
                "title": "Moderate UV",
                "message": "Consider sun protection when staying outdoors for a long time.",
            }
        )

    # Visibility
    if visibility < 2:

        insights.append(
            {
                "type": "warning",
                "title": "Low visibility",
                "message": "Visibility is low. Exercise extra caution while driving.",
            }
        )

    # Weather condition
    if weather_main == "Thunderstorm":

        insights.append(
            {
                "type": "warning",
                "title": "Thunderstorm",
                "message": "Thunderstorm conditions are present. Avoid exposed outdoor areas.",
            }
        )

    elif weather_main == "Rain":

        insights.append(
            {
                "type": "info",
                "title": "Rain expected",
                "message": "Wet conditions are present. Carry suitable rain protection.",
            }
        )

    # Forecast trend
    if daily and len(daily) >= 2:

        tomorrow = daily[1]

        today_max = daily[0]["max_temp"]
        tomorrow_max = tomorrow["max_temp"]

        difference = tomorrow_max - today_max

        if difference >= 3:

            insights.append(
                {
                    "type": "info",
                    "title": "Warming trend",
                    "message": "Tomorrow is expected to be warmer than today.",
                }
            )

        elif difference <= -3:

            insights.append(
                {
                    "type": "info",
                    "title": "Cooling trend",
                    "message": "Tomorrow is expected to be cooler than today.",
                }
            )

    return insights


# ============================================================
# WEATHER DATA BY COORDINATES
# ============================================================


def get_weather_by_coordinates(
    latitude, longitude, city_name="Your Location", country=""
):

    try:

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "is_day,"
                "precipitation,"
                "rain,"
                "showers,"
                "snowfall,"
                "weather_code,"
                "cloud_cover,"
                "pressure_msl,"
                "surface_pressure,"
                "wind_speed_10m,"
                "wind_direction_10m"
            ),
            "hourly": (
                "temperature_2m,"
                "relative_humidity_2m,"
                "apparent_temperature,"
                "precipitation_probability,"
                "precipitation,"
                "weather_code,"
                "cloud_cover,"
                "visibility,"
                "wind_speed_10m,"
                "wind_direction_10m"
            ),
            "daily": (
                "weather_code,"
                "temperature_2m_max,"
                "temperature_2m_min,"
                "sunrise,"
                "sunset,"
                "uv_index_max,"
                "precipitation_probability_max,"
                "precipitation_sum"
            ),
            "forecast_days": 7,
            "timezone": "auto",
        }

        response = requests.get(FORECAST_URL, params=params, timeout=15)

        if response.status_code != 200:

            print("Open-Meteo error:", response.text)

            return {"success": False, "error": "Unable to load weather data."}

        data = response.json()

        current = data.get("current", {})
        hourly_data = data.get("hourly", {})
        daily_data = data.get("daily", {})

        # ----------------------------------------------------
        # CURRENT WEATHER
        # ----------------------------------------------------

        weather_code = current.get("weather_code", 0)

        weather_info = get_weather_info(weather_code)

        current_temperature = round(current.get("temperature_2m", 0), 1)

        feels_like = round(current.get("apparent_temperature", current_temperature), 1)

        humidity = current.get("relative_humidity_2m", 0)

        wind_speed = round(current.get("wind_speed_10m", 0), 1)

        wind_direction = current.get("wind_direction_10m", 0)

        clouds = current.get("cloud_cover", 0)

        pressure = round(current.get("pressure_msl", 0), 1)

        # ----------------------------------------------------
        # FIND CURRENT HOURLY INDEX
        # ----------------------------------------------------

        hourly_times = hourly_data.get("time", [])

        current_time = current.get("time", "")

        current_index = 0

        if current_time in hourly_times:

            current_index = hourly_times.index(current_time)

        # ----------------------------------------------------
        # CURRENT VISIBILITY
        # ----------------------------------------------------

        hourly_visibility = hourly_data.get("visibility", [])

        if hourly_visibility:

            visibility_meters = hourly_visibility[
                min(current_index, len(hourly_visibility) - 1)
            ]

            visibility = round(visibility_meters / 1000, 1)

        else:

            visibility = 10

        # ----------------------------------------------------
        # RAIN PROBABILITY
        # ----------------------------------------------------

        rain_probabilities = hourly_data.get("precipitation_probability", [])

        if rain_probabilities:

            rain_probability = rain_probabilities[
                min(current_index, len(rain_probabilities) - 1)
            ]

        else:

            rain_probability = 0

        # ----------------------------------------------------
        # DAILY FORECAST
        # ----------------------------------------------------

        forecast_days = []

        daily_times = daily_data.get("time", [])

        daily_codes = daily_data.get("weather_code", [])

        daily_max = daily_data.get("temperature_2m_max", [])

        daily_min = daily_data.get("temperature_2m_min", [])

        daily_uv = daily_data.get("uv_index_max", [])

        daily_rain_probability = daily_data.get("precipitation_probability_max", [])

        daily_rain = daily_data.get("precipitation_sum", [])

        daily_sunrise = daily_data.get("sunrise", [])

        daily_sunset = daily_data.get("sunset", [])

        for i in range(min(7, len(daily_times))):

            code = daily_codes[i]

            info = get_weather_info(code)

            date_object = datetime.strptime(daily_times[i], "%Y-%m-%d")

            if i < len(daily_uv):

                uv_value = round(daily_uv[i], 1)

            else:

                uv_value = 0

            if i < len(daily_rain_probability):

                rain_value = daily_rain_probability[i]

            else:

                rain_value = 0

            if i < len(daily_rain):

                precipitation = round(daily_rain[i], 1)

            else:

                precipitation = 0

            if i < len(daily_sunrise):

                sunrise = datetime.fromisoformat(daily_sunrise[i]).strftime("%H:%M")

            else:

                sunrise = ""

            if i < len(daily_sunset):

                sunset = datetime.fromisoformat(daily_sunset[i]).strftime("%H:%M")

            else:

                sunset = ""

            forecast_days.append(
                {
                    "date": date_object.strftime("%a, %d %b"),
                    "full_date": daily_times[i],
                    "min_temp": round(daily_min[i], 1),
                    "max_temp": round(daily_max[i], 1),
                    "description": info["description"],
                    "main": info["main"],
                    "icon": info["icon"],
                    "weather_code": code,
                    "rain_probability": rain_value,
                    "precipitation": precipitation,
                    "uv_index": uv_value,
                    "sunrise": sunrise,
                    "sunset": sunset,
                }
            )

        # ----------------------------------------------------
        # HOURLY FORECAST
        # ----------------------------------------------------

        hourly = []

        hourly_temperatures = hourly_data.get("temperature_2m", [])

        hourly_feels = hourly_data.get("apparent_temperature", [])

        hourly_humidity = hourly_data.get("relative_humidity_2m", [])

        hourly_codes = hourly_data.get("weather_code", [])

        hourly_wind = hourly_data.get("wind_speed_10m", [])

        hourly_rain = hourly_data.get("precipitation_probability", [])

        hourly_clouds = hourly_data.get("cloud_cover", [])

        # Start from current hour
        start = current_index

        end = min(start + 24, len(hourly_times))

        for i in range(start, end):

            code = hourly_codes[i]

            info = get_weather_info(code)

            time_object = datetime.fromisoformat(hourly_times[i])

            hourly.append(
                {
                    "time": time_object.strftime("%H:%M"),
                    "date": hourly_times[i],
                    "temperature": round(hourly_temperatures[i], 1),
                    "feels_like": round(hourly_feels[i], 1),
                    "humidity": hourly_humidity[i],
                    "wind": round(hourly_wind[i], 1),
                    "rain_probability": (hourly_rain[i] if i < len(hourly_rain) else 0),
                    "clouds": (hourly_clouds[i] if i < len(hourly_clouds) else 0),
                    "icon": info["icon"],
                    "description": info["description"],
                    "main": info["main"],
                    "weather_code": code,
                }
            )

        # ----------------------------------------------------
        # TODAY SUNRISE / SUNSET
        # ----------------------------------------------------

        sunrise = ""

        sunset = ""

        if daily_sunrise:

            sunrise = datetime.fromisoformat(daily_sunrise[0]).strftime("%H:%M")

        if daily_sunset:

            sunset = datetime.fromisoformat(daily_sunset[0]).strftime("%H:%M")

        # ----------------------------------------------------
        # UV INDEX
        # ----------------------------------------------------

        if daily_uv:

            uv_index = round(daily_uv[0], 1)

        else:

            uv_index = 0

        # ----------------------------------------------------
        # CURRENT OBJECT
        # ----------------------------------------------------

        current_object = {
            "temperature": current_temperature,
            "feels_like": feels_like,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "clouds": clouds,
            "pressure": pressure,
            "visibility": visibility,
            "rain_probability": rain_probability,
            "uv_index": uv_index,
            "weather_main": weather_info["main"],
        }

        # ----------------------------------------------------
        # WEATHER INSIGHTS
        # ----------------------------------------------------

        insights = generate_insights(current_object, forecast_days)

        # ----------------------------------------------------
        # FINAL RESPONSE
        # ----------------------------------------------------

        result = {
            "success": True,
            "city": city_name,
            "country": country,
            "coordinates": {"lat": latitude, "lon": longitude},
            "temperature": current_temperature,
            "feels_like": feels_like,
            "temp_min": (round(daily_min[0], 1) if daily_min else current_temperature),
            "temp_max": (round(daily_max[0], 1) if daily_max else current_temperature),
            "humidity": humidity,
            "pressure": pressure,
            "visibility": visibility,
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "clouds": clouds,
            "rain_probability": rain_probability,
            "uv_index": uv_index,
            "precipitation": (round(daily_rain[0], 1) if daily_rain else 0),
            "description": weather_info["description"],
            "weather_main": weather_info["main"],
            "icon": weather_info["icon"],
            "weather_code": weather_code,
            "sunrise": sunrise,
            "sunset": sunset,
            "forecast": forecast_days,
            "hourly": hourly,
            "insights": insights,
        }

        return result

    except requests.exceptions.Timeout:

        return {"success": False, "error": "Weather service timed out. Try again."}

    except requests.exceptions.ConnectionError:

        return {"success": False, "error": "Internet connection problem."}

    except Exception as e:

        print("WEATHER ERROR:", e)

        return {
            "success": False,
            "error": "Something went wrong while loading weather.",
        }


# ============================================================
# CITY WEATHER
# ============================================================


def get_weather(city):

    location = get_city_coordinates(city)

    if not location:

        return {"success": False, "error": f"City '{city}' was not found."}

    return get_weather_by_coordinates(
        location["latitude"],
        location["longitude"],
        location["name"],
        location["country"],
    )


# ============================================================
# HOME
# ============================================================


@app.route("/", methods=["GET"])
def home():

    return render_template("index.html")


# ============================================================
# WEATHER BY CITY
# ============================================================


@app.route("/weather", methods=["POST"])
def weather():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({"success": False, "error": "Invalid request."}), 400

    city = data.get("city", "").strip()

    if not city:

        return jsonify({"success": False, "error": "Please enter a city name."}), 400

    result = get_weather(city)

    return jsonify(result)


# ============================================================
# WEATHER BY GPS LOCATION
# ============================================================


@app.route("/weather/location", methods=["POST"])
def weather_location():

    data = request.get_json(silent=True)

    if not data:

        return jsonify({"success": False, "error": "Location data missing."}), 400

    latitude = data.get("lat")

    longitude = data.get("lon")

    if latitude is None or longitude is None:

        return (
            jsonify(
                {"success": False, "error": "Latitude and longitude are required."}
            ),
            400,
        )

    try:

        latitude = float(latitude)

        longitude = float(longitude)

    except ValueError:

        return jsonify({"success": False, "error": "Invalid coordinates."}), 400

    result = get_weather_by_coordinates(latitude, longitude, "Your Location", "")

    return jsonify(result)


# ============================================================
# BROWSER AUTO OPEN
# ============================================================


def open_browser():

    webbrowser.open_new("http://127.0.0.1:5000/")


# ============================================================
# RUN FLASK
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 60)
    print("🌦️  ADVANCED 3D WEATHER FORECAST")
    print("=" * 60)
    print()
    print("API: Open-Meteo")
    print("API Key: NOT REQUIRED")
    print()
    print("Server:")
    print("http://127.0.0.1:5000/")
    print()
    print("=" * 60)
    print()

    Timer(1, open_browser).start()

    app.run(debug=True, host="127.0.0.1", port=5000)
