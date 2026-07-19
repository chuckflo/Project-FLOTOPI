#!/usr/bin/env python3

import re
import subprocess
from datetime import datetime

STATION_CALLSIGN = "AK6QN-10"
MAX_EVENTS = 12

JOURNAL_LINE = re.compile(
    r"^(?P<timestamp>\S+)\s+\S+\s+direwolf\[\d+\]:\s+(?P<message>.*)$"
)

RF_PACKET = re.compile(
    r"^\[[^\]]+\]\s+"
    r"(?P<source>[A-Z0-9-]+)>"
    r"(?P<path>[^:]+):"
    r"(?P<payload>.*)$"
)

IGATE_PACKET = re.compile(
    r"^\[ig>tx\]\s+"
    r"(?P<source>[A-Z0-9-]+)>"
    r"(?P<path>[^:]+):"
    r"(?P<payload>.*)$"
)


def read_direwolf_log(hours=1):
    """Read recent Direwolf journal entries."""
    command = [
        "journalctl",
        "-u",
        "direwolf.service",
        "--since",
        f"{hours} hour ago",
        "--no-pager",
        "--output=short-iso",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
        )
        return result.stdout.splitlines()
    except (subprocess.SubprocessError, OSError):
        return []


def format_time(timestamp):
    """Convert an ISO journal timestamp to local display time."""
    try:
        parsed = datetime.fromisoformat(timestamp)
        return parsed.strftime("%-I:%M:%S %p")
    except ValueError:
        return timestamp


def identify_packet_type(payload):
    """Classify an APRS packet from its data-type identifier."""
    if not payload:
        return "Unknown"

    if payload.startswith("T#"):
        return "Telemetry"

    packet_identifier = payload[0]

    packet_types = {
        "!": "Position",
        "=": "Position",
        "/": "Position",
        "@": "Position",
        "`": "Mic-E Position",
        "'": "Mic-E Position",
        "_": "Weather",
        ":": "Message",
        ";": "Object",
        ")": "Item",
        ">": "Status",
        "?": "Query",
        "}": "Third-Party",
        "{": "User Defined",
    }

    return packet_types.get(packet_identifier, "Other")


def create_event(timestamp, action, source, payload):
    """Create one structured activity event."""
    return {
        "time": format_time(timestamp),
        "action": action,
        "station": source,
        "packet_type": identify_packet_type(payload),
    }


def parse_activity(lines):
    """Convert Direwolf journal lines into structured APRS events."""
    events = []
    seen = set()

    for line in reversed(lines):
        journal_match = JOURNAL_LINE.match(line)
        if not journal_match:
            continue

        timestamp = journal_match.group("timestamp")
        message = journal_match.group("message")

        igate_match = IGATE_PACKET.match(message)

        if igate_match:
            event = create_event(
                timestamp=timestamp,
                action="IGated",
                source=igate_match.group("source"),
                payload=igate_match.group("payload"),
            )

        else:
            packet_match = RF_PACKET.match(message)
            if not packet_match:
                continue

            source = packet_match.group("source")
            path = packet_match.group("path")
            payload = packet_match.group("payload")

            if source == STATION_CALLSIGN:
                action = "Beacon Sent"
            elif f"{STATION_CALLSIGN}*" in path:
                action = "Digipeated"
            else:
                action = "Heard"

            event = create_event(
                timestamp=timestamp,
                action=action,
                source=source,
                payload=payload,
            )

        event_key = (
            timestamp,
            event["action"],
            event["station"],
            event["packet_type"],
        )

        if event_key in seen:
            continue

        seen.add(event_key)
        events.append(event)

        if len(events) >= MAX_EVENTS:
            break

    return list(reversed(events))


def main():
    lines = read_direwolf_log(hours=1)
    events = parse_activity(lines)

    if not events:
        print("No recent APRS activity found.")
        return

    print("\nRecent APRS Activity\n")

    for event in events:
        print(
            f"{event['time']:>11}  "
            f"{event['action']:<12}  "
            f"{event['station']:<12}  "
            f"{event['packet_type']}"
        )


def get_recent_activity(hours=1, max_events=8):
    """
    Return recent APRS activity as a list of dictionaries.
    """
    global MAX_EVENTS
    MAX_EVENTS = max_events

    lines = read_direwolf_log(hours=hours)
    return parse_activity(lines)


if __name__ == "__main__":
    main()
