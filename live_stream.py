#!/usr/bin/env python3

import os
import subprocess
import datetime

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
    # Your AI system should already create live_ai_output.mp3
    print("AI audio generated for streaming.")

def start_stream():
    cmd = build_stream_command()
    print("Starting scheduled stream...")
    print(" ".join(cmd))

    process = subprocess.Popen(cmd)
    process.wait()

    print("Stream finished.")

def main():
    print(f"Starting scheduled broadcast for {STATION}")
    print("Timestamp:", datetime.datetime.now())

    generate_audio()
    start_stream()

    print("Broadcast completed successfully.")

if __name__ == "__main__":
    main()
