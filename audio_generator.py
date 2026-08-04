#!/usr/bin/env python3

from gtts import gTTS
import os

def create_audio():
    text_parts = []

    if os.path.exists("traffic_report.txt"):
        with open("traffic_report.txt", "r", encoding="utf-8") as f:
            text_parts.append(f.read())

    if os.path.exists("weather_report.txt"):
        with open("weather_report.txt", "r", encoding="utf-8") as f:
            text_parts.append(f.read())

    if not text_parts:
        text_parts.append(
            "You are listening to Delaware All Saints Gospel Radio Podcast. "
            "Your automated weather and traffic update is being prepared."
        )

    broadcast_text = "\n\n".join(text_parts)

    audio = gTTS(
        text=broadcast_text,
        lang="en",
        slow=False
    )

    audio.save("output.mp3")

    print("Created output.mp3")


if __name__ == "__main__":
    create_audio()
