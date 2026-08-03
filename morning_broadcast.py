#!/usr/bin/env python3
import argparse
import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from gtts import gTTS
import textwrap

STATION = "Delaware All Saints Gospel Radio"
COORDS = "39.6837,-75.7497"  # Newark, DE
USER_AGENT = "Delaware All Saints Gospel Radio automation"
OUTPUT_FILE = Path("delaware_all_saints_global_morning.mp3")
REQUEST_TIMEOUT = 10.0

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Weather:
    temp: Optional[str] = None
    condition: Optional[str] = None
    wind: Optional[str] = None
    humidity: Optional[str] = None

    def as_display(self):
        return {
            "temp": self.temp or "unavailable",
            "condition": self.condition or "weather data unavailable",
            "wind": self.wind or "unavailable",
            "humidity": self.humidity or "Not available",
        }


def build_session(retries: int = 3, backoff_factor: float = 0.3) -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        status=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def fetch_json(session: requests.Session, url: str, timeout: float = REQUEST_TIMEOUT) -> dict:
    resp = session.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def get_weather(session: Optional[requests.Session] = None, coords: str = COORDS) -> Weather:
    sess = session or build_session()
    points_url = f"https://api.weather.gov/points/{coords}"
    logger.info("Fetching points data from %s", points_url)
    data = fetch_json(sess, points_url)
    forecast_url = data.get("properties", {}).get("forecast")
    if not forecast_url:
        raise ValueError("Forecast URL not found in points response")

    logger.info("Fetching forecast from %s", forecast_url)
    forecast = fetch_json(sess, forecast_url)
    periods = forecast.get("properties", {}).get("periods", [])
    if not periods:
        raise ValueError("No forecast periods found")

    period = periods[0]
    return Weather(
        temp=str(period.get("temperature")),
        condition=period.get("shortForecast"),
        wind=period.get("windSpeed"),
        humidity=None,  # API might include relativeHumidity elsewhere; map it if needed
    )


def weather_report(weather: Weather) -> str:
    d = weather.as_display()
    return (
        f"Here is your Delaware forecast. "
        f"Temperatures are currently {d['temp']} degrees "
        f"with {d['condition']}. "
        f"Winds are {d['wind']}."
    )


def traffic_report() -> str:
    return (
        "For our listeners traveling through Delaware, "
        "traffic is being monitored across Interstate 95, "
        "the Delaware Memorial Bridge, Route 1, and the Wilmington area. "
        "Please allow extra travel time and drive safely."
    )


def gospel_inspiration() -> str:
    return (
        "Today's scripture comes from Isaiah chapter forty-one, verse ten. "
        "Fear not, for I am with you; be not dismayed, for I am your God. "
        "Wherever you are listening around the world today, remember "
        "that God's love and mercy reach every nation. "
        "Walk in faith, stay encouraged, and know that you are never alone."
    )


def build_script(weather: Weather, station: str = STATION) -> str:
    today = datetime.datetime.now().strftime("%A, %B %d")
    parts = [
        "Good morning, good afternoon, and good evening to our listeners around the world.",
        f"You are listening to {station}, broadcasting from Delaware to the nations. Where Praise Lives.",
        f"Today is {today}.",
        weather_report(weather),
        traffic_report(),
        gospel_inspiration(),
        f"Thank you for starting your day with {station}.",
        "Stay blessed, keep the faith, and keep it right here.",
    ]
    # join with spaces to ensure proper spacing, then normalize whitespace
    return textwrap.dedent(" ".join(parts)).strip()


def create_audio(script: str, output: Path = OUTPUT_FILE) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    tts = gTTS(text=script, lang="en", slow=False)
    tts.save(str(output))
    logger.info("Created %s", output)
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(description="Global Morning Update - weather.gov version")
    parser.add_argument("--coords", default=COORDS, help="Latitude,Longitude for weather points API")
    parser.add_argument("--output", default=str(OUTPUT_FILE), help="Output MP3 filename")
    args = parser.parse_args(argv)

    logger.info("Starting Global Morning Update - WEATHER.GOV VERSION")
    sess = build_session()

    try:
        weather = get_weather(session=sess, coords=args.coords)
    except (requests.RequestException, ValueError, KeyError) as exc:
        logger.exception("Weather fetch failed: %s", exc)
        weather = Weather()  # fallback with None fields

    script = build_script(weather)
    logger.info("Built script: %s", script)
    create_audio(script, output=Path(args.output))


if __name__ == "__main__":
    main()
