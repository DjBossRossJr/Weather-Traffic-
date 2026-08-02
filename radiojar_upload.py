#!/usr/bin/env python3

import os
import requests


RADIOJAR_UPLOAD_URL = "https://api.radiojar.com/v2/media/upload/"


def upload_to_radiojar(filename):

    api_key = os.getenv("RADIOJAR_API_KEY")

    if not api_key:
        print("ERROR: RADIOJAR_API_KEY is missing.")
        return False

    try:
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

        if response.status_code in (200, 201):
            print("✅ Upload successful to RadioJar")
            print(response.text)
            return True

        else:
            print("❌ RadioJar upload failed")
            print(response.status_code)
            print(response.text)
            return False

    except Exception as error:
        print(f"Upload error: {error}")
        return False


if __name__ == "__main__":

    audio_file = "delaware_all_saints_global_morning.mp3"

    upload_to_radiojar(audio_file)
