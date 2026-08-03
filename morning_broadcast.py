#!/usr/bin/env python3
"""
morning_broadcast.py

Continuously fetch weather and traffic, build a short spoken briefing,
optionally "AI-enhance" the text through OpenAI, and play it live.

Config via environment variables or CLI args:
- COORDS (lat,lon) default: 39.6837,-75.7497 (Newark, DE)
- STATION  default: "Delaware All Saints Gospel Radio"
- POLL_INTERVAL (seconds) default: 300
- TRAFFIC_PROVIDER: "mapquest" or "here" or empty (none)
- TRAFFIC_API_KEY: provider key (MapQuest, HERE, etc.)
- OPENAI_API_KEY: optional, for nicer phrasing via OpenAI
"""
from __future__ import annotations
import argparse
import datetime
import json
import logging
import os
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Optional libs - used if installed
try:
    import pyttsx3  # offline TTS
except Exception:
    pyttsx3 = None
try:
    from gtts import gTTS
    from pydub import AudioSegment
    from pydub.playback import play as play_audio
except Exception:
    gTTS = None
    AudioSegment = None
    play_audio = None

# Optional OpenAI (only used if OPENAI_API_KEY present)
try:
    import openai
except Exception:
    openai = None

# Logging
logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("morning_broadcast")

# Configuration defaults (can be overridden by env or CLI)
DEFAULT_COORDS = os.getenv("COORDS", "39.6837,-75.7497")
DEFAULT_STATION = os.getenv("STATION", "Delaware All Saints Gospel Radio")
DEFAULT_POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "300"))  # 5 minutes

# Retry configuration
REQUEST_TIMEOUT = 10.0
RETRIES = 3
BACKOFF_FACTOR = 0.5


def build_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=RETRIES,
        read=RETRIES,
        connect=RETRIES,
        status=RETRIES,
        backoff_factor=BACKOFF_FACTOR,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"]),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"User-Agent": f"{DEFAULT_STATION} automation"})
    return session


@dataclass
class Weather:
    temperature: Optional[float] = None
    short_forecast: Optional[str] = None
    wind: Optional[str] = None
    humidity: Optional[str] = None
    fetched_at: Optional[datetime.datetime] = None

    def to_dict(self) -> Dict:
        return {
            "temperature": self.temperature,
            "short_forecast": self.short_forecast,
            "wind": self.wind,
            "humidity": self.humidity,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
        }


@dataclass
class TrafficIncident:
    title: str
    description: str
    severity: Optional[int] = None
    lat: Optional[float] = None
    lon: Optional[float] = None


@dataclass
class Traffic:
    incidents: list[TrafficIncident]
    fetched_at: Optional[datetime.datetime] = None

    def summary(self, max_incidents=3) -> str:
        if not self.incidents:
            return "Traffic is clear in the monitored area."
        parts = []
        for i, inc in enumerate(self.incidents[:max_incidents], start=1):
            parts.append(f"Incident {i}: {inc.title}. {inc.description}")
        if len(self.incidents) > max_incidents:
            parts.append(f"And {len(self.incidents) - max_incidents} more incidents reported.")
        return " ".join(parts)


def fetch_json(session: requests.Session, url: str, timeout: float = REQUEST_TIMEOUT) -> Dict:
    logger.debug("GET %s", url)
    r = session.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def get_weather(session: requests.Session, coords: str) -> Weather:
    """
    Query weather.gov points -> forecast. Returns first period as a simple Weather object.
    """
    try:
        points_url = f"https://api.weather.gov/points/{coords}"
        logger.info("Fetching weather points for %s", coords)
        points = fetch_json(session, points_url)
        forecast_url = points.get("properties", {}).get("forecast")
        if not forecast_url:
            raise RuntimeError("No forecast URL in points response")
        logger.info("Fetching forecast from %s", forecast_url)
        forecast = fetch_json(session, forecast_url)
        periods = forecast.get("properties", {}).get("periods", [])
        if not periods:
            raise RuntimeError("No periods in forecast")
        p0 = periods[0]
        temp = p0.get("temperature")
        short = p0.get("shortForecast")
        wind = p0.get("windSpeed") or p0.get("windDirection")
        w = Weather(
            temperature=float(temp) if temp is not None else None,
            short_forecast=short,
            wind=wind,
            fetched_at=datetime.datetime.utcnow(),
        )
        logger.debug("Weather fetched: %s", w.to_dict())
        return w
    except Exception:
        logger.exception("Failed to fetch weather")
        raise


