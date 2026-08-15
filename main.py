"""
Main application for availability calendar.
"""

from calendar_api import CalendarReader
from image_generator import AvailabilityImageGenerator
import config


def main():

    print("=" * 50)
    print("Availability Calendar")
    print("=" * 50)

    print(f"Calendar : {config.CALENDAR_ID}")
    print(f"Timezone : {config.TIMEZONE}")
    print(f"Days     : {config.DAYS_TO_SHOW}")
    print()

    print("Reading Google Calendar...")

    reader = CalendarReader()

    events = reader.get_events()

    print(f"Found {len(events)} events")

    print()
    print("Generating availability image...")

    generator = AvailabilityImageGenerator(events)

    generator.generate()

    print()
    print("Done.")


if __name__ == "__main__":
    main()