#!/usr/bin/env python3

import os
import requests

RADIOJAR_UPLOAD_URL = "https://api.radiojar.com/v2/media/upload/"
AUDIO_FILE = "delaware_all_saints_update.mp3"


def upload_to_radiojar(filename):
    api_key = os.getenv("RADIOJAR_API_KEY")

    if not api_key:
        raise RuntimeError("RADIOJAR_API_KEY is missing.")

    if not os.path.exists(filename):
        raise FileNotFoundError(
            f"Audio file not found: {filename}"
        )

    print(f"Uploading {filename} to RadioJar...")

    with open(filename, "rb") as audio:
        response = requests.post(
            RADIOJAR_UPLOAD_URL,
            headers={
                "Authorization": f"Bearer {api_key}"
            },
            files={
                "file": audio
            },
            timeout=60
        )

    if response.status_code not in (200, 201):
        print("RadioJar upload failed.")
        print(f"HTTP status: {response.status_code}")
        print(response.text)
        raise RuntimeError("RadioJar upload failed.")

    print("Upload successful to RadioJar.")
    print(response.text)


if __name__ == "__main__":
    upload_to_radiojar(AUDIO_FILE)