def get_traffic_mapquest(session: requests.Session, bbox: Tuple[float, float, float, float], api_key: str) -> Traffic:
    """
    Example MapQuest Traffic incidents call.
    bbox: (minLat, minLon, maxLat, maxLon)
    MapQuest Traffic API returns incidents - see docs for parameters and key requirements.
    """
    try:
        minLat, minLon, maxLat, maxLon = bbox
        url = (
            "https://www.mapquestapi.com/traffic/v2/incidents"
            f"?key={api_key}&boundingBox={maxLat},{minLon},{minLat},{maxLon}&filters=construction,incidents"
        )
        data = fetch_json(session, url)
        incidents_raw = data.get("incidents", [])
        incidents = []
        for inc in incidents_raw:
            title = inc.get("typeDesc", "Traffic incident")
            desc = inc.get("fullDesc") or inc.get("shortDesc") or ""
            lat = inc.get("lat")
            lon = inc.get("lng")
            severity = inc.get("severity")
            incidents.append(TrafficIncident(title=title, description=desc, severity=severity, lat=lat, lon=lon))
        return Traffic(incidents=incidents, fetched_at=datetime.datetime.utcnow())
    except Exception:
        logger.exception("MapQuest traffic fetch failed")
        return Traffic(incidents=[], fetched_at=datetime.datetime.utcnow())


def get_traffic_here(session: requests.Session, bbox: Tuple[float, float, float, float], api_key: str) -> Traffic:
    """
    Example HERE Traffic API call (flow/incidents). This is a sketch: check HERE docs for exact params.
    """
    try:
        # HERE often expects a bounding box as "bbox=lat1,lon1;lat2,lon2"
        minLat, minLon, maxLat, maxLon = bbox
        bbox_param = f"{minLat},{minLon};{maxLat},{maxLon}"
        url = f"https://traffic.ls.hereapi.com/traffic/6.3/incidents.json?bbox={bbox_param}&apiKey={api_key}"
        data = fetch_json(session, url)
        incidents_raw = []
        # HERE's response structure is nested — this is conservative extraction
        try:
            poi = data.get("TRAFFIC_ITEMS", {}).get("TRAFFIC_ITEM", [])
            incidents_raw = poi
        except Exception:
            incidents_raw = []
        incidents = []
        for inc in incidents_raw:
            title = inc.get("TRAFFIC_ITEM_TYPE_DESC", "Traffic incident")
            desc = inc.get("TRAFFIC_ITEM_DESCRIPTION", [{}])[0].get("value", "")
            incidents.append(TrafficIncident(title=title, description=desc))
        return Traffic(incidents=incidents, fetched_at=datetime.datetime.utcnow())
    except Exception:
        logger.exception("HERE traffic fetch failed")
        return Traffic(incidents=[], fetched_at=datetime.datetime.utcnow())


def get_traffic(session: requests.Session, provider: str, center_coords: Tuple[float, float], radius_km: float, api_key: Optional[str]) -> Traffic:
    """
    Generic wrapper to fetch traffic from a provider in a bounding box around center_coords.
    - provider: 'mapquest' or 'here' or ''
    - center_coords: (lat, lon)
    - radius_km: radius size for bbox
    """
    if not provider:
        return Traffic(incidents=[], fetched_at=datetime.datetime.utcnow())
    if not api_key:
        logger.warning("Traffic provider configured but no API key supplied")
        return Traffic(incidents=[], fetched_at=datetime.datetime.utcnow())

    lat, lon = center_coords
    # Create crude bounding box ~ radius_km (approx, degrees)
    # 1 deg latitude ~ 111km; 1 deg longitude ~ 111km * cos(lat)
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(0.1, abs(math.cos(math.radians(lat)))))
    minLat, maxLat = lat - dlat, lat + dlat
    minLon, maxLon = lon - dlon, lon + dlon
    bbox = (minLat, minLon, maxLat, maxLon)

    if provider == "mapquest":
        return get_traffic_mapquest(session, bbox, api_key)
    if provider == "here":
        return get_traffic_here(session, bbox, api_key)
    logger.warning("Unsupported traffic provider: %s", provider)
    return Traffic(incidents=[], fetched_at=datetime.datetime.utcnow())


