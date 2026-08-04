#!/usr/bin/env python3

"""
Delaware All Saints Gospel Radio
Live Traffic Broadcast Generator
"""

import requests
from datetime import datetime


def get_delaware_traffic():
    """
    Get Delaware traffic alerts.
    """

    url = "https://511api.delaware.gov/api/getevents"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        data = response.json()

        alerts = []

        for event in data.get("events", []):
            headline = event.get("headline")

            if headline:
                alerts.append(headline)

        if alerts:
            return alerts[:5]

        return ["No major traffic incidents reported at this time."]

    except Exception:
        return ["Live traffic information is temporarily unavailable."]


def create_traffic_report():

    time_now = datetime.now().strftime("%I:%M %p")

    traffic = get_delaware_traffic()

    report = f"""
You are listening to Delaware All Saints Gospel Radio Podcast,
where praise lives.

This is your live Delaware traffic update at {time_now}.

"""

    for item in traffic:
        report += item + ". "

    report += """

Please drive safely, allow extra travel time,
and keep it right here on Delaware All Saints Gospel Radio Podcast.
Stay blessed.
"""

    with open("traffic_report.txt", "w", encoding="utf-8") as file:
        file.write(report)

    print(report)


if __name__ == "__main__":
    create_traffic_report()
