"""
Google Calendar API reader.

Reads availability from one or more Google Calendars
and returns one combined list of events.

Individual event colorId is preserved because it is used
to determine whether an event can be rescheduled.
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


    # ========================================================
    # GET EVENTS
    # ========================================================

    def get_events(self):

        timezone = pytz.timezone(
            config.TIMEZONE
        )

        now = datetime.now(
            timezone
        )

        end = (
            now
            + timedelta(
                days=config.DAYS_TO_SHOW
            )
        )

        all_events = []

        print()
        print(
            "Reading Google Calendars..."
        )


        # ====================================================
        # READ EACH CALENDAR
        # ====================================================

        for calendar_id in config.CALENDAR_IDS:

            print()
            print(
                f"Reading calendar: "
                f"{calendar_id}"
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


                # ============================================
                # STORE REQUIRED INFORMATION
                # ============================================

                for event in events:

                    event[
                        "_source_calendar_id"
                    ] = calendar_id

                    event_color_id = event.get(
                        "colorId",
                        ""
                    )

                    event[
                        "_event_color_id"
                    ] = str(
                        event_color_id
                    )


                all_events.extend(
                    events
                )


            except Exception as error:

                print(
                    f"ERROR reading calendar "
                    f"{calendar_id}: {error}"
                )


        # ====================================================
        # REMOVE EXACT DUPLICATES
        # ====================================================

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
                start_data.get(
                    "dateTime"
                )
                or start_data.get(
                    "date"
                )
            )

            end_value = (
                end_data.get(
                    "dateTime"
                )
                or end_data.get(
                    "date"
                )
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


    # ========================================================
    # PRINT EVENTS
    # ========================================================

    def print_events(self):

        events = self.get_events()

        print()

        for event in events:

            start = event.get(
                "start",
                {}
            )

            end = event.get(
                "end",
                {}
            )

            start_value = (
                start.get("dateTime")
                or start.get("date")
            )

            end_value = (
                end.get("dateTime")
                or end.get("date")
            )

            title = event.get(
                "summary",
                "(No title)"
            )

            color_id = event.get(
                "colorId",
                ""
            )

            print(
                f"START : {start_value}"
            )

            print(
                f"END   : {end_value}"
            )

            print(
                f"TITLE : {title}"
            )

            print(
                f"COLOR : "
                f"{color_id or '(default)'}"
            )

            print(
                f"STATUS: "
                f"{event.get('status', '(unknown)')}"
            )

            print(
                "-" * 40
            )