def build_briefing_text(station: str, weather: Weather, traffic: Traffic, always_speak: bool = False) -> str:
    """
    Build a plain-language briefing string. If OPENAI_API_KEY is set, optionally call OpenAI to rewrite it to be more natural.
    """
    # Basic assembly
    now = datetime.datetime.now().strftime("%A, %B %d at %I:%M %p")
    parts = [
        f"Good day. You are listening to {station}.",
        f"The time is {now}.",
    ]
    if weather.short_forecast or weather.temperature is not None:
        temp_text = f"{weather.temperature} degrees" if weather.temperature is not None else "an unknown temperature"
        forecast_text = weather.short_forecast or ""
        wind_text = f"Wind {weather.wind}." if weather.wind else ""
        parts.append(f"Weather: {forecast_text}. Temperature: {temp_text}. {wind_text}")
    else:
        parts.append("Weather information is currently unavailable.")

    # Traffic summary
    parts.append(traffic.summary())

    # Closing
    parts.append("Drive safely and have a blessed day.")

    plain = " ".join(parts).strip()

    # Optionally use OpenAI to rewrite to sound nicer
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai and always_speak is False:
        # Use OpenAI only for refinement — keep fallback if anything fails
        try:
            openai.api_key = openai_key
            prompt = (
                "Rewrite the following short radio briefing to sound natural and warm for listeners, "
                "keeping the content but making it concise (50-90 words):\n\n"
                f"{plain}\n\nRewritten:"
            )
            logger.debug("Calling OpenAI to rewrite briefing")
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini" if hasattr(openai, "ChatCompletion") else "gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=180,
                temperature=0.6,
            )
            # ChatCompletion vs Completion shapes; attempt robust extraction
            if "choices" in resp and resp["choices"]:
                rewritten = resp["choices"][0]["message"]["content"].strip() if "message" in resp["choices"][0] else resp["choices"][0].get("text", "").strip()
                if rewritten:
                    logger.debug("OpenAI rewrite success")
                    return rewritten
        except Exception:
            logger.exception("OpenAI rewrite failed; using plain briefing")
    return plain


def speak_text(text: str, voice_rate: Optional[int] = None):
    """
    Speak text live. Prefer pyttsx3 (offline). Fallback to gTTS + pydub play.
    """
    logger.info("Speaking briefing (approx %d chars)", len(text))
    if pyttsx3:
        try:
            engine = pyttsx3.init()
            if voice_rate:
                try:
                    engine.setProperty("rate", voice_rate)
                except Exception:
                    pass
            # run in non-blocking thread to avoid blocking main loop; but ensure we wait for it to finish before starting next
            finished = threading.Event()

            def on_end(name, completed):
                finished.set()

            try:
                engine.connect("finished-utterance", on_end)
            except Exception:
                # some implementations don't expose this hook; fallback to runAndWait
                pass

            engine.say(text)
            engine.runAndWait()
            # if event approach failed, runAndWait returned after speak finishes
            return
        except Exception:
            logger.exception("pyttsx3 failed; falling back to gTTS")

    # Fallback: gTTS -> pydub playback
    if gTTS and AudioSegment and play_audio:
        try:
            tts = gTTS(text=text, lang="en", slow=False)
            tmp = Path(".") / f"_mb_{int(time.time())}.mp3"
            tts.save(str(tmp))
            audio = AudioSegment.from_file(str(tmp))
            play_audio(audio)
            try:
                tmp.unlink()
            except Exception:
                pass
            return
        except Exception:
            logger.exception("gTTS/pydub playback failed")

    # Final fallback: print and leave it to the user
    logger.warning("No TTS available: printing briefing instead\n\n%s\n", text)


import math


def coords_to_tuple(coords: str) -> Tuple[float, float]:
    lat_s, lon_s = coords.split(",")
    return float(lat_s.strip()), float(lon_s.strip())


def bounding_box(center: Tuple[float, float], radius_km: float) -> Tuple[float, float, float, float]:
    lat, lon = center
    dlat = radius_km / 111.0
    dlon = radius_km / (111.0 * max(0.1, abs(math.cos(math.radians(lat)))))
    return (lat - dlat, lon - dlon, lat + dlat, lon + dlon)


