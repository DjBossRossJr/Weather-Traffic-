#!/usr/bin/env python3

import datetime
import requests
import os
from gtts import gTTS

STATION = "Delaware All Saints Gospel Radio Podcast"
TAGLINE = "Where Praise Lives"

NWS_HEADERS = {
    "User-Agent": "Delaware All Saints Gospel Radio automation"
}


def get_weather():
    """Get the latest Delaware forecast from the National Weather Service."""

    points_url = "https://api.weather.gov/points/39.6837,-75.7497"

    points_response = requests.get(
        points_url,
        headers=NWS_HEADERS,
        timeout=15
    )
    points_response.raise_for_status()

    points = points_response.json()

    forecast_url = points["properties"]["forecast"]

    forecast_response = requests.get(
        forecast_url,
        headers=NWS_HEADERS,
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


def get_emergency_alerts():
    """Get currently active NWS alerts affecting Delaware."""

    alerts_url = "https://api.weather.gov/alerts/active?area=DE"

    try:
        response = requests.get(
            alerts_url,
            headers=NWS_HEADERS,
            timeout=15
        )
        response.raise_for_status()

        data = response.json()

        alerts = []

        for feature in data.get("features", []):
            properties = feature.get("properties", {})

            event = properties.get("event")
            headline = properties.get("headline")
            description = properties.get("description")
            severity = properties.get("severity")

            if event:
                alerts.append({
                    "event": event,
                    "headline": headline,
                    "description": description,
                    "severity": severity
                })

        return alerts

    except Exception as e:
        print(f"Emergency alert check failed: {e}")
        return []


def emergency_alert_report(alerts):
    """Create a radio announcement for active alerts."""

    if not alerts:
        return (
            "There are currently no active National Weather Service "
            "weather alerts for Delaware."
        )

    report = (
        "Attention Delaware listeners. "
        "This is an active weather alert announcement. "
    )

    for alert in alerts[:3]:
        event = alert["event"]

        report += (
            f"The National Weather Service has issued a {event}. "
        )

        if alert["headline"]:
            report += f"{alert['headline']} "

    report += (
        "Please monitor official emergency information, "
        "follow instructions from local authorities, "
        "and keep yourself and your family safe."
    )

    return report


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
        "Monitoring Interstate 95, Interstate 495, "
        "Route 1, Route 13, Route 40, Route 202, "
        "and the Delaware Memorial Bridge. "
        "Please drive safely."
    )


def gospel_inspiration():
    return (
        "Today's inspiration comes from Isaiah chapter forty-one "
        "verse ten. Fear not, for I am with you. "
        "God is with you through every challenge. "
        "Stay encouraged and walk in faith."
    )


def build_script(weather, alerts):
    today = datetime.datetime.now().strftime("%A, %B %d")

    return (
        f"You're listening to {STATION}, "
        f"{TAGLINE}. "
        f"Broadcasting from Delaware to listeners around the world. "
        f"Today is {today}. "

        f"{weather_report(weather)} "

        f"{emergency_alert_report(alerts)} "

        f"{traffic_report()} "

        f"{gospel_inspiration()} "

        f"Thank you for starting your day with {STATION}. "
        f"Stay blessed and keep it right here on "
        f"{STATION}."
    )


def create_audio(script):
    """Create MP3 using safe gTTS chunks."""

    parts = script.split(". ")
    chunk_files = []

    for i, part in enumerate(parts):
        if part.strip():

            filename = f"chunk_{i}.mp3"

            tts = gTTS(
                text=part.strip(),
                lang="en"
            )

            tts.save(filename)
            chunk_files.append(filename)

    output_filename = (
        f"delaware_all_saints_"
        f"{datetime.datetime.now().strftime('%Y_%m_%d_%H_%M')}.mp3"
    )

    concat = "|".join(chunk_files)

    os.system(
        f'ffmpeg -y -i "concat:{concat}" '
        f'-acodec libmp3lame -ab 128k "{output_filename}"'
    )

    print(f"Created {output_filename}")

    # Clean up temporary chunks
    for filename in chunk_files:
        try:
            os.remove(filename)
        except OSError:
            pass

    return output_filename


def main():

    print("Starting Delaware All Saints Global Morning Broadcast")

    # Get weather
    weather = get_weather()

    # Check active emergency alerts
    alerts = get_emergency_alerts()

    print(f"Active Delaware alerts: {len(alerts)}")

    # Build broadcast
    script = build_script(weather, alerts)

    print("\n--- BROADCAST SCRIPT ---")
    print(script)
    print("--- END SCRIPT ---\n")

    # Create audio
    audio_file = create_audio(script)

    print(f"Broadcast completed successfully: {audio_file}")


if __name__ == "__main__":
    main()
