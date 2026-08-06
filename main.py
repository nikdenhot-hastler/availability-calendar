"""
Availability Calendar
Main entry point

Author: Nik
"""

from pathlib import Path

import config
from calendar_api import CalendarReader


def initialize():
    """
    Prepare folders before application starts.
    """

    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():

    initialize()

    print("=" * 50)
    print("Availability Calendar")
    print("=" * 50)

    print(f"Calendar : {config.CALENDAR_ID}")
    print(f"Timezone : {config.TIMEZONE}")
    print(f"Days      : {config.DAYS_TO_SHOW}")

    print()

    print("Project initialized successfully.")
    print("Waiting for calendar module...")
    reader = CalendarReader()
reader.print_events()


if __name__ == "__main__":
    main()
