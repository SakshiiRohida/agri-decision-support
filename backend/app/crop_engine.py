
import json
from pathlib import Path


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "crop_catalog.json"
)


def load_crops():
    """Load the crop catalogue."""
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def range_score(value, minimum, maximum):
    """Calculate a simple score against a configured range."""
    if minimum <= value <= maximum:
        return 100.0

    distance = (
        minimum - value
        if value < minimum
        else value - maximum
    )
    width = max(maximum - minimum, 1)

    return max(0.0, 100.0 - (distance / width) * 100.0)


def recommend_crops(season, temperature, rainfall=None):
    """Legacy catalogue-based recommendation function."""
    results = []

    for crop in load_crops():
        if season not in crop["seasons"]:
            continue

        temp_score = range_score(
            temperature,
            crop["temperature_min"],
            crop["temperature_max"],
        )

        rain_score = None
        score = temp_score

        reasons = [
            (
                "Temperature matches the catalogue range."
                if temp_score == 100
                else "Temperature is outside the catalogue range."
            )
        ]

        if rainfall is None:
            reasons.append(
                "Rainfall suitability has not been assessed."
            )
        else:
            rain_score = range_score(
                rainfall,
                crop["rainfall_min"],
                crop["rainfall_max"],
            )
            score = round((temp_score + rain_score) / 2, 1)
            reasons.append(
                "Rainfall was compared with the catalogue range."
            )

        results.append({
            "crop": crop["name"],
            "suitability_score": round(score, 1),
            "temperature_score": round(temp_score, 1),
            "rainfall_score": (
                round(rain_score, 1)
                if rain_score is not None
                else None
            ),
            "reasons": reasons,
        })

    return sorted(
        results,
        key=lambda item: item["suitability_score"],
        reverse=True,
    )


def recommend_from_weather(season, weather_data):
    """
    Generate preliminary suggestions from current and forecast
    temperatures, filtered by the selected season.

    This does not use the trained Random Forest model.
    """
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})

    current_temp = current.get("temperature_2m")

    if not isinstance(current_temp, (int, float)):
        raise ValueError("Current temperature is unavailable.")

    forecast_temps = []

    for key in ("temperature_2m_max", "temperature_2m_min"):
        values = daily.get(key, [])
        if isinstance(values, list):
            forecast_temps.extend(
                value
                for value in values
                if isinstance(value, (int, float))
            )

    temperatures = [current_temp] + forecast_temps
    results = []

    for crop in load_crops():
        if season not in crop.get("seasons", []):
            continue

        minimum = crop["temperature_min"]
        maximum = crop["temperature_max"]

        scores = [
            range_score(value, minimum, maximum)
            for value in temperatures
        ]

        score = round(sum(scores) / len(scores), 1)

        results.append({
            "crop": crop["name"],
            "suitability_score": score,
            "temperature_score": score,
            "rainfall_score": None,
            "reasons": [
                (
                    "Current and available forecast temperatures "
                    "were compared with the crop catalogue range."
                ),
                (
                    "Soil nutrients, soil pH, seasonal rainfall "
                    "suitability and irrigation have not been assessed."
                ),
            ],
            "method": "Preliminary temperature-range heuristic",
        })

    return sorted(
        results,
        key=lambda item: item["suitability_score"],
        reverse=True,
    )


def build_weather_advisories(weather_data):
    """Extract weather information without inventing crop thresholds."""
    current = weather_data.get("current", {})
    daily = weather_data.get("daily", {})

    rainfall = daily.get("precipitation_sum", [])
    rain_probability = daily.get(
        "precipitation_probability_max", []
    )
    max_wind = daily.get("wind_speed_10m_max", [])

    valid_rainfall = [
        value for value in rainfall
        if isinstance(value, (int, float))
    ]
    valid_probability = [
        value for value in rain_probability
        if isinstance(value, (int, float))
    ]
    valid_wind = [
        value for value in max_wind
        if isinstance(value, (int, float))
    ]

    return {
        "current_temperature_c": current.get("temperature_2m"),
        "feels_like_temperature_c": current.get(
            "apparent_temperature"
        ),
        "current_humidity_percent": current.get(
            "relative_humidity_2m"
        ),
        "current_rain_mm": current.get("rain"),
        "current_wind_speed_kmh": current.get("wind_speed_10m"),
        "current_wind_gusts_kmh": current.get("wind_gusts_10m"),
        "forecast_rainfall_total_mm": (
            round(sum(valid_rainfall), 1)
            if valid_rainfall else None
        ),
        "forecast_rain_probability_max_percent": (
            max(valid_probability)
            if valid_probability else None
        ),
        "forecast_max_wind_speed_kmh": (
            max(valid_wind) if valid_wind else None
        ),
        "notice": (
            "These are weather indicators, not soil measurements "
            "or validated crop-specific farming advice."
        ),
    }
