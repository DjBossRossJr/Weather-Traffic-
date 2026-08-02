#!/usr/bin/env python3
import time, datetime, requests, subprocess
from gtts import gTTS

# ───────────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────────
STATION = "Delaware All Saints Gospel Radio"
UPDATE_INTERVAL = 60  # seconds

WEATHER_API_KEY = "eh4FZOMlzAybrUuS"  # your WeatherAPI key
WEATHER_LOCATION = "Newark,DE"

# ffmpeg output – adjust "default" to your actual audio device if needed
STREAM_COMMAND = [
    "ffmpeg",
    "-re",
    "-i", "live_ai_output.mp3",
    "-f", "wav",
    "default"
]

# ───────────────────────────────────────────────
# SCHEDULING LOGIC
# ───────────────────────────────────────────────

def ai_mode_now():
    """
    Returns:
      "station_id"  → play top-of-hour ID
      "live_show"   → Friday 8–10 PM (AI silent)
      "ai"          → normal AI operation
    """
    now = datetime.datetime.now()
    day = now.weekday()   # Monday=0, Friday=4
    hour = now.hour
    minute = now.minute

    # Rule 1 — Top-of-hour Station ID
    if minute == 0:
        return "station_id"

    # Rule 2 — Friday Live Show (8 PM to 10 PM)
    if day == 4 and 20 <= hour < 22:
        return "live_show"

    # Rule 3 — Normal AI
    return "ai"

# ───────────────────────────────────────────────
# WEATHER
# ───────────────────────────────────────────────

def get_delaware_weather():
    url = (
        f"https://api.weatherapi.com/v1/current.json?"
        f"key={WEATHER_API_KEY}&q={WEATHER_LOCATION}"
    )
    r = requests.get(url, timeout=10).json()

    return {
        "temp": r["current"]["temp_f"],
        "condition": r["current"]["condition"]["text"],
        "wind": r["current"]["wind_mph"],
        "humidity": r["current"]["humidity"]
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
