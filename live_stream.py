#!/usr/bin/env python3
import os
import time, datetime, requests, subprocess
from gtts import gTTS

# ───────────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────────
STATION = "Delaware All Saints Gospel Radio"
UPDATE_INTERVAL = 60  # seconds

STREAM_COMMAND = [
    "ffmpeg",
    "-re",
    "-i", "live_ai_output.mp3",
    "-acodec", "libmp3lame",
    "-ab", "128k",
    "-content_type", "audio/mpeg",
    "-f", "mp3",
  f"icecast://source:{os.getenv('STREAM_PASSWORD')}@stream.radiojar.com:80/{os.getenv('STREAM_MOUNTPOINT')}"
]


# ───────────────────────────────────────────────
# SCHEDULING LOGIC
# ───────────────────────────────────────────────

def ai_mode_now():
    now = datetime.datetime.now()
    day = now.weekday()   # Monday=0, Friday=4
    hour = now.hour
    minute = now.minute

    if minute == 0:
        return "station_id"

    if day == 4 and 20 <= hour < 22:
        return "live_show"

    return "ai"

# ───────────────────────────────────────────────
# WEATHER
# ───────────────────────────────────────────────

def get_delaware_weather():

    headers = {
        "User-Agent": "Delaware All Saints Gospel Radio automation"
    }

    points_url = (
        "https://api.weather.gov/points/"
        "39.6837,-75.7497"
    )

    points = requests.get(
        points_url,
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

def build_weather_report(w):
    return (
        f"In Newark, Delaware, it is {w['temp']} degrees with "
        f"{w['condition'].lower()}, winds at {w['wind']} miles per hour, "
        f"and humidity at {w['humidity']} percent."
    )

# ───────────────────────────────────────────────
# TRAFFIC MODES
# ───────────────────────────────────────────────

def get_traffic_mode():
    now = datetime.datetime.now()
    hour = now.hour

    if 5 <= hour < 9:
        return "morning_rush"
    elif 11 <= hour < 13:
        return "midday"
    elif 16 <= hour < 18:
        return "evening_rush"
    elif 22 <= hour < 24:
        return "late_night"
    else:
        return "normal"

def build_traffic_report(mode):
    if mode == "morning_rush":
        return (
            "Morning rush hour delays on I-95 near Wilmington, "
            "slowdowns approaching the Delaware Memorial Bridge, "
            "and increased commuter traffic along Route 1."
        )

    if mode == "midday":
        return (
            "Midday traffic is generally light with steady flow around "
            "Christiana Mall and Route 7. No major incidents reported."
        )

    if mode == "evening_rush":
        return (
            "Evening rush hour congestion building on I-95 northbound, "
            "delays near the mall ramps, and heavier traffic approaching "
            "the Delaware Memorial Bridge."
        )

    if mode == "late_night":
        return (
            "Late-night roads are mostly clear across Delaware. Watch for "
            "overnight construction zones and long-haul truck activity on I-95."
        )

    return "Traffic is moving normally across Delaware with no major incidents."

# ───────────────────────────────────────────────
# EMERGENCIES (PLACEHOLDER)
# ───────────────────────────────────────────────

def get_emergency_status():
    return "No active emergency alerts at this time."

# ───────────────────────────────────────────────
# STATION ID
# ───────────────────────────────────────────────

def build_station_id():
    return (
        f"You are listening to {STATION}, broadcasting from Delaware to the world. "
        f"Delaware All Saints Gospel Radio — established twenty twenty-one."
    )

# ───────────────────────────────────────────────
# AI VOICE GENERATOR
# ───────────────────────────────────────────────

def generate_audio(text):
    tts = gTTS(text=text, lang="en", slow=False)
    tts.save("live_ai_output.mp3")

def stream_audio():
    subprocess.Popen(STREAM_COMMAND)
# ───────────────────────────────────────────────
# MAIN LOOP
# ───────────────────────────────────────────────

def run_station_id():
    script = build_station_id()
    print("🔊 Station ID (top of hour)")
    generate_audio(script)
    stream_audio()

def run_ai_update():
    try:
        weather = get_delaware_weather()
        weather_report = build_weather_report(weather)
    except Exception as e:
        print(f"⚠️ Weather fetch failed: {e}")
        weather_report = "Weather data is temporarily unavailable."

    traffic_mode = get_traffic_mode()
    traffic_report = build_traffic_report(traffic_mode)

    emergency_report = get_emergency_status()

    now = datetime.datetime.now().strftime("%A %B %-d, %-I:%M %p EDT")

    script = (
        f"This is your live update from {STATION}. "
        f"As of {now}, {weather_report} "
        f"Traffic update: {traffic_report} "
        f"Emergency status: {emergency_report} "
        f"More live conditions in sixty seconds."
    )

    print("🎙️ AI live segment generated.")
    generate_audio(script)
    stream_audio()

def main():
    print("🔴 AI LIVE BROADCAST STARTED — Weather, Traffic Modes, Emergencies")

    while True:
        mode = ai_mode_now()

        if mode == "station_id":
            run_station_id()

        elif mode == "live_show":
            print("🎧 Live show window (Friday 8–10 PM) — AI paused.")

        else:
            run_ai_update()

        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    main()
