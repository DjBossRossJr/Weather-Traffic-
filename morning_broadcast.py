#!/usr/bin/env python3

import datetime
import requests
from gtts import gTTS

STATION = "Delaware All Saints Gospel Radio"


def get_weather():

    headers = {
        "User-Agent": "Delaware All Saints Gospel Radio automation"
    }

    points_url = (
        "https://api.weather.gov/points/"
        "39.6837,-75.7497"
    )

    points_response = requests.get(
        points_url,
        headers=headers,
        timeout=15
    )

    points_response.raise_for_status()

    points = points_response.json()

    forecast_url = points["properties"]["forecast"]

    forecast_response = requests.get(
        forecast_url,
        headers=headers,
        timeout=15
    )

    forecast_response.raise_for_status()

    forecast = forecast_response.json()

    period = forecast["properties"]["periods"][0]

    return {
        "temp": period["temperature"],
        "condition": period["shortForecast"],
        "wind": period["windSpeed"]
    }


def weather_report(weather):

    return (
        f"Here is your Delaware forecast. "
        f"Temperatures are {weather['temp']} degrees "
        f"with {weather['condition']}. "
        f"Winds are {weather['wind']}."
    )


def traffic_report():

    return (
        "Traffic update for Delaware. "
        "Monitoring Interstate 95, the Delaware Memorial Bridge, "
        "Route 1, and Wilmington area travel. "
        "Please drive safely."
    )


def gospel_inspiration():

    return (
        "Today's inspiration comes from Isaiah chapter forty-one verse ten. "
        "Fear not, for I am with you. "
        "God is with you through every challenge. "
        "Stay encouraged and walk in faith."
    )


def build_script(weather):

    today = datetime.datetime.now().strftime(
        "%A, %B %d"
    )

    return (
        f"Good morning from {STATION}. "
        f"Broadcasting from Delaware to listeners around the world. "
        f"Where Praise Lives. "

        f"Today is {today}. "

        f"{weather_report(weather)} "

        f"{traffic_report()} "

        f"{gospel_inspiration()} "

        f"Thank you for starting your day with "
        f"{STATION}. "
        f"Stay blessed and keep it right here."
    )


def create_audio(script):

    filename = (
        f"delaware_all_saints_"
        f"{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.mp3"
    )

    voice = gTTS(
        text=script,
        lang="en",
        slow=False
    )

    voice.save(filename)

    print(f"Created {filename}")

def main():

    print("Starting Delaware All Saints Global Morning Broadcast")

    weather = get_weather()

    script = build_script(weather)

    print(script)

    create_audio(script)

    print("Broadcast completed successfully")


if __name__ == "__main__":
    main()
