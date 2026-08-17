"""
Google Calendar API reader.

Reads availability from multiple Google Calendars
and returns one combined list of events.

Events from MOVABLE calendars are marked as movable.
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

        all_events = []

        print()
        print("Reading Google Calendars...")

        for calendar_id in config.CALENDAR_IDS:

            print(
                f"Reading calendar: {calendar_id}"
            )

            try:

                result = (
                    self.service
                    .events()
                    .list(
                        calendarId=calendar_id,
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

                print(
                    f"Found {len(events)} events"
                )

                # ------------------------------------------------
                # Add source calendar information to every event.
                # ------------------------------------------------

                for event in events:

                    event["_source_calendar_id"] = calendar_id

                    # ------------------------------------------------
                    # Diagnostic information.
                    # ------------------------------------------------

                    start_data = event.get(
                        "start",
                        {}
                    )

                    end_data = event.get(
                        "end",
                        {}
                    )

                    start_value = (
                        start_data.get("dateTime")
                        or start_data.get("date")
                    )

                    end_value = (
                        end_data.get("dateTime")
                        or end_data.get("date")
                    )

                    summary = event.get(
                        "summary",
                        "(без назви)"
                    )

                    color_id = event.get(
                        "colorId",
                        ""
                    )

                    print(
                        f"  EVENT: {summary}"
                    )

                    print(
                        f"         "
                        f"{start_value} -> {end_value}"
                    )

                    print(
                        f"         "
                        f"Calendar: {calendar_id}"
                    )

                    print(
                        f"         "
                        f"colorId: {color_id or '(calendar color)'}"
                    )

                all_events.extend(
                    events
                )

            except Exception as error:

                print(
                    f"ERROR reading calendar "
                    f"{calendar_id}: {error}"
                )

        # ============================================================
        # REMOVE EXACT DUPLICATES
        # ============================================================

        unique_events = []

        seen = set()

        for event in all_events:

            start_data = event.get(
                "start",
                {}
            )

            end_data = event.get(
                "end",
                {}
            )

            start_value = (
                start_data.get("dateTime")
                or start_data.get("date")
            )

            end_value = (
                end_data.get("dateTime")
                or end_data.get("date")
            )

            summary = event.get(
                "summary",
                ""
            )

            duplicate_key = (
                summary,
                start_value,
                end_value,
            )

            if duplicate_key in seen:
                continue

            seen.add(
                duplicate_key
            )

            unique_events.append(
                event
            )

        print()

        print(
            f"Total unique events: "
            f"{len(unique_events)}"
        )

        return unique_events
