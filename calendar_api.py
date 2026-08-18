"""
Google Calendar API reader.

Reads availability from multiple Google Calendars
and returns one combined list of events.

Events from calendars with colorId == "6"
(Tangerine / Мандарин) are marked as movable.
"""

from datetime import datetime, timedelta

import pytz

from google.oauth2 import service_account
from googleapiclient.discovery import build

import config


SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly"
]


# ============================================================
# GOOGLE CALENDAR STATUS
# ============================================================

# Google Calendar:
# 6 = Tangerine / Мандарин
MOVABLE_COLOR_ID = "6"


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
    # CALENDAR COLOR
    # ========================================================

    def _get_calendar_color_id(
        self,
        calendar_id,
    ):

        try:

            # IMPORTANT:
            # Calendar color is stored in CalendarListEntry,
            # NOT in the Calendar resource.
            calendar = (
                self.service
                .calendarList()
                .get(
                    calendarId=calendar_id,
                )
                .execute()
            )


            color_id = calendar.get(
                "colorId",
                "",
            )


            print(
                f"Calendar color: "
                f"{calendar_id} -> "
                f"{color_id or '(default)'}"
            )


            return str(
                color_id
            )


        except Exception as error:

            print(
                f"ERROR reading calendar color "
                f"for {calendar_id}: {error}"
            )


            return ""


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


            # ------------------------------------------------
            # Get actual color of the calendar.
            #
            # This is the critical part:
            # calendarList().get()
            # ------------------------------------------------

            calendar_color_id = (
                self._get_calendar_color_id(
                    calendar_id
                )
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
                # Add source calendar information
                # to every event.
                # ------------------------------------------------

                for event in events:

                    # Store source calendar ID.
                    event[
                        "_source_calendar_id"
                    ] = calendar_id


                    # Store source calendar color.
                    #
                    # This is later used by
                    # image_generator.py.
                    event[
                        "_calendar_color_id"
                    ] = calendar_color_id


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
                        "(без назви)"
                    )


                    event_color_id = event.get(
                        "colorId",
                        ""
                    )


                    print(
                        f"  EVENT: {summary}"
                    )


                    print(
                        f"         "
                        f"{start_value} -> "
                        f"{end_value}"
                    )


                    print(
                        f"         "
                        f"Calendar: "
                        f"{calendar_id}"
                    )


                    print(
                        f"         "
                        f"Event colorId: "
                        f"{event_color_id or '(calendar color)'}"
                    )


                    print(
                        f"         "
                        f"Calendar colorId: "
                        f"{calendar_color_id or '(default)'}"
                    )


                all_events.extend(
                    events
                )


            except Exception as error:

                print(
                    f"ERROR reading calendar "
                    f"{calendar_id}: {error}"
                )


        # ========================================================
        # REMOVE EXACT DUPLICATES
        # ========================================================

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