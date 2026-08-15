"""
Availability image generator.

Generates two public availability images from Google Calendar:

    output/availability.png
    output/availability_uk.png

Each row represents a 24-hour period:

    06:00 current day
        ->
    06:00 following day

The generator never displays event titles or private
calendar information.
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
    1: "січня",
    2: "лютого",
    3: "березня",
    4: "квітня",
    5: "травня",
    6: "червня",
    7: "липня",
    8: "серпня",
    9: "вересня",
    10: "жовтня",
    11: "листопада",
    12: "грудня",
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
# COLORS
# ============================================================

# Dark overall background.
BACKGROUND = (17, 17, 17)

# Main text.
TEXT_PRIMARY = (235, 235, 235)

# Secondary text.
TEXT_SECONDARY = (175, 175, 175)

# Muted secondary text.
TEXT_MUTED = (105, 105, 105)

# Free time.
# Light, calm, slightly desaturated green.
FREE = (190, 200, 184)

# Busy time.
# Clearly red, but not excessively saturated.
BUSY = (195, 55, 55)

# Hour separators.
# Significantly darker than FREE.
HOUR_LINE = (80, 87, 78)

# Background of each row.
DAY_BACKGROUND = (25, 25, 25)

# Weekend day labels.
# Saturday and Sunday use exactly the same color.
WEEKEND = (145, 45, 45)

# Small green accent above title.
ACCENT = (115, 155, 105)


# ============================================================
# IMAGE / LAYOUT
# ============================================================

# Wide image because 24 hours must remain readable.
IMAGE_WIDTH = 1400

# Number of calendar days.
DAYS_TO_SHOW = 14

# Timeline starts at 06:00.
START_HOUR = 6

# Full 24-hour period.
HOURS = 24

# Margins.
MARGIN_LEFT = 55
MARGIN_RIGHT = 55

# Header.
HEADER_TOP = 32

# Smaller than the previous oversized version.
TITLE_SIZE = 42
SUBTITLE_SIZE = 20

# Hour labels.
TIME_SIZE = 20
TIME_Y = 120

# Day/date labels.
DAY_SIZE = 23

# Rows.
DAY_START_Y = 160
ROW_HEIGHT = 70

# Availability bar.
BAR_HEIGHT = 40

# Width reserved for weekday/date.
DAY_LABEL_WIDTH = 245

# Timeline X coordinate.
BAR_X = MARGIN_LEFT + DAY_LABEL_WIDTH


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
            + ROW_HEIGHT * DAYS_TO_SHOW
            + 90
        )

    # ========================================================
    # FONT
    # ========================================================

    def _font_path(self):
        """
        Finds a font that works on GitHub Actions Linux.

        DejaVu Sans supports Ukrainian Cyrillic.
        """

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

            if Path(font_path).exists():
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
    # GOOGLE CALENDAR EVENTS
    # ========================================================

    def _parse_event_times(self, event):
        """
        Converts Google Calendar event times into
        timezone-aware Europe/Kyiv datetimes.
        """

        start_data = event.get(
            "start",
            {},
        )

        end_data = event.get(
            "end",
            {},
        )

        # ----------------------------------------------------
        # All-day event
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
        # Timed event
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
    # DATE FORMATTING
    # ========================================================

    def _format_date(
        self,
        date,
        language,
    ):

        if language == "uk":

            return (
                UKRAINIAN_DAYS[
                    date.weekday()
                ]
                + ", "
                + str(date.day)
                + " "
                + UKRAINIAN_MONTHS[
                    date.month
                ]
            )

        return (
            ENGLISH_DAYS[
                date.weekday()
            ]
            + ", "
            + f"{date.day:02d}"
            + " "
            + ENGLISH_MONTHS[
                date.month
            ]
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
                HEADER_TOP + 30,
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
        """
        Draws:

        06 07 08 ... 23 00 01 ... 05
        """

        font = self._font(
            TIME_SIZE
        )

        hour_width = (
            bar_width / HOURS
        )

        for index in range(
            HOURS
        ):

            hour = (
                START_HOUR
                + index
            ) % 24

            label = f"{hour:02d}"

            center_x = (
                bar_x
                + index * hour_width
                + hour_width / 2
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
                    TIME_Y,
                ),
                label,
                font=font,
                fill=TEXT_SECONDARY,
            )

    # ========================================================
    # HOUR SEPARATORS
    # ========================================================

    def _draw_hour_grid(
        self,
        draw,
        bar_x,
        bar_y,
        bar_width,
        bar_height,
    ):
        """
        Separates every hour with a dark vertical line.
        """

        hour_width = (
            bar_width / HOURS
        )

        for index in range(
            HOURS + 1
        ):

            x = (
                bar_x
                + index * hour_width
            )

            draw.line(
                (
                    x,
                    bar_y,
                    x,
                    bar_y + bar_height,
                ),
                fill=HOUR_LINE,
                width=2,
            )

    # ========================================================
    # BUSY INTERVAL
    # ========================================================

    def _draw_busy_interval(
        self,
        draw,
        row_start,
        row_end,
        event_start,
        event_end,
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
            row_end - row_start
        ).total_seconds()

        start_seconds = (
            visible_start - row_start
        ).total_seconds()

        end_seconds = (
            visible_end - row_start
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

        draw.rectangle(
            (
                x1,
                bar_y,
                x2,
                bar_y + bar_height,
            ),
            fill=BUSY,
        )

    # ========================================================
    # DAY ROW
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
        """
        Draws one 24-hour row:

        06:00 current day
        ->
        06:00 following day
        """

        day_font = self._font(
            DAY_SIZE
        )

        # ----------------------------------------------------
        # 24-hour boundaries
        # ----------------------------------------------------

        row_start = self.timezone.localize(
            datetime(
                date.year,
                date.month,
                date.day,
                START_HOUR,
                0,
            )
        )

        row_end = (
            row_start
            + timedelta(
                days=1
            )
        )

        # ----------------------------------------------------
        # Background first
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (
                MARGIN_LEFT - 10,
                y,
                self.width
                - MARGIN_RIGHT
                + 10,
                y + BAR_HEIGHT + 16,
            ),
            radius=6,
            fill=DAY_BACKGROUND,
        )

        # ----------------------------------------------------
        # Day / date
        # ----------------------------------------------------

        if language == "uk":

            day_name = (
                UKRAINIAN_DAYS[
                    date.weekday()
                ]
            )

            date_part = (
                f"{date.day} "
                f"{UKRAINIAN_MONTHS[date.month]}"
            )

        else:

            day_name = (
                ENGLISH_DAYS[
                    date.weekday()
                ]
            )

            date_part = (
                f"{date.day:02d} "
                f"{ENGLISH_MONTHS[date.month]}"
            )

        weekday_text = (
            f"{day_name},"
        )

        # Saturday and Sunday:
        # same dark-red color.
        weekday_color = (
            WEEKEND
            if date.weekday() in (5, 6)
            else TEXT_PRIMARY
        )

        draw.text(
            (
                MARGIN_LEFT,
                y + 8,
            ),
            weekday_text,
            font=day_font,
            fill=weekday_color,
        )

        weekday_bbox = draw.textbbox(
            (0, 0),
            weekday_text,
            font=day_font,
        )

        weekday_width = (
            weekday_bbox[2]
            - weekday_bbox[0]
        )

        draw.text(
            (
                MARGIN_LEFT
                + weekday_width
                + 10,
                y + 8,
            ),
            date_part,
            font=day_font,
            fill=TEXT_SECONDARY,
        )

        # ----------------------------------------------------
        # Free-time base
        # ----------------------------------------------------

        bar_y = y + 6

        draw.rounded_rectangle(
            (
                bar_x,
                bar_y,
                bar_x
                + bar_width,
                bar_y
                + BAR_HEIGHT,
            ),
            radius=6,
            fill=FREE,
        )

        # ----------------------------------------------------
        # Busy events
        # ----------------------------------------------------

        for event in self.events:

            (
                event_start,
                event_end,
                all_day,
            ) = self._parse_event_times(
                event
            )

            # No overlap.
            if event_end <= row_start:
                continue

            if event_start >= row_end:
                continue

            # All-day event.
            if all_day:

                self._draw_busy_interval(
                    draw,
                    row_start,
                    row_end,
                    row_start,
                    row_end,
                    bar_x,
                    bar_y,
                    bar_width,
                    BAR_HEIGHT,
                )

            # Timed event.
            else:

                self._draw_busy_interval(
                    draw,
                    row_start,
                    row_end,
                    event_start,
                    event_end,
                    bar_x,
                    bar_y,
                    bar_width,
                    BAR_HEIGHT,
                )

        # ----------------------------------------------------
        # Hour separators last
        # ----------------------------------------------------

        self._draw_hour_grid(
            draw,
            bar_x,
            bar_y,
            bar_width,
            BAR_HEIGHT,
        )

        return y + ROW_HEIGHT

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
            18
        )

        if language == "uk":

            free_text = "вільно"
            busy_text = "зайнято"

            timezone_text = (
                "Час у вашому часовому поясі: "
                "Europe/Kyiv"
            )

        else:

            free_text = "available"
            busy_text = "booked"

            timezone_text = (
                "Time zone: Europe/Kyiv"
            )

        marker_size = 26

        # ----------------------------------------------------
        # Free
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (
                MARGIN_LEFT,
                y,
                MARGIN_LEFT
                + marker_size,
                y + marker_size,
            ),
            radius=5,
            fill=FREE,
        )

        draw.text(
            (
                MARGIN_LEFT
                + marker_size
                + 10,
                y - 1,
            ),
            free_text,
            font=font,
            fill=TEXT_SECONDARY,
        )

        # ----------------------------------------------------
        # Busy
        # ----------------------------------------------------

        busy_x = (
            MARGIN_LEFT
            + 155
        )

        draw.rounded_rectangle(
            (
                busy_x,
                y,
                busy_x
                + marker_size,
                y + marker_size,
            ),
            radius=5,
            fill=BUSY,
        )

        draw.text(
            (
                busy_x
                + marker_size
                + 10,
                y - 1,
            ),
            busy_text,
            font=font,
            fill=TEXT_SECONDARY,
        )

        # ----------------------------------------------------
        # Timezone
        # ----------------------------------------------------

        bbox = draw.textbbox(
            (0, 0),
            timezone_text,
            font=font,
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
                y - 1,
            ),
            timezone_text,
            font=font,
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

        # Header.
        self._draw_header(
            draw,
            language,
        )

        # Timeline.
        bar_x = BAR_X

        bar_width = (
            self.width
            - bar_x
            - MARGIN_RIGHT
        )

        self._draw_time_scale(
            draw,
            bar_x,
            bar_width,
        )

        # Days.
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

        # Legend.
        self._draw_legend(
            draw,
            language,
            y + 10,
        )

        # Save.
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
        """
        Generates both English and Ukrainian images.
        """

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
