#!/usr/bin/env python3
import os
import subprocess
import time
import datetime
from gtts import gTTS

STATION = "Delaware All Saints Gospel Radio"

def build_stream_command():
    password = os.getenv("STREAM_PASSWORD")
    mount = os.getenv("STREAM_MOUNTPOINT")

    return [
        "ffmpeg",
        "-re",
        "-i", "live_ai_output.mp3",
        "-acodec", "libmp3lame",
        "-ab", "128k",
        "-content_type", "audio/mpeg",
        "-f", "mp3",
        f"icecast://source:{password}@stream.radiojar.com:80/{mount}"
    ]

def generate_audio():
    print("AI audio generated for streaming.")

def start_stream():
    cmd = build_stream_command()
    print("Starting scheduled stream...")
    print(" ".join(cmd))

    process = subprocess.Popen(cmd)
    process.wait()

    print("Stream finished.")
last_hour = -1

def generate_audio(message):
    print("Generating:", message)

    tts = gTTS(
        text=message,
        lang="en"
    )

    tts.save("live_ai_output.mp3")


def main():

    print(f"Starting scheduled broadcast for {STATION}")

    while True:

        now = datetime.datetime.now()

        # Station ID once at the top of every hour
        if now.minute == 0 and now.hour != last_hour:

            last_hour = now.hour

            message = (
                f"You're listening to {STATION}. "
                "Where praise lives twenty-four hours a day. "
                "Stay blessed and keep listening."
            )

            generate_audio(message)

            start_stream()

        time.sleep(10)


if __name__ == "__main__":
    main()
