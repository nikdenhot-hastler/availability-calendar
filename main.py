"""
Diagnostic main.py

Reads Google Calendar and prints the exact start/end
times of events visible to the service account.

No event titles are printed.
"""

from datetime import datetime

import pytz

from calendar_api import CalendarReader
import config


def main():

    print("=" * 60)
    print("GOOGLE CALENDAR DIAGNOSTIC")
    print("=" * 60)

    timezone = pytz.timezone(config.TIMEZONE)

    now = datetime.now(timezone)

    print()
    print(f"Calendar ID : {config.CALENDAR_ID}")
    print(f"Timezone    : {config.TIMEZONE}")
    print(
        f"Current time: "
        f"{now.strftime('%Y-%m-%d %H:%M:%S %Z')}"
    )
    print(
        f"Days to show: "
        f"{config.DAYS_TO_SHOW}"
    )

    print()
    print("-" * 60)
    print("Reading Google Calendar...")
    print("-" * 60)

    reader = CalendarReader()

    events = reader.get_events()

    print()
    print(f"FOUND EVENTS: {len(events)}")
    print()

    if not events:

        print("NO EVENTS FOUND.")
        print()

    else:

        print("=" * 60)
        print("EVENT TIMES")
        print("=" * 60)

        for number, event in enumerate(
            events,
            start=1
        ):

            start_data = event.get(
                "start",
                {}
            )

            end_data = event.get(
                "end",
                {}
            )

            # Timed event
            if "dateTime" in start_data:

                start = start_data[
                    "dateTime"
                ]

                end = end_data[
                    "dateTime"
                ]

                event_type = "TIMED"

            # All-day event
            elif "date" in start_data:

                start = start_data[
                    "date"
                ]

                end = end_data[
                    "date"
                ]

                event_type = "ALL-DAY"

            else:

                start = "UNKNOWN"
                end = "UNKNOWN"
                event_type = "UNKNOWN"

            print()
            print(f"EVENT #{number}")
            print(f"Type : {event_type}")
            print(f"Start: {start}")
            print(f"End  : {end}")
            print("-" * 40)

    print()
    print("=" * 60)
    print("DIAGNOSTIC FINISHED")
    print("=" * 60)


if __name__ == "__main__":
    main()
