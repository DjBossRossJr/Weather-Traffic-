#!/usr/bin/env python3

import requests
import os
from gtts import gTTS

ALERT_FILE = "last_alert.txt"

HEADERS = {
    "User-Agent": "Delaware All Saints Gospel Radio Emergency Alerts"
}

ALERT_TYPES = [
    "Tornado Warning",
    "Severe Thunderstorm Warning",
    "Flash Flood Warning",
    "Flood Warning",
    "Hurricane Warning",
    "Tropical Storm Warning",
    "Winter Storm Warning",
    "Blizzard Warning",
    "Ice Storm Warning",
    "Excessive Heat Warning",
    "Extreme Cold Warning",
    "Wind Advisory",
    "Dense Fog Advisory",
    "Coastal Flood Advisory",
    "Special Weather Statement"
]


def get_alerts():

    url = "https://api.weather.gov/alerts/active?area=DE"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=15
    )

    response.raise_for_status()

    return response.json()["features"]


def get_last_alert():

    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, "r") as f:
            return f.read()

    return ""


def save_alert(alert):

    with open(ALERT_FILE, "w") as f:
        f.write(alert)


def create_audio(message):

    filename = "emergency_alert.mp3"

    voice = gTTS(
        text=message,
        lang="en"
    )

    voice.save(filename)

    print("Created:", filename)


def main():

    alerts = get_alerts()

    for alert in alerts:

        title = alert["properties"]["event"]

        if title in ALERT_TYPES:

            headline = alert["properties"]["headline"]
            description = alert["properties"]["description"]

            alert_id = headline

            last = get_last_alert()

            if alert_id != last:

                message = (
                    "Emergency weather update from "
                    "Delaware All Saints Gospel Radio. "
                    f"{headline}. "
                    f"{description}. "
                    "Please take precautions and stay safe."
                )

                create_audio(message)

                save_alert(alert_id)

                return

    print("No new alerts.")


if __name__ == "__main__":
    main()
