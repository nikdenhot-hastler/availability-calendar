"""
Availability image generator.

Generates public availability images from Google Calendar.

Statuses:

    FREE:
        No event.

    BUSY:
        Normal Google Calendar event.

    MOVABLE:
        Event from vmedyk@gmail.com
        OR event with Google Calendar colorId == "6".

The image does not display event titles
or private calendar information.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytz
from PIL import Image, ImageDraw, ImageFont

import config


# ============================================================
# LANGUAGE DATA
# ============================================================

UKRAINIAN_DAYS = {
    0: "пн",
    1: "вт",
    2: "ср",
    3: "чт",
    4: "пт",
    5: "сб",
    6: "нд",
}


UKRAINIAN_MONTHS = {
    1: "січ",
    2: "лют",
    3: "бер",
    4: "квіт",
    5: "трав",
    6: "черв",
    7: "лип",
    8: "серп",
    9: "верес",
    10: "жовт",
    11: "лист",
    12: "груд",
}


ENGLISH_DAYS = {
    0: "Mon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun",
}


ENGLISH_MONTHS = {
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}


# ============================================================
# GOOGLE CALENDAR STATUS
# ============================================================

MOVABLE_COLOR_ID = "6"

# All events from this calendar are movable.
MOVABLE_CALENDAR_ID = "vmedyk@gmail.com"


# ============================================================
# COLORS
# ============================================================

BACKGROUND = (17, 17, 17)

TEXT_PRIMARY = (235, 235, 235)

TEXT_SECONDARY = (175, 175, 175)

TEXT_MUTED = (105, 105, 105)

FREE = (190, 200, 184)

BUSY = (195, 55, 55)

MOVABLE = (205, 125, 55)

HOUR_LINE = (78, 85, 76)

DAY_BACKGROUND = (25, 25, 25)

WEEKEND = (145, 45, 45)

ACCENT = (115, 155, 105)


# ============================================================
# IMAGE / LAYOUT
# ============================================================

IMAGE_WIDTH = 1050

DAYS_TO_SHOW = 14

START_HOUR = 6

TOTAL_HOURS = 24

SECTORS = 12

HOURS_PER_SECTOR = 2


# ============================================================
# MARGINS
# ============================================================

MARGIN_LEFT = 28

MARGIN_RIGHT = 28


# ============================================================
# HEADER
# ============================================================

HEADER_TOP = 22

SUBTITLE_SIZE = 20

TITLE_SIZE = 36


# ============================================================
# TIMELINE
# ============================================================

TIME_SIZE = 24

DAY_LABEL_WIDTH = 190

BAR_X = (
    MARGIN_LEFT
    + DAY_LABEL_WIDTH
)


# ============================================================
# DAY ROWS
# ============================================================

DAY_SIZE = 24

DAY_START_Y = 120

DAY_HEIGHT = 68

BAR_HEIGHT = 34


# ============================================================
# LEGEND
# ============================================================

LEGEND_SIZE = 28

LEGEND_MARKER_SIZE = 34

LEGEND_ROW_HEIGHT = 58

LEGEND_TOP_GAP = 20

LEGEND_BOTTOM_GAP = 25


# ============================================================
# CLASS
# ============================================================

class AvailabilityImageGenerator:

    def __init__(self, events):

        self.events = events

        self.timezone = pytz.timezone(
            config.TIMEZONE
        )

        config.OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.font_path = self._font_path()

        self.width = IMAGE_WIDTH

        self.height = (
            DAY_START_Y
            + DAYS_TO_SHOW * DAY_HEIGHT
            + LEGEND_TOP_GAP
            + LEGEND_ROW_HEIGHT * 3
            + LEGEND_BOTTOM_GAP
        )


    # ========================================================
    # FONT
    # ========================================================

    def _font_path(self):

        local_font = getattr(
            config,
            "FONT_PATH",
            None,
        )

        if local_font:

            local_path = Path(
                local_font
            )

            if local_path.exists():

                return str(
                    local_path
                )


        linux_fonts = [

            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",

            "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",

        ]


        for font_path in linux_fonts:

            if Path(
                font_path
            ).exists():

                return font_path


        raise FileNotFoundError(
            "No usable font found."
        )


    def _font(self, size):

        return ImageFont.truetype(
            self.font_path,
            size,
        )


    # ========================================================
    # EVENT TIME PARSING
    # ========================================================

    def _parse_event_times(
        self,
        event,
    ):

        start_data = event.get(
            "start",
            {},
        )

        end_data = event.get(
            "end",
            {},
        )


        # ----------------------------------------------------
        # All-day event.
        # ----------------------------------------------------

        if "date" in start_data:

            start_date = datetime.strptime(
                start_data["date"],
                "%Y-%m-%d",
            )

            end_date = datetime.strptime(
                end_data["date"],
                "%Y-%m-%d",
            )

            start = self.timezone.localize(
                start_date
            )

            end = self.timezone.localize(
                end_date
            )

            return (
                start,
                end,
                True,
            )


        # ----------------------------------------------------
        # Timed event.
        # ----------------------------------------------------

        start = datetime.fromisoformat(
            start_data["dateTime"]
        )

        end = datetime.fromisoformat(
            end_data["dateTime"]
        )


        if start.tzinfo is None:

            start = self.timezone.localize(
                start
            )


        if end.tzinfo is None:

            end = self.timezone.localize(
                end
            )


        return (
            start.astimezone(
                self.timezone
            ),
            end.astimezone(
                self.timezone
            ),
            False,
        )


    # ========================================================
    # EVENT STATUS
    # ========================================================

    def _event_status(
        self,
        event,
    ):

        # ----------------------------------------------------
        # SOURCE CALENDAR
        # ----------------------------------------------------
        #
        # IMPORTANT:
        #
        # All events from vmedyk@gmail.com are movable.
        #
        # This is the original logic that was used before
        # the color-based logic was introduced.
        #
        # ----------------------------------------------------

        source_calendar = str(
            event.get(
                "_source_calendar_id",
                "",
            )
        )


        if (
            source_calendar
            == MOVABLE_CALENDAR_ID
        ):

            return "movable"


        # ----------------------------------------------------
        # EVENT COLOR
        # ----------------------------------------------------

        event_color_id = str(
            event.get(
                "colorId",
                "",
            )
        )


        if (
            event_color_id
            == MOVABLE_COLOR_ID
        ):

            return "movable"


        # ----------------------------------------------------
        # CALENDAR COLOR
        # ----------------------------------------------------

        calendar_color_id = str(
            event.get(
                "_calendar_color_id",
                "",
            )
        )


        if (
            calendar_color_id
            == MOVABLE_COLOR_ID
        ):

            return "movable"


        # ----------------------------------------------------
        # DEFAULT
        # ----------------------------------------------------

        return "busy"


    # ========================================================
    # DATE TEXT
    # ========================================================

    def _date_parts(
        self,
        date,
        language,
    ):

        if language == "uk":

            day_name = (
                UKRAINIAN_DAYS[
                    date.weekday()
                ]
            )

            date_text = (
                f"{date.day} "
                f"{UKRAINIAN_MONTHS[date.month]}"
            )

        else:

            day_name = (
                ENGLISH_DAYS[
                    date.weekday()
                ]
            )

            date_text = (
                f"{date.day:02d} "
                f"{ENGLISH_MONTHS[date.month]}"
            )


        return (
            day_name,
            date_text,
        )


    # ========================================================
    # HEADER
    # ========================================================

    def _draw_header(
        self,
        draw,
        language,
    ):

        subtitle_font = self._font(
            SUBTITLE_SIZE
        )

        title_font = self._font(
            TITLE_SIZE
        )


        if language == "uk":

            subtitle = (
                "МОЯ ПОТОЧНА ДОСТУПНІСТЬ:"
            )

            title = "ДОСТУПНІСТЬ"

        else:

            subtitle = (
                "MY CURRENT AVAILABILITY:"
            )

            title = "AVAILABILITY"


        draw.text(
            (
                MARGIN_LEFT,
                HEADER_TOP,
            ),
            subtitle,
            font=subtitle_font,
            fill=ACCENT,
        )


        draw.text(
            (
                MARGIN_LEFT,
                HEADER_TOP + 29,
            ),
            title,
            font=title_font,
            fill=TEXT_PRIMARY,
        )


    # ========================================================
    # TIME SCALE
    # ========================================================

    def _draw_time_scale(
        self,
        draw,
        bar_x,
        bar_width,
    ):

        font = self._font(
            TIME_SIZE
        )


        sector_width = (
            bar_width
            / SECTORS
        )


        for index in range(
            SECTORS
        ):

            hour = (
                START_HOUR
                + index
                * HOURS_PER_SECTOR
            ) % 24


            label = f"{hour:02d}"


            center_x = (
                bar_x
                + index
                * sector_width
            )


            bbox = draw.textbbox(
                (0, 0),
                label,
                font=font,
            )


            label_width = (
                bbox[2]
                - bbox[0]
            )


            draw.text(
                (
                    center_x
                    - label_width / 2,
                    84,
                ),
                label,
                font=font,
                fill=TEXT_PRIMARY,
            )


    # ========================================================
    # HOUR GRID
    # ========================================================

    def _draw_hour_grid(
        self,
        draw,
        bar_x,
        bar_y,
        bar_width,
        bar_height,
    ):

        hour_width = (
            bar_width
            / TOTAL_HOURS
        )


        for hour_index in range(
            TOTAL_HOURS + 1
        ):

            x = (
                bar_x
                + hour_index
                * hour_width
            )


            if hour_index % 2 == 0:

                draw.line(
                    (
                        x,
                        bar_y,
                        x,
                        bar_y
                        + bar_height,
                    ),
                    fill=HOUR_LINE,
                    width=2,
                )

            else:

                dash_length = 5

                gap = 5

                current_y = bar_y


                while current_y < (
                    bar_y
                    + bar_height
                ):

                    end_y = min(
                        current_y
                        + dash_length,
                        bar_y
                        + bar_height,
                    )


                    draw.line(
                        (
                            x,
                            current_y,
                            x,
                            end_y,
                        ),
                        fill=HOUR_LINE,
                        width=1,
                    )


                    current_y += (
                        dash_length
                        + gap
                    )


    # ========================================================
    # DRAW INTERVAL
    # ========================================================

    def _draw_interval(
        self,
        draw,
        row_start,
        row_end,
        event_start,
        event_end,
        status,
        bar_x,
        bar_y,
        bar_width,
        bar_height,
    ):

        visible_start = max(
            event_start,
            row_start,
        )


        visible_end = min(
            event_end,
            row_end,
        )


        if visible_end <= visible_start:

            return


        total_seconds = (
            row_end
            - row_start
        ).total_seconds()


        start_seconds = (
            visible_start
            - row_start
        ).total_seconds()


        end_seconds = (
            visible_end
            - row_start
        ).total_seconds()


        x1 = (
            bar_x
            + bar_width
            * start_seconds
            / total_seconds
        )


        x2 = (
            bar_x
            + bar_width
            * end_seconds
            / total_seconds
        )


        fill = (
            MOVABLE
            if status == "movable"
            else BUSY
        )


        draw.rectangle(
            (
                x1,
                bar_y,
                x2,
                bar_y
                + bar_height,
            ),
            fill=fill,
        )


    # ========================================================
    # DRAW ONE DAY
    # ========================================================

    def _draw_day(
        self,
        draw,
        date,
        y,
        language,
        bar_x,
        bar_width,
    ):

        day_font = self._font(
            DAY_SIZE
        )


        # ----------------------------------------------------
        # Background row.
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (
                MARGIN_LEFT - 6,
                y,
                self.width
                - MARGIN_RIGHT
                + 6,
                y
                + BAR_HEIGHT
                + 14,
            ),
            radius=6,
            fill=DAY_BACKGROUND,
        )


        # ----------------------------------------------------
        # Day/date label.
        # ----------------------------------------------------

        (
            day_name,
            date_text,
        ) = self._date_parts(
            date,
            language,
        )


        weekday_text = (
            f"{day_name},"
        )


        weekday_color = (
            WEEKEND
            if date.weekday()
            in (5, 6)
            else TEXT_PRIMARY
        )


        label_y = y + 5


        draw.text(
            (
                MARGIN_LEFT,
                label_y,
            ),
            weekday_text,
            font=day_font,
            fill=weekday_color,
        )


        bbox = draw.textbbox(
            (0, 0),
            weekday_text,
            font=day_font,
        )


        weekday_width = (
            bbox[2]
            - bbox[0]
        )


        draw.text(
            (
                MARGIN_LEFT
                + weekday_width
                + 8,
                label_y,
            ),
            date_text,
            font=day_font,
            fill=TEXT_SECONDARY,
        )


        # ----------------------------------------------------
        # 24-hour row.
        # ----------------------------------------------------

        row_start = (
            self.timezone.localize(
                datetime(
                    date.year,
                    date.month,
                    date.day,
                    START_HOUR,
                    0,
                )
            )
        )


        row_end = (
            row_start
            + timedelta(
                hours=TOTAL_HOURS
            )
        )


        bar_y = y


        # ----------------------------------------------------
        # Free background.
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (
                bar_x,
                bar_y,
                bar_x
                + bar_width,
                bar_y
                + BAR_HEIGHT,
            ),
            radius=5,
            fill=FREE,
        )


        # ----------------------------------------------------
        # Collect events for this day.
        # ----------------------------------------------------

        day_events = []


        for event in self.events:

            try:

                (
                    event_start,
                    event_end,
                    is_all_day,
                ) = self._parse_event_times(
                    event
                )

            except Exception:

                continue


            if event_end <= row_start:

                continue


            if event_start >= row_end:

                continue


            status = (
                self._event_status(
                    event
                )
            )


            day_events.append(
                (
                    event_start,
                    event_end,
                    status,
                    is_all_day,
                )
            )


        # ----------------------------------------------------
        # MOVABLE FIRST.
        # ----------------------------------------------------

        for (
            event_start,
            event_end,
            status,
            is_all_day,
        ) in day_events:

            if status != "movable":

                continue


            if is_all_day:

                event_start = row_start

                event_end = row_end


            self._draw_interval(
                draw,
                row_start,
                row_end,
                event_start,
                event_end,
                status,
                bar_x,
                bar_y,
                bar_width,
                BAR_HEIGHT,
            )


        # ----------------------------------------------------
        # BUSY SECOND.
        #
        # BUSY is deliberately drawn after MOVABLE.
        # If two events overlap, red wins.
        # ----------------------------------------------------

        for (
            event_start,
            event_end,
            status,
            is_all_day,
        ) in day_events:

            if status != "busy":

                continue


            if is_all_day:

                event_start = row_start

                event_end = row_end


            self._draw_interval(
                draw,
                row_start,
                row_end,
                event_start,
                event_end,
                status,
                bar_x,
                bar_y,
                bar_width,
                BAR_HEIGHT,
            )


        # ----------------------------------------------------
        # Grid on top of colors.
        # ----------------------------------------------------

        self._draw_hour_grid(
            draw,
            bar_x,
            bar_y,
            bar_width,
            BAR_HEIGHT,
        )


        return (
            y
            + DAY_HEIGHT
        )


    # ========================================================
    # LEGEND
    # ========================================================

    def _draw_legend(
        self,
        draw,
        language,
        y,
    ):

        font = self._font(
            LEGEND_SIZE
        )


        if language == "uk":

            items = [

                (
                    FREE,
                    "ВІЛЬНО",
                ),

                (
                    BUSY,
                    "ЗАЙНЯТО",
                ),

                (
                    MOVABLE,
                    "МОЖУ ПЕРЕНЕСТИ",
                ),

            ]

        else:

            items = [

                (
                    FREE,
                    "AVAILABLE",
                ),

                (
                    BUSY,
                    "BOOKED",
                ),

                (
                    MOVABLE,
                    "CAN RESCHEDULE",
                ),

            ]


        marker_size = (
            LEGEND_MARKER_SIZE
        )


        for index, (
            marker_color,
            text,
        ) in enumerate(items):

            row_y = (
                y
                + index
                * LEGEND_ROW_HEIGHT
            )


            draw.rounded_rectangle(
                (
                    MARGIN_LEFT,
                    row_y,
                    MARGIN_LEFT
                    + marker_size,
                    row_y
                    + marker_size,
                ),
                radius=6,
                fill=marker_color,
            )


            draw.text(
                (
                    MARGIN_LEFT
                    + marker_size
                    + 16,
                    row_y - 3,
                ),
                text,
                font=font,
                fill=TEXT_PRIMARY,
            )


        # ----------------------------------------------------
        # Timezone.
        # ----------------------------------------------------

        timezone_font = self._font(
            18
        )


        timezone_text = (
            f"Час: {config.TIMEZONE}"
            if language == "uk"
            else f"Time: {config.TIMEZONE}"
        )


        bbox = draw.textbbox(
            (0, 0),
            timezone_text,
            font=timezone_font,
        )


        timezone_width = (
            bbox[2]
            - bbox[0]
        )


        draw.text(
            (
                self.width
                - MARGIN_RIGHT
                - timezone_width,
                y
                + LEGEND_ROW_HEIGHT
                * 3
                - 24,
            ),
            timezone_text,
            font=timezone_font,
            fill=TEXT_MUTED,
        )


    # ========================================================
    # GENERATE ONE LANGUAGE
    # ========================================================

    def _generate_language(
        self,
        language,
        output_path,
    ):

        image = Image.new(
            "RGB",
            (
                self.width,
                self.height,
            ),
            BACKGROUND,
        )


        draw = ImageDraw.Draw(
            image
        )


        # ----------------------------------------------------
        # Header.
        # ----------------------------------------------------

        self._draw_header(
            draw,
            language,
        )


        # ----------------------------------------------------
        # Timeline.
        # ----------------------------------------------------

        bar_x = BAR_X


        bar_width = (
            self.width
            - bar_x
            - MARGIN_RIGHT
        )


        # ----------------------------------------------------
        # Time labels.
        # ----------------------------------------------------

        self._draw_time_scale(
            draw,
            bar_x,
            bar_width,
        )


        # ----------------------------------------------------
        # Days.
        # ----------------------------------------------------

        now = datetime.now(
            self.timezone
        )


        y = DAY_START_Y


        for offset in range(
            DAYS_TO_SHOW
        ):

            date = (
                now
                + timedelta(
                    days=offset
                )
            ).date()


            y = self._draw_day(
                draw,
                date,
                y,
                language,
                bar_x,
                bar_width,
            )


        # ----------------------------------------------------
        # Legend.
        # ----------------------------------------------------

        self._draw_legend(
            draw,
            language,
            y
            + LEGEND_TOP_GAP,
        )


        # ----------------------------------------------------
        # Save PNG.
        # ----------------------------------------------------

        image.save(
            output_path,
            "PNG",
        )


        print(
            f"Availability image created: "
            f"{output_path}"
        )


    # ========================================================
    # GENERATE BOTH LANGUAGES
    # ========================================================

    def generate(self):

        english_output = (
            config.OUTPUT_DIR
            / "availability.png"
        )


        ukrainian_output = (
            config.OUTPUT_DIR
            / "availability_uk.png"
        )


        self._generate_language(
            "en",
            english_output,
        )


        self._generate_language(
            "uk",
            ukrainian_output,
        )


        print(
            "Both availability images "
            "generated successfully."
        )