"""
Google Calendar — automatic synchronization.

SOURCE:
    vmedyk@gmail.com

TARGET:
    nik.den.hot@gmail.com

RULES:

    Source event colorId == "6"
        -> movable
        -> target colorId == "6"

    Any other source color
        -> busy
        -> target colorId == "11"

Automatic copies are marked with:

    extendedProperties.private.sync_marker
        = "vmedyk_auto_copy"

The source event ID is stored in:

    extendedProperties.private.source_event_id
"""

from datetime import datetime, timedelta

import pytz

from google.oauth2 import service_account
from googleapiclient.discovery import build

import config


# ============================================================
# CONFIGURATION
# ============================================================

SOURCE_CALENDAR = "vmedyk@gmail.com"
TARGET_CALENDAR = "nik.den.hot@gmail.com"

SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]

MOVABLE_COLOR_ID = "6"

# Google Calendar event color:
# 11 = red
BUSY_COLOR_ID = "11"

SYNC_MARKER = "vmedyk_auto_copy"

SYNC_DAYS = 60


# ============================================================
# GOOGLE CALENDAR
# ============================================================

def get_service():

    credentials = (
        service_account
        .Credentials.from_service_account_file(
            config.SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
        )
    )

    return build(
        "calendar",
        "v3",
        credentials=credentials,
        cache_discovery=False,
    )


# ============================================================
# TIME RANGE
# ============================================================

def get_period():

    timezone = pytz.timezone(
        config.TIMEZONE
    )

    now = datetime.now(
        timezone
    )

    end = (
        now
        + timedelta(
            days=SYNC_DAYS
        )
    )

    return now, end


# ============================================================
# READ SOURCE EVENTS
# ============================================================

def get_source_events(
    service,
    time_min,
    time_max,
):

    print()
    print(
        "Reading source calendar..."
    )

    result = (
        service
        .events()
        .list(
            calendarId=SOURCE_CALENDAR,
            timeMin=time_min.isoformat(),
            timeMax=time_max.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=2500,
        )
        .execute()
    )

    events = result.get(
        "items",
        []
    )

    print(
        f"Source events: {len(events)}"
    )

    return events


# ============================================================
# READ TARGET EVENTS
# ============================================================

def get_target_events(
    service,
    time_min,
    time_max,
):

    print()
    print(
        "Reading target calendar..."
    )

    result = (
        service
        .events()
        .list(
            calendarId=TARGET_CALENDAR,
            timeMin=time_min.isoformat(),
            timeMax=time_max.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=2500,
        )
        .execute()
    )

    events = result.get(
        "items",
        []
    )

    print(
        f"Target events: {len(events)}"
    )

    return events


# ============================================================
# AUTOMATIC COPY INDEX
# ============================================================

def build_copy_index(
    target_events,
):

    copies = {}

    for event in target_events:

        private_props = (
            event
            .get(
                "extendedProperties",
                {}
            )
            .get(
                "private",
                {}
            )
        )

        marker = private_props.get(
            "sync_marker"
        )

        source_event_id = private_props.get(
            "source_event_id"
        )

        if (
            marker == SYNC_MARKER
            and source_event_id
        ):

            copies[source_event_id] = event

    return copies


# ============================================================
# EVENT STATUS
# ============================================================

def get_status(
    source_event,
):

    color_id = str(
        source_event.get(
            "colorId",
            ""
        )
    ).strip()

    if color_id == MOVABLE_COLOR_ID:

        return (
            "movable",
            MOVABLE_COLOR_ID,
        )

    return (
        "busy",
        BUSY_COLOR_ID,
    )


# ============================================================
# COPY START / END
# ============================================================

