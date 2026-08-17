"""
Google Calendar API module.

Reads Google Calendar events.
Event titles are never used by the availability image.
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

        now = datetime.now(
            timezone
        )

        end = (
            now
            + timedelta(
                days=config.DAYS_TO_SHOW
            )
        )

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

        return result.get(
            "items",
            []
        )
