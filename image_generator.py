"""
Availability image generator.

Generates public availability images from Google Calendar.

Layout:
    06 | 08 | 10 | 12 | ... | 22 | 00 | 02 | 04

Each large 2-hour section is divided vertically in half:
    first half  = first hour
    second half = second hour

Therefore:
    06 section = 06:00-08:00
    08 section = 08:00-10:00
    ...
    04 section = 04:00-06:00

The actual event position is calculated continuously,
including minutes.

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

# Light, muted green.
FREE = (190, 200, 184)

# Darker red for occupied time.
BUSY = (195, 55, 55)

# Dark vertical lines separating individual hours.
HOUR_LINE = (78, 85, 76)

# Dark background behind each day.
DAY_BACKGROUND = (25, 25, 25)

# Same dark-red color for Saturday and Sunday.
WEEKEND = (145, 45, 45)

# Green accent above the main title.
ACCENT = (115, 155, 105)


# ============================================================
# IMAGE / LAYOUT
# ============================================================

# Requested final width.
IMAGE_WIDTH = 1050

# Number of days displayed.
DAYS_TO_SHOW = 14

# The availability day starts at 06:00.
START_HOUR = 6

# 24 hours total.
TOTAL_HOURS = 24

# 12 large sectors, each representing 2 hours.
SECTORS = 12

# Hours represented by one large sector.
HOURS_PER_SECTOR = 2

# ------------------------------------------------------------
# Margins
# ------------------------------------------------------------

MARGIN_LEFT = 28
MARGIN_RIGHT = 28

# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

HEADER_TOP = 18

SUBTITLE_SIZE = 17
TITLE_SIZE = 34

# ------------------------------------------------------------
# Timeline
# ------------------------------------------------------------

TIME_SIZE = 16

# Space occupied by day/date label.
DAY_LABEL_WIDTH = 175

# Timeline starts here.
BAR_X = MARGIN_LEFT + DAY_LABEL_WIDTH

# ------------------------------------------------------------
# Day rows
# ------------------------------------------------------------

DAY_SIZE = 20

DAY_START_Y = 112

DAY_HEIGHT = 58

BAR_HEIGHT = 27

# ------------------------------------------------------------
# Bottom legend
# ------------------------------------------------------------

LEGEND_SIZE = 15


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
            + 60
        )

    # ========================================================
    # FONT
    # ========================================================

    def _font_path(self):
        """
        Find a font that supports Ukrainian Cyrillic
        and works on GitHub Actions.
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
                HEADER_TOP + 25,
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
        Draw only even hours:

        06 08 10 12 14 16 18 20 22 00 02 04

        Each label represents the beginning of
        a 2-hour sector.
        """

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
                + index * sector_width
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
                    83,
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
        """
        Draw:

        - solid lines at every 2-hour boundary
        - slightly darker/dashed-looking lines at every
          1-hour boundary

        Therefore every large sector visually contains
        two individual hours.
        """

        hour_width = (
            bar_width
            / TOTAL_HOURS
        )

        for hour_index in range(
            TOTAL_HOURS + 1
        ):

            x = (
                bar_x
                + hour_index * hour_width
            )

            # Two-hour boundary.
            if hour_index % 2 == 0:

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

            # One-hour internal divider.
            else:

                # Dashed vertical line.
                dash_length = 4
                gap = 4

                current_y = bar_y

                while current_y < (
                    bar_y + bar_height
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
        Draw an event using exact start/end time.

        Minutes are preserved.
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
        Draw one complete 24-hour availability bar.
        """

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
                y + BAR_HEIGHT + 12,
            ),
            radius=5,
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
            if date.weekday() in (5, 6)
            else TEXT_PRIMARY
        )

        label_y = y + 6

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
                + 7,
                label_y,
            ),
            date_text,
            font=day_font,
            fill=TEXT_SECONDARY,
        )

        # ----------------------------------------------------
        # 24-hour row.
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
                hours=TOTAL_HOURS
            )
        )

        # ----------------------------------------------------
        # Free background.
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (
                bar_x,
                y,
                bar_x + bar_width,
                y + BAR_HEIGHT,
            ),
            radius=4,
            fill=FREE,
        )

        # ----------------------------------------------------
        # Busy intervals.
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
                    y,
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
                    y,
                    bar_width,
                    BAR_HEIGHT,
                )

        # ----------------------------------------------------
        # Hour grid over the colors.
        # ----------------------------------------------------

        self._draw_hour_grid(
            draw,
            bar_x,
            y,
            bar_width,
            BAR_HEIGHT,
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
            LEGEND_SIZE
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

        marker_size = 21

        # ----------------------------------------------------
        # Free marker.
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
                + 8,
                y - 1,
            ),
            free_text,
            font=font,
            fill=TEXT_SECONDARY,
        )

        # ----------------------------------------------------
        # Busy marker.
        # ----------------------------------------------------

        busy_x = (
            MARGIN_LEFT
            + 115
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
                + 8,
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

        # Hour labels.
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
            y + 5,
        )

        # Save PNG.
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
