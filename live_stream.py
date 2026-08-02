 #!/usr/bin/env python3
import time, datetime, requests, os
from gtts import gTTS
import subprocess

# ───────────────────────────────────────────────
# CONFIG
# ───────────────────────────────────────────────
STATION = "Delaware All Saints Gospel Radio"
VOICE_SPEED = 1.0   # normal speed
UPDATE_INTERVAL = 60  # seconds

# Your live encoder command (BUTT / ffmpeg / OBS virtual device)
# This example uses ffmpeg to stream to a virtual audio device.
STREAM_COMMAND = [
    "ffmpeg",
    "-re",
    "-i", "live_ai_output.mp3",
    "-f", "wav",
    "default"
]

# ───────────────────────────────────────────────
# DATA FETCHERS
# ───────────────────────────────────────────────

def get_delaware_weather():
    url = "https://api.weatherapi.com/v1/current.json?key=YOUR_KEY&q=Newark,DE"
    r = requests.get(url).json()
    return {
        "temp": r["current"]["temp_f"],
        "condition": r["current"]["condition"]["text"],
        "wind": r["current"]["wind_mph"],
        "humidity": r["current"]["humidity"]
    }

def get_i95_traffic():
    # Example traffic API (replace with real DOT feed)
    return {
        "status": "Moderate congestion near Wilmington and the Delaware Memorial Bridge",
        "incidents": "No major accidents reported"
    }

def get_us_weather():
    # Example national weather summary
    return "Scattered storms across the Midwest, heat advisories in the South, clear skies in the Northeast."

def get_global_weather():
    # Example global weather summary
    return "Heavy monsoon rains in India, heatwave in Southern Europe, tropical moisture increasing in the Caribbean."

# ───────────────────────────────────────────────
# SCRIPT BUILDER (Male Broadcaster Style)
# ───────────────────────────────────────────────

def build_script(local, traffic, national, global_wx):
    now = datetime.datetime.now().strftime("%A %B %-d, %-I:%M %p EDT")

    return (
        f"This is your live global weather and traffic update from {STATION}. "
        f"Broadcasting from Delaware to the world. "
        f"As of {now}, Newark sits at {local['temp']} degrees with {local['condition'].lower()}. "
        f"Winds at {local['wind']} miles per hour and humidity at {local['humidity']} percent. "
        f"Along the I ninety five corridor, {traffic['status']}. {traffic['incidents']}. "
        f"Across the United States, {national}. "
        f"Internationally, {global_wx}. "
        f"This has been your live AI broadcaster update. "
        f"More real time conditions in sixty seconds."
    )

# ───────────────────────────────────────────────
# AI VOICE GENERATOR
# ───────────────────────────────────────────────

def generate_audio(text):
    tts = gTTS(text=text, lang="en", slow=False)
    tts.save("live_ai_output.mp3")

# ───────────────────────────────────────────────
# LIVE STREAM LOOP
# ───────────────────────────────────────────────

def main():
    print("🔴 AI LIVE BROADCAST STARTED — Male Broadcaster Voice")

    while True:
        try:
            local = get_delaware_weather()
            traffic = get_i95_traffic()
            national = get_us_weather()
            global_wx = get_global_weather()

            script = build_script(local, traffic, national, global_wx)
            generate_audio(script)

            print("🎙️  Generated new live AI segment… streaming now.")

            subprocess.Popen(STREAM_COMMAND)

        except Exception as e:
            print(f"❌ Error: {e}")

        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    main()
