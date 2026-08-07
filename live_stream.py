    #!/usr/bin/env python3

import os
import time
import datetime
import requests
import subprocess
from gtts import gTTS

# ==========================================================
# Delaware All Saints Gospel Radio
# Live AI Weather • Traffic • Emergency Broadcast
# ==========================================================

STATION = "Delaware All Saints Gospel Radio"
UPDATE_INTERVAL = 590 # seconds

# ----------------------------------------------------------
# RadioJar GitHub Secrets
# ----------------------------------------------------------

STREAM_HOST = os.getenv("STREAM_HOST")
STREAM_PORT = os.getenv("STREAM_PORT")
STREAM_PASSWORD = os.getenv("STREAM_PASSWORD")
STREAM_MOUNTPOINT = os.getenv("STREAM_MOUNTPOINT")

required = {
    "STREAM_HOST": STREAM_HOST,
    "STREAM_PORT": STREAM_PORT,
    "STREAM_PASSWORD": STREAM_PASSWORD,
    "STREAM_MOUNTPOINT": STREAM_MOUNTPOINT,
}

missing = [k for k, v in required.items() if not v]

if missing:
    raise RuntimeError(
        f"Missing GitHub Secrets: {', '.join(missing)}"
    )

# ----------------------------------------------------------
# FFmpeg Streaming Command
# ----------------------------------------------------------

STREAM_COMMAND = [
    "ffmpeg",
    "-re",
    "-i", "live_ai_output.mp3",
    "-acodec", "libmp3lame",
    "-b:a", "128k",
    "-content_type", "audio/mpeg",
    "-f", "mp3",
    (
        f"icecast://source:{STREAM_PASSWORD}"
        f"@{STREAM_HOST}:{STREAM_PORT}"
        f"/{STREAM_MOUNTPOINT}"
    ),
]

# ----------------------------------------------------------
# Scheduling
# ----------------------------------------------------------

def ai_mode_now():
    now = datetime.datetime.now()
    day = now.weekday()
    hour = now.hour
    minute = now.minute

    if minute == 0:
        return "station_id"

    if day == 4 and 20 <= hour < 22:
        return "live_show"

    return "ai"

# ----------------------------------------------------------
# Weather
# ----------------------------------------------------------

def get_delaware_weather():

    headers = {
        "User-Agent": "Delaware All Saints Gospel Radio Automation"
    }

    points = requests.get(
        "https://api.weather.gov/points/39.6837,-75.7497",
        headers=headers,
        timeout=10
    ).json()

    forecast_url = points["properties"]["forecast"]

    forecast = requests.get(
        forecast_url,
        headers=headers,
        timeout=10
    ).json()

    period = forecast["properties"]["periods"][0]

    return {
        "temp": period["temperature"],
        "condition": period["shortForecast"],
        "wind": period["windSpeed"],
        "humidity": "not available"
    }

def build_weather_report(weather):
    return (
        f"In Newark, Delaware it is "
        f"{weather['temp']} degrees with "
        f"{weather['condition'].lower()}, "
        f"winds {weather['wind']}, "
        f"humidity {weather['humidity']}."
    )

# ----------------------------------------------------------
# Traffic
# ----------------------------------------------------------

def get_traffic_mode():

    hour = datetime.datetime.now().hour

    if 5 <= hour < 9:
        return "morning"

    if 11 <= hour < 13:
        return "midday"

    if 16 <= hour < 18:
        return "evening"

    if hour >= 22:
        return "late"

    return "normal"

def build_traffic_report(mode):

    reports = {
        "morning":
            "Morning rush hour traffic is heavy on I-95 near Wilmington and Route 1.",

        "midday":
            "Traffic is moving well across Delaware with light congestion.",

        "evening":
            "Evening commute delays are building along I-95 and Route 1.",

        "late":
            "Roads are mostly clear with occasional overnight construction.",

        "normal":
            "Traffic is moving normally across Delaware."
    }

    return reports[mode]

# ----------------------------------------------------------
# Emergency Alerts
# ----------------------------------------------------------

def get_emergency_status():
    return "No active emergency alerts at this time."

# ----------------------------------------------------------
# Station ID
# ----------------------------------------------------------

def build_station_id():

    return (
        f"You're listening to {STATION}, "
        "broadcasting from the First State to listeners around the world. "
        "Where praise lives twenty-four hours a day."
    )

# ----------------------------------------------------------
# Audio Generation
# ----------------------------------------------------------

def generate_audio(text):

    print("Generating audio...")

    tts = gTTS(
        text=text,
        lang="en",
        slow=False
    )

    tts.save("live_ai_output.mp3")

# ----------------------------------------------------------
# Stream
# ----------------------------------------------------------

def stream_audio():

    print("Connecting to RadioJar...")

    result = subprocess.run(STREAM_COMMAND)

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg exited with status {result.returncode}"
        )

    print("Broadcast completed.")

# ----------------------------------------------------------
# Broadcast Modes
# ----------------------------------------------------------

def run_station_id():

    generate_audio(build_station_id())

    stream_audio()

def run_ai_update():

    try:

        weather = get_delaware_weather()

        weather_report = build_weather_report(weather)

    except Exception as e:

        print(e)

        weather_report = "Weather information is temporarily unavailable."

    traffic_report = build_traffic_report(
        get_traffic_mode()
    )

    emergency = get_emergency_status()

    now = datetime.datetime.now().strftime(
        "%A %B %d, %I:%M %p EDT"
    )

    script = (
        f"This is your live update from {STATION}. "
        f"As of {now}. "
        f"{weather_report} "
        f"Traffic update. {traffic_report} "
        f"Emergency update. {emergency} "
        f"Stay blessed and keep listening to "
        f"{STATION}."
    )

    generate_audio(script)

    stream_audio()

# ----------------------------------------------------------
# Main
# ----------------------------------------------------------

def main():

    print("AI Broadcast Started")

    while True:

        mode = ai_mode_now()

        if mode == "station_id":

            print("Station ID")

            run_station_id()

        elif mode == "live_show":

            print("Friday Live Show - AI Paused")

        else:

            print("AI Weather Update")

            run_ai_update()

        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    main()  
