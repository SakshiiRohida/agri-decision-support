
import json
from pathlib import Path

DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "crop_catalog.json"
)


def load_crops():
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def range_score(value, minimum, maximum):
    if minimum <= value <= maximum:
        return 100.0

    if value < minimum:
        distance = minimum - value
    else:
        distance = value - maximum

    width = max(maximum - minimum, 1)
    return max(0.0, 100.0 - (distance / width) * 100.0)


def recommend_crops(season, temperature, rainfall=None):
    results = []

    for crop in load_crops():
        if season not in crop["seasons"]:
            continue

        temp_score = range_score(
            temperature,
            crop["temperature_min"],
            crop["temperature_max"],
        )

        if rainfall is None:
            # Location-based prototype: do not compare short-term
            # forecast rainfall with seasonal rainfall requirements.
            score = temp_score
            rain_score = None
            reasons = [
                (
                    "Temperature is within the catalogue range."
                    if temp_score == 100
                    else "Temperature is outside the catalogue range."
                ),
                (
                    "Rainfall suitability has not been assessed; "
                    "longer-term local rainfall data is needed."
                ),
            ]
        else:
            rain_score = range_score(
                rainfall,
                crop["rainfall_min"],
                crop["rainfall_max"],
            )
            score = round((temp_score + rain_score) / 2, 1)
            reasons = [
                (
                    "Temperature is within the catalogue range."
                    if temp_score == 100
                    else "Temperature is outside the catalogue range."
                ),
                (
                    "Rainfall is within the catalogue range."
                    if rain_score == 100
                    else "Rainfall is outside the catalogue range."
                ),
            ]

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
