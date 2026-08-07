#!/usr/bin/env python3

import datetime
import requests
from gtts import gTTS

STATION = "Delaware All Saints Gospel Radio"


def get_weather():

    headers = {
        "User-Agent": "Delaware All Saints Gospel Radio"
    }

    url = "https://api.weather.gov/points/39.6837,-75.7497"

    data = requests.get(
        url,
        headers=headers,
        timeout=15
    ).json()

    forecast_url = data["properties"]["forecast"]

    forecast = requests.get(
        forecast_url,
        headers=headers,
        timeout=15
    ).json()

    period = forecast["properties"]["periods"][0]

    return (
        f"Temperature {period['temperature']} degrees. "
        f"{period['shortForecast']}. "
        f"Winds {period['windSpeed']}."
    )


def create_broadcast():

    now = datetime.datetime.now()

    weather = get_weather()

    script = (
        f"You're listening to {STATION}. "
        "Where Praise Lives. "
        f"This is your Delaware weather and traffic update. "
        f"{weather} "
        "Traffic is being monitored on Interstate 95, "
        "Route 1, and the Delaware Memorial Bridge. "
        "Please travel safely. "
        "Remember Isaiah chapter forty-one verse ten. "
        "Fear not, for I am with you. "
        "Stay blessed and keep listening."
    )

    filename = "delaware_all_saints_update.mp3"

    tts = gTTS(
        text=script,
        lang="en"
    )

    tts.save(filename)

    print("Created:", filename)


if __name__ == "__main__":
    create_broadcast()
