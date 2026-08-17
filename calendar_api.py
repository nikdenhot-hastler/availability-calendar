"""
Google Calendar API reader.
"""

from datetime import datetime, timedelta

import pytz

from google.oauth2 import service_account
from googleapiclient.discovery import build

import config


SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly"
]


class CalendarReader:

    def __init__(self):

        credentials = (
            service_account
            .Credentials
            .from_service_account_file(
                config.SERVICE_ACCOUNT_FILE,
                scopes=SCOPES,
            )
        )

        self.service = build(
            "calendar",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )

    def get_events(self):

        timezone = pytz.timezone(
            config.TIMEZONE
        )

        now = datetime.now(timezone)

        end = (
            now
            + timedelta(
                days=config.DAYS_TO_SHOW
            )
        )

        print()
        print("=" * 60)
        print("GOOGLE CALENDAR ACCESS TEST")
        print("=" * 60)

        print()
        print(
            f"Calendar ID: "
            f"{config.CALENDAR_ID}"
        )

        print()
        print("Reading calendar...")

        result = (
            self.service
            .events()
            .list(
                calendarId=config.CALENDAR_ID,
                timeMin=now.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = result.get(
            "items",
            []
        )

        print()
        print(
            f"FOUND EVENTS: {len(events)}"
        )

        print()
        print("=" * 60)
        print("EVENTS")
        print("=" * 60)

        for number, event in enumerate(
            events,
            start=1,
        ):

            title = event.get(
                "summary",
                "(No title)"
            )

            start = event.get(
                "start",
                {}
            )

            end_data = event.get(
                "end",
                {}
            )

            start_value = (
                start.get("dateTime")
                or start.get("date")
            )

            end_value = (
                end_data.get("dateTime")
                or end_data.get("date")
            )

            print()
            print(
                f"EVENT #{number}"
            )

            print(
                f"Title : {title}"
            )

            print(
                f"Start : {start_value}"
            )

            print(
                f"End   : {end_value}"
            )

            print(
                "-" * 40
            )

        print()
        print("=" * 60)
        print("DIAGNOSTIC FINISHED")
        print("=" * 60)

        return events
