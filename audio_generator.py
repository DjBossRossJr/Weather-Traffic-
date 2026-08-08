#!/usr/bin/env python3

import requests
from gtts import gTTS

STATION = "Delaware All Saints Gospel Radio"
OUTPUT_FILE = "delaware_all_saints_update.mp3"

HEADERS = {
    "User-Agent": "Delaware All Saints Gospel Radio"
}


def get_weather():
    points_url = "https://api.weather.gov/points/39.6837,-75.7497"

    response = requests.get(
        points_url,
        headers=HEADERS,
        timeout=15
    )
    response.raise_for_status()

    points = response.json()
    forecast_url = points["properties"]["forecast"]

    forecast_response = requests.get(
        forecast_url,
        headers=HEADERS,
        timeout=15
    )
    forecast_response.raise_for_status()

    periods = forecast_response.json()["properties"]["periods"]

    if not periods:
        raise RuntimeError("No weather forecast periods were returned.")

    period = periods[0]

    return (
        f"Temperature {period['temperature']} degrees. "
        f"{period['shortForecast']}. "
        f"Winds {period['windSpeed']}."
    )


def create_broadcast():
    weather = get_weather()

    script = (
        f"You're listening to {STATION}. "
        "Where Praise Lives. "
        "This is your Delaware weather and traffic update. "
        f"{weather} "
        "Traffic is being monitored on Interstate 95, "
        "Route 1, and the Delaware Memorial Bridge. "
        "Please travel safely. "
        "Remember Isaiah chapter forty-one verse ten. "
        "Fear not, for I am with you. "
        "Stay blessed and keep listening."
    )

    voice = gTTS(
        text=script,
        lang="en"
    )

    voice.save(OUTPUT_FILE)

    print(f"Created: {OUTPUT_FILE}")


if __name__ == "__main__":
    create_broadcast()
