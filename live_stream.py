#!/usr/bin/env python3

import os
import subprocess
from gtts import gTTS

# ==========================================================
# Delaware All Saints Gospel Radio
# Live AI Broadcast Stream
# ==========================================================

STATION = "Delaware All Saints Gospel Radio"

# ----------------------------------------------------------
# RadioJar GitHub Secrets
# ----------------------------------------------------------

STREAM_HOST = os.getenv("STREAM_HOST")
STREAM_PORT = os.getenv("STREAM_PORT")
STREAM_USERNAME = os.getenv("STREAM_USERNAME")
STREAM_PASSWORD = os.getenv("STREAM_PASSWORD")
STREAM_MOUNTPOINT = os.getenv("STREAM_MOUNTPOINT")

required = {
    "STREAM_HOST": STREAM_HOST,
    "STREAM_PORT": STREAM_PORT,
    "STREAM_USERNAME": STREAM_USERNAME,
    "STREAM_PASSWORD": STREAM_PASSWORD,
    "STREAM_MOUNTPOINT": STREAM_MOUNTPOINT,
}

missing = [k for k, v in required.items() if not v]

if missing:
    raise RuntimeError(
        f"Missing GitHub Secrets: {', '.join(missing)}"
    )


# ----------------------------------------------------------
# Create AI Audio
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
# RadioJar Stream
# ----------------------------------------------------------

def stream_audio():

    stream_url = (
        f"icecast://{STREAM_USERNAME}:{STREAM_PASSWORD}"
        f"@{STREAM_HOST}:{STREAM_PORT}"
        f"/{STREAM_MOUNTPOINT}"
    )

    command = [
        "ffmpeg",
        "-re",
        "-stream_loop",
        "-1",
        "-i",
        "live_ai_output.mp3",
        "-acodec",
        "libmp3lame",
        "-b:a",
        "128k",
        "-content_type",
        "audio/mpeg",
        "-f",
        "mp3",
        stream_url
    ]

    print("Connecting to RadioJar...")

    process = subprocess.Popen(command)

    process.wait()

    if process.returncode != 0:
        raise RuntimeError(
            f"FFmpeg exited with status {process.returncode}"
        )


# ----------------------------------------------------------
# Station Start
# ----------------------------------------------------------

def main():

    print("AI Broadcast Started")

    message = (
        f"You're listening to {STATION}. "
        "Where praise lives twenty-four hours a day. "
        "Stay blessed and keep listening."
    )

    generate_audio(message)

    stream_audio()


if __name__ == "__main__":
    main()