def copy_datetime_fields(
    source_event,
):

    start = source_event.get(
        "start",
        {}
    )

    end = source_event.get(
        "end",
        {}
    )

    result_start = {}

    result_end = {}

    # --------------------------------------------------------
    # ALL DAY
    # --------------------------------------------------------

    if "date" in start:

        result_start["date"] = start[
            "date"
        ]

        result_end["date"] = end[
            "date"
        ]

    # --------------------------------------------------------
    # TIMED
    # --------------------------------------------------------

    else:

        result_start["dateTime"] = start[
            "dateTime"
        ]

        result_start["timeZone"] = start.get(
            "timeZone",
            config.TIMEZONE
        )

        result_end["dateTime"] = end[
            "dateTime"
        ]

        result_end["timeZone"] = end.get(
            "timeZone",
            config.TIMEZONE
        )

    return (
        result_start,
        result_end,
    )


# ============================================================
# BUILD TARGET EVENT
# ============================================================

def build_target_event(
    source_event,
):

    source_id = source_event[
        "id"
    ]

    title = source_event.get(
        "summary",
        "Зайнято"
    )

    status, target_color = get_status(
        source_event
    )

    start, end = copy_datetime_fields(
        source_event
    )

    target_event = {

        "summary": title,

        "start": start,

        "end": end,

        "colorId": target_color,

        "extendedProperties": {

            "private": {

                "sync_marker":
                    SYNC_MARKER,

                "source_event_id":
                    source_id,

                "availability_status":
                    status,

            }
        }
    }

    return target_event


# ============================================================
# CREATE
# ============================================================

def create_copy(
    service,
    source_event,
):

    target_event = build_target_event(
        source_event
    )

    created = (
        service
        .events()
        .insert(
            calendarId=TARGET_CALENDAR,
            body=target_event,
        )
        .execute()
    )

    return created


# ============================================================
# UPDATE
# ============================================================

def update_copy(
    service,
    target_event,
    source_event,
):

    target_id = target_event[
        "id"
    ]

    updated_body = build_target_event(
        source_event
    )

    updated = (
        service
        .events()
        .update(
            calendarId=TARGET_CALENDAR,
            eventId=target_id,
            body=updated_body,
        )
        .execute()
    )

    return updated


# ============================================================
# COMPARE
# ============================================================

def events_are_equal(
    target_event,
    source_event,
):

    expected = build_target_event(
        source_event
    )

    target_start = target_event.get(
        "start",
        {}
    )

    target_end = target_event.get(
        "end",
        {}
    )

    expected_start = expected[
        "start"
    ]

    expected_end = expected[
        "end"
    ]

    # --------------------------------------------------------
    # TITLE
    # --------------------------------------------------------

    if target_event.get(
        "summary"
    ) != expected.get(
        "summary"
    ):

        return False

    # --------------------------------------------------------
    # COLOR
    # --------------------------------------------------------

    if str(
        target_event.get(
            "colorId",
            ""
        )
    ) != str(
        expected.get(
            "colorId",
            ""
        )
    ):

        return False

    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    if target_start.get(
        "date"
    ) != expected_start.get(
        "date"
    ):

        if target_start.get(
            "dateTime"
        ) != expected_start.get(
            "dateTime"
        ):

            return False

    # --------------------------------------------------------
    # END
    # --------------------------------------------------------

    if target_end.get(
        "date"
    ) != expected_end.get(
        "date"
    ):

        if target_end.get(
            "dateTime"
        ) != expected_end.get(
            "dateTime"
        ):

            return False

    # --------------------------------------------------------
    # STATUS
    # --------------------------------------------------------

    target_private = (
        target_event
        .get(
            "extendedProperties",
            {}
        )
        .get(
            "private",
            {}
        )
    )

    expected_private = (
        expected
        .get(
            "extendedProperties",
            {}
        )
        .get(
            "private",
            {}
        )
    )

    if target_private.get(
        "availability_status"
    ) != expected_private.get(
        "availability_status"
    ):

        return False

    return True


# ============================================================
# DELETE
# ============================================================

def delete_copy(
    service,
    target_event,
):

    (
        service
        .events()
        .delete(
            calendarId=TARGET_CALENDAR,
            eventId=target_event["id"],
        )
        .execute()
    )


# ============================================================
# MAIN SYNC
# ============================================================