def run_loop(
    coords: str,
    station: str,
    poll_interval: int,
    traffic_provider: str,
    traffic_api_key: Optional[str],
    traffic_radius_km: float,
    openai_refine: bool,
    speak_on_change_only: bool,
):
    session = build_session()
    center = coords_to_tuple(coords)
    last_weather_json = None
    last_traffic_json = None

    logger.info("Starting loop: coords=%s station=%s interval=%ds traffic=%s", coords, station, poll_interval, traffic_provider or "none")

    while True:
        try:
            # Weather
            weather = get_weather(session, coords)

            # Traffic (if configured)
            if traffic_provider:
                bbox = bounding_box(center, traffic_radius_km)
                traffic = get_traffic(session, traffic_provider, center, traffic_radius_km, traffic_api_key)
            else:
                traffic = Traffic(incidents=[], fetched_at=datetime.datetime.utcnow())

            # Decide whether to speak
            cur_weather_json = json.dumps(weather.to_dict(), sort_keys=True)
            cur_traffic_json = json.dumps([inc.__dict__ for inc in traffic.incidents], sort_keys=True)
            changed = (cur_weather_json != last_weather_json) or (cur_traffic_json != last_traffic_json)

            if (not speak_on_change_only) or changed:
                text = build_briefing_text(station, weather, traffic, always_speak=not openai_refine)
                speak_text(text)
                last_weather_json = cur_weather_json
                last_traffic_json = cur_traffic_json
            else:
                logger.debug("No change detected; not speaking this cycle")

        except Exception:
            logger.exception("Main loop iteration failed")

        # Sleep until next poll
        time.sleep(poll_interval)


def parse_args():
    parser = argparse.ArgumentParser(description="Live Weather+Traffic Morning Broadcast")
    parser.add_argument("--coords", default=DEFAULT_COORDS, help="Latitude,Longitude for weather")
    parser.add_argument("--station", default=DEFAULT_STATION, help="Station name spoken in briefing")
    parser.add_argument("--interval", type=int, default=DEFAULT_POLL_INTERVAL, help="Polling interval in seconds")
    parser.add_argument("--traffic-provider", choices=["", "mapquest", "here"], default=os.getenv("TRAFFIC_PROVIDER", ""), help="Traffic provider")
    parser.add_argument("--traffic-key", default=os.getenv("TRAFFIC_API_KEY", None), help="Traffic API key")
    parser.add_argument("--traffic-radius", type=float, default=float(os.getenv("TRAFFIC_RADIUS_KM", "10")), help="Traffic bounding radius in km")
    parser.add_argument("--openai-refine", action="store_true", help="If set and OPENAI_API_KEY provided, refine text with OpenAI")
    parser.add_argument("--always-speak", action="store_true", help="Speak every poll even if no change")
    parser.add_argument("--once", action="store_true", help="Run a single fetch and speak (for cron or manual invocation)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)

    # If openai-refine requested but openai library missing, warn
    if args.openai_refine and (openai is None or not os.getenv("OPENAI_API_KEY")):
        logger.warning("OpenAI refinement requested but openai library or OPENAI_API_KEY is missing. Skipping refinement.")

    if args.once:
        # Perform one poll and exit
        session = build_session()
        try:
            weather = get_weather(session, args.coords)
            if args.traffic_provider:
                center = coords_to_tuple(args.coords)
                traffic = get_traffic(session, args.traffic_provider, center, args.traffic_radius, args.traffic_key)
            else:
                traffic = Traffic(incidents=[], fetched_at=datetime.datetime.utcnow())
            text = build_briefing_text(args.station, weather, traffic, always_speak=not args.openai_refine)
            speak_text(text)
        except Exception:
            logger.exception("One-shot run failed")
        return

def main():

    print("Starting Delaware All Saints Global Morning Broadcast")

    try:
        weather = get_weather()

    except Exception as e:
        print(f"Weather error: {e}")

        weather = {
            "temp": "unavailable",
            "condition": "weather data unavailable",
            "wind": "unavailable",
            "humidity": "Not available"
        }

    script = build_script(weather)

    print(script)

    create_audio(script)

    print("Broadcast MP3 created successfully.")


if __name__ == "__main__":
    main()
