"""
Diagnostic main application for availability calendar.
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
    print(f"Current time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"Days to show: {config.DAYS_TO_SHOW}")

    print()
    print("-" * 60)
    print("Reading Google Calendar...")
    print("-" * 60)

    reader = CalendarReader()

    try:
        events = reader.get_events()
    except Exception as error:
        print()
        print("ERROR while reading Google Calendar:")
        print(type(error).__name__)
        print(str(error))
        raise

    print()
    print(f"FOUND EVENTS: {len(events)}")
    print()

    if not events:
        print("NO EVENTS FOUND.")
        print()
        print("The service account does not see any future events")
        print("in the requested 14-day period.")
        print()
    else:

        print("=" * 60)
        print("EVENTS VISIBLE TO SERVICE ACCOUNT")
        print("=" * 60)

        for number, event in enumerate(events, start=1):

            start_data = event.get("start", {})
            end_data = event.get("end", {})

            start = start_data.get(
                "dateTime",
                start_data.get("date", "UNKNOWN")
            )

            end = end_data.get(
                "dateTime",
                end_data.get("date", "UNKNOWN")
            )

            status = event.get("status", "UNKNOWN")

            print()
            print(f"EVENT #{number}")
            print(f"Start : {start}")
            print(f"End   : {end}")
            print(f"Status: {status}")
            print("-" * 40)

    print()
    print("=" * 60)
    print("DIAGNOSTIC FINISHED")
    print("=" * 60)


if __name__ == "__main__":
    main()
