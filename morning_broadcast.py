#!/usr/bin/env python3

import os
import datetime
import requests
from gtts import gTTS

STATION = "Delaware All Saints Gospel Radio"
LOCATION = "Newark,DE"

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")


def get_weather():
    url = (
        "https://api.weatherapi.com/v1/current.json?"
        f"key={WEATHER_API_KEY}&q={LOCATION}"
    )

    response = requests.get(url, timeout=10)

    print("Weather API status:", response.status_code)
    print("Weather API response:", response.text[:500])

    data = response.json()

    if "current" not in data:
        raise Exception(f"Weather API returned an error: {data}")

    return {
        "temp": data["current"]["temp_f"],
        "condition": data["current"]["condition"]["text"],
        "wind": data["current"]["wind_mph"],
        "humidity": data["current"]["humidity"]
    }

def traffic_report():
    return (
        "For our listeners traveling through Delaware, "
        "traffic is being monitored across Interstate 95, "
        "the Delaware Memorial Bridge, Route 1, and the Wilmington area. "
        "Please allow extra travel time and drive safely."
    )


def gospel_inspiration():

    return (
        "Today's scripture comes from Isaiah chapter forty-one, verse ten. "
        "Fear not, for I am with you; be not dismayed, for I am your God. "
        "Wherever you are listening around the world today, remember "
        "that God's love and mercy reach every nation. "
        "Walk in faith, stay encouraged, and know that you are never alone."
    )


def build_script(weather):

    today = datetime.datetime.now().strftime(
        "%A, %B %d"
    )

    return (
        f"Good morning, good afternoon, and good evening "
        f"to our listeners around the world. "

        f"You are listening to {STATION}, "
        f"broadcasting from Delaware to the nations. "
        f"Where Praise Lives. "

        f"Today is {today}. "

        f"{weather_report(weather)} "

        f"{traffic_report()} "

        f"{gospel_inspiration()} "

        f"Thank you for starting your day with "
        f"{STATION}. "
        f"Stay blessed, keep the faith, and keep it right here."
    )


def create_audio(script):

    filename = "delaware_all_saints_global_morning.mp3"

    voice = gTTS(
        text=script,
        lang="en",
        slow=False
    )

    voice.save(filename)

    print(f"Created {filename}")


def main():

    print("Starting Global Morning Update")

    weather = get_weather()

    script = build_script(weather)

    print(script)

    create_audio(script)


if __name__ == "__main__":
    main()