def main():

    print()
    print("=" * 60)
    print(
        "GOOGLE CALENDAR — FULL SYNC"
    )
    print("=" * 60)

    print()
    print(
        f"SOURCE : {SOURCE_CALENDAR}"
    )

    print(
        f"TARGET : {TARGET_CALENDAR}"
    )

    time_min, time_max = get_period()

    print()
    print("PERIOD:")

    print(
        f"FROM   : {time_min.isoformat()}"
    )

    print(
        f"TO     : {time_max.isoformat()}"
    )

    service = get_service()

    # --------------------------------------------------------
    # READ
    # --------------------------------------------------------

    source_events = get_source_events(
        service,
        time_min,
        time_max,
    )

    target_events = get_target_events(
        service,
        time_min,
        time_max,
    )

    copy_index = build_copy_index(
        target_events
    )

    print()
    print(
        f"Automatic copies: "
        f"{len(copy_index)}"
    )

    # --------------------------------------------------------
    # SYNC
    # --------------------------------------------------------

    created_count = 0
    updated_count = 0
    unchanged_count = 0
    deleted_count = 0

    source_ids = set()

    for source_event in source_events:

        source_id = source_event.get(
            "id"
        )

        if not source_id:

            continue

        source_ids.add(
            source_id
        )

        title = source_event.get(
            "summary",
            "(No title)"
        )

        start = source_event.get(
            "start",
            {}
        )

        end = source_event.get(
            "end",
            {}
        )

        start_text = start.get(
            "dateTime",
            start.get(
                "date",
                ""
            )
        )

        end_text = end.get(
            "dateTime",
            end.get(
                "date",
                ""
            )
        )

        source_color = str(
            source_event.get(
                "colorId",
                ""
            )
        ).strip()

        status, target_color = get_status(
            source_event
        )

        print()
        print("-" * 60)

        print(
            f"EVENT: {title}"
        )

        print(
            f"START: {start_text}"
        )

        print(
            f"END  : {end_text}"
        )

        print(
            f"SOURCE COLOR: "
            f"{source_color or '(default)'}"
        )

        print(
            f"STATUS: {status}"
        )

        print(
            f"TARGET COLOR: {target_color}"
        )

        # ----------------------------------------------------
        # CREATE
        # ----------------------------------------------------

        if source_id not in copy_index:

            print(
                "ACTION: CREATE"
            )

            created = create_copy(
                service,
                source_event,
            )

            print(
                f"CREATED: "
                f"{created['id']}"
            )

            created_count += 1

            continue

        # ----------------------------------------------------
        # EXISTING
        # ----------------------------------------------------

        target_event = copy_index[
            source_id
        ]

        if events_are_equal(
            target_event,
            source_event,
        ):

            print(
                "ACTION: UNCHANGED"
            )

            unchanged_count += 1

        else:

            print(
                "ACTION: UPDATE"
            )

            updated = update_copy(
                service,
                target_event,
                source_event,
            )

            print(
                f"UPDATED: "
                f"{updated['id']}"
            )

            updated_count += 1

    # --------------------------------------------------------
    # DELETE COPIES WHOSE SOURCE EVENTS NO LONGER EXIST
    # --------------------------------------------------------

    print()
    print(
        "CHECKING FOR DELETED SOURCE EVENTS"
    )

    for source_id, target_event in copy_index.items():

        if source_id in source_ids:

            continue

        print()
        print(
            "DELETE AUTOMATIC COPY:"
        )

        print(
            f"ID    : "
            f"{target_event['id']}"
        )

        print(
            f"TITLE : "
            f"{target_event.get('summary', '')}"
        )

        delete_copy(
            service,
            target_event,
        )

        print(
            "DELETED"
        )

        deleted_count += 1

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print(
        "FULL SYNC COMPLETED"
    )
    print("=" * 60)

    print(
        f"Source events : {len(source_events)}"
    )

    print(
        f"Created       : {created_count}"
    )

    print(
        f"Updated       : {updated_count}"
    )

    print(
        f"Unchanged     : {unchanged_count}"
    )

    print(
        f"Deleted       : {deleted_count}"
    )

    print("=" * 60)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()