#!/usr/bin/env python3

import os
import requests
from gtts import gTTS

ALERT_FILE = "last_alert.txt"
OUTPUT_FILE = "emergency_alert.mp3"

HEADERS = {
    "User-Agent": "Delaware All Saints Gospel Radio Emergency Alerts"
}

ALERT_TYPES = {
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
    "Special Weather Statement",
}


def get_alerts():
    url = "https://api.weather.gov/alerts/active?area=DE"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=15
    )

    response.raise_for_status()

    return response.json().get("features", [])


def get_last_alert():
    if os.path.exists(ALERT_FILE):
        with open(ALERT_FILE, "r", encoding="utf-8") as file:
            return file.read().strip()

    return ""


def save_alert(alert_id):
    with open(ALERT_FILE, "w", encoding="utf-8") as file:
        file.write(alert_id)


def create_audio(message):
    voice = gTTS(
        text=message,
        lang="en"
    )

    voice.save(OUTPUT_FILE)

    print(f"Created: {OUTPUT_FILE}")


def main():
    alerts = get_alerts()

    if not alerts:
        print("No active Delaware weather alerts.")
        return

    last_alert = get_last_alert()

    for alert in alerts:
        properties = alert.get("properties", {})

        event = properties.get("event", "")

        if event not in ALERT_TYPES:
            continue

        alert_id = alert.get("id") or properties.get("headline", "")

        if alert_id == last_alert:
            print("No new emergency alerts.")
            return

        headline = properties.get(
            "headline",
            "A weather alert has been issued for Delaware."
        )

        description = properties.get(
            "description",
            "Please monitor local weather conditions and follow official safety instructions."
        )

        message = (
            "Emergency weather update from "
            "Delaware All Saints Gospel Radio. "
            f"{headline}. "
            f"{description}. "
            "Please take precautions and stay safe. "
            "Stay tuned to Delaware All Saints Gospel Radio "
            "for additional updates."
        )

        create_audio(message)

        save_alert(alert_id)

        print("New emergency alert audio created.")
        return

    print("No new emergency alerts.")


if __name__ == "__main__":
    main()
