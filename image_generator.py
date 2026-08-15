"""
Availability image generator.

Generates public availability images from Google Calendar.

Each calendar day is displayed as two 12-hour timelines:

    06 07 08 09 10 11 12 13 14 15 16 17

    18 19 20 21 22 23 00 01 02 03 04 05

This layout is designed to work inside websites that only
allow a normal <img> element and remove custom HTML/CSS.

No event titles or private calendar information are displayed.
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

BACKGROUND = (17, 17, 17)

TEXT_PRIMARY = (235, 235, 235)
TEXT_SECONDARY = (175, 175, 175)
TEXT_MUTED = (105, 105, 105)

# Light, desaturated green for available time.
FREE = (190, 200, 184)

# Clearly red, but not excessively saturated.
BUSY = (195, 55, 55)

# Dark separators between individual hours.
HOUR_LINE = (78, 85, 76)

# Background behind each day.
DAY_BACKGROUND = (25, 25, 25)

# Same dark red for Saturday and Sunday.
WEEKEND = (145, 45, 45)

# Small accent above the main title.
ACCENT = (115, 155, 105)


# ============================================================
# IMAGE / LAYOUT
# ============================================================

# The image is intentionally no longer 1400 px wide.
# It is designed to fit normal website content.
IMAGE_WIDTH = 1000

# Number of days.
DAYS_TO_SHOW = 14

# The working day starts at 06:00.
START_HOUR = 6

# Two blocks of 12 hours each.
HOURS_PER_ROW = 12

# Margins.
MARGIN_LEFT = 35
MARGIN_RIGHT = 35

# Header.
HEADER_TOP = 24
SUBTITLE_SIZE = 18
TITLE_SIZE = 36

# Time labels.
TIME_SIZE = 16

# Day/date labels.
DAY_SIZE = 21

# Position of the first day.
DAY_START_Y = 115

# Space occupied by one complete day.
DAY_HEIGHT = 92

# Availability bars.
BAR_HEIGHT = 25

# Distance between the two 12-hour bars.
BAR_GAP = 7

# Width reserved for day/date labels.
DAY_LABEL_WIDTH = 190

# Timeline begins here.
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
            + DAYS_TO_SHOW * DAY_HEIGHT
            + 70
        )

    # ========================================================
    # FONT
    # ========================================================

    def _font_path(self):
        """
        Find a font that works both locally and
        on GitHub Actions.

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
    # GOOGLE CALENDAR EVENT PARSING
    # ========================================================

    def _parse_event_times(self, event):
        """
        Convert Google Calendar event times into
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
    # DATE TEXT
    # ========================================================

    def _date_parts(
        self,
        date,
        language,
    ):

        if language == "uk":

            day_name = UKRAINIAN_DAYS[
                date.weekday()
            ]

            date_text = (
                f"{date.day} "
                f"{UKRAINIAN_MONTHS[date.month]}"
            )

        else:

            day_name = ENGLISH_DAYS[
                date.weekday()
            ]

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
                HEADER_TOP + 26,
            ),
            title,
            font=title_font,
            fill=TEXT_PRIMARY,
        )

    # ========================================================
    # TIME LABELS
    # ========================================================

    def _draw_time_labels(
        self,
        draw,
        bar_x,
        bar_width,
        y,
        start_hour,
    ):
        """
        Draw 12 hourly labels.

        Example:

        06 07 08 09 10 11 12 13 14 15 16 17
        """

        font = self._font(
            TIME_SIZE
        )

        hour_width = (
            bar_width
            / HOURS_PER_ROW
        )

        for index in range(
            HOURS_PER_ROW
        ):

            hour = (
                start_hour + index
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
                    y,
                ),
                label,
                font=font,
                fill=TEXT_SECONDARY,
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
        """
        Draw vertical separators for each hour.
        """

        hour_width = (
            bar_width
            / HOURS_PER_ROW
        )

        for index in range(
            HOURS_PER_ROW + 1
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
    # DRAW BUSY INTERVAL
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
        """
        Draw an event clipped to one 12-hour block.
        """

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
    # DRAW 12-HOUR BAR
    # ========================================================

    def _draw_time_block(
        self,
        draw,
        row_start,
        row_end,
        bar_x,
        bar_y,
        bar_width,
    ):
        """
        Draw one 12-hour availability bar.
        """

        # ----------------------------------------------------
        # Free background.
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (
                bar_x,
                bar_y,
                bar_x + bar_width,
                bar_y + BAR_HEIGHT,
            ),
            radius=4,
            fill=FREE,
        )

        # ----------------------------------------------------
        # Busy events.
        # ----------------------------------------------------

        for event in self.events:

            (
                event_start,
                event_end,
                all_day,
            ) = self._parse_event_times(
                event
            )

            if event_end <= row_start:
                continue

            if event_start >= row_end:
                continue

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
        # Hour separators.
        # ----------------------------------------------------

        self._draw_hour_grid(
            draw,
            bar_x,
            bar_y,
            bar_width,
            BAR_HEIGHT,
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
        """
        Draw one calendar day using two 12-hour blocks.

        Block 1:
            06:00 -> 18:00

        Block 2:
            18:00 -> 06:00 next day
        """

        day_font = self._font(
            DAY_SIZE
        )

        # ----------------------------------------------------
        # Day background.
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (
                MARGIN_LEFT - 8,
                y,
                self.width
                - MARGIN_RIGHT
                + 8,
                y + DAY_HEIGHT - 8,
            ),
            radius=5,
            fill=DAY_BACKGROUND,
        )

        # ----------------------------------------------------
        # Day label.
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
            if date.weekday() in (5, 6)
            else TEXT_PRIMARY
        )

        label_y = y + 27

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
        # First 12-hour period.
        # 06:00 -> 18:00
        # ----------------------------------------------------

        first_start = self.timezone.localize(
            datetime(
                date.year,
                date.month,
                date.day,
                6,
                0,
            )
        )

        first_end = (
            first_start
            + timedelta(
                hours=12
            )
        )

        # ----------------------------------------------------
        # Second 12-hour period.
        # 18:00 -> 06:00
        # ----------------------------------------------------

        second_start = first_end

        second_end = (
            second_start
            + timedelta(
                hours=12
            )
        )

        # ----------------------------------------------------
        # Time labels.
        # ----------------------------------------------------

        first_label_y = (
            y + 4
        )

        second_label_y = (
            y
            + 4
            + BAR_HEIGHT
            + BAR_GAP
            + 19
        )

        self._draw_time_labels(
            draw,
            bar_x,
            bar_width,
            first_label_y,
            6,
        )

        self._draw_time_labels(
            draw,
            bar_x,
            bar_width,
            second_label_y,
            18,
        )

        # ----------------------------------------------------
        # Bars.
        # ----------------------------------------------------

        first_bar_y = (
            y
            + 21
        )

        second_bar_y = (
            first_bar_y
            + BAR_HEIGHT
            + BAR_GAP
        )

        self._draw_time_block(
            draw,
            first_start,
            first_end,
            bar_x,
            first_bar_y,
            bar_width,
        )

        self._draw_time_block(
            draw,
            second_start,
            second_end,
            bar_x,
            second_bar_y,
            bar_width,
        )

        return y + DAY_HEIGHT

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
            16
        )

        if language == "uk":

            free_text = "вільно"
            busy_text = "зайнято"

            timezone_text = (
                "Час: Europe/Kyiv"
            )

        else:

            free_text = "available"
            busy_text = "booked"

            timezone_text = (
                "Time: Europe/Kyiv"
            )

        marker_size = 22

        # ----------------------------------------------------
        # Free.
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (
                MARGIN_LEFT,
                y,
                MARGIN_LEFT
                + marker_size,
                y + marker_size,
            ),
            radius=4,
            fill=FREE,
        )

        draw.text(
            (
                MARGIN_LEFT
                + marker_size
                + 9,
                y - 1,
            ),
            free_text,
            font=font,
            fill=TEXT_SECONDARY,
        )

        # ----------------------------------------------------
        # Busy.
        # ----------------------------------------------------

        busy_x = (
            MARGIN_LEFT
            + 130
        )

        draw.rounded_rectangle(
            (
                busy_x,
                y,
                busy_x
                + marker_size,
                y + marker_size,
            ),
            radius=4,
            fill=BUSY,
        )

        draw.text(
            (
                busy_x
                + marker_size
                + 9,
                y - 1,
            ),
            busy_text,
            font=font,
            fill=TEXT_SECONDARY,
        )

        # ----------------------------------------------------
        # Timezone.
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

        # ----------------------------------------------------
        # Header.
        # ----------------------------------------------------

        self._draw_header(
            draw,
            language,
        )

        # ----------------------------------------------------
        # Timeline dimensions.
        # ----------------------------------------------------

        bar_x = BAR_X

        bar_width = (
            self.width
            - bar_x
            - MARGIN_RIGHT
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
            y + 5,
        )

        # ----------------------------------------------------
        # Save.
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
        """
        Generate English and Ukrainian images.
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
