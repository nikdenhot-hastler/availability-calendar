"""
Availability image generator.

Generates two public availability images from Google Calendar:

    output/availability.png
    output/availability_uk.png

Each row represents a 24-hour period:
06:00 of the selected day -> 06:00 of the following day.

Private event titles and private calendar information are never displayed.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytz
from PIL import Image, ImageDraw, ImageFont

import config


# ============================================================
# LANGUAGE
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
TEXT_SECONDARY = (185, 185, 185)
TEXT_MUTED = (125, 125, 125)

# Free time: light, but not aggressively bright.
FREE = (205, 215, 198)

# Busy time: muted dark red/orange-red.
BUSY = (205, 55, 55)

# Hour separators: clearly darker than FREE.
HOUR_LINE = (105, 110, 102)

# Background behind each day.
DAY_BACKGROUND = (25, 25, 25)

# Weekend label color: same dark red for Saturday and Sunday.
WEEKEND = (145, 45, 45)

# Small green heading accent.
ACCENT = (115, 155, 105)


# ============================================================
# LAYOUT
# ============================================================

# These values are intentionally moderate so that the image
# does not look oversized when displayed on the website.

MARGIN_LEFT = 35
MARGIN_RIGHT = 35

HEADER_TOP = 28

TITLE_SIZE = 34
SUBTITLE_SIZE = 18

TIME_SIZE = 14
DAY_SIZE = 18

TIME_Y = 92

DAY_START_Y = 125
ROW_HEIGHT = 63

BAR_HEIGHT = 38

DAY_LABEL_WIDTH = 180

BAR_X = MARGIN_LEFT + DAY_LABEL_WIDTH

BAR_RIGHT_MARGIN = MARGIN_RIGHT

BOTTOM_MARGIN = 55

# Number of hours shown.
HOURS = 24

START_HOUR = 6


class AvailabilityImageGenerator:

    def __init__(self, events):
        self.events = events
        self.timezone = pytz.timezone(config.TIMEZONE)

        config.OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.font_path = self._font_path()

        # Use configured image size if available.
        self.width = getattr(
            config,
            "WIDTH",
            930,
        )

        self.height = (
            DAY_START_Y
            + ROW_HEIGHT * getattr(
                config,
                "DAYS_TO_SHOW",
                14,
            )
            + BOTTOM_MARGIN
        )

    # ========================================================
    # FONT
    # ========================================================

    def _font_path(self):
        """
        Find a font that works both locally and on GitHub Actions.
        """

        local_font = getattr(
            config,
            "FONT_PATH",
            None,
        )

        if local_font:
            local_path = Path(local_font)

            if local_path.exists():
                return str(local_path)

        # GitHub Actions / Ubuntu.
        linux_fonts = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
        ]

        for font in linux_fonts:
            if Path(font).exists():
                return font

        raise FileNotFoundError(
            "No usable font found."
        )

    def _font(self, size):
        return ImageFont.truetype(
            self.font_path,
            size,
        )

    # ========================================================
    # EVENT PARSING
    # ========================================================

    def _parse_event_times(self, event):
        """
        Returns:

            start
            end
            all_day

        All datetimes are timezone-aware and converted
        to Europe/Kyiv.
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
        """
        Format date for the selected language.
        """

        if language == "uk":

            day_name = UKRAINIAN_DAYS[
                date.weekday()
            ]

            month_name = UKRAINIAN_MONTHS[
                date.month
            ]

            return (
                f"{day_name}, "
                f"{date.day} "
                f"{month_name}"
            )

        day_name = ENGLISH_DAYS[
            date.weekday()
        ]

        month_name = ENGLISH_MONTHS[
            date.month
        ]

        return (
            f"{day_name}, "
            f"{date.day:02d} "
            f"{month_name}"
        )

    # ========================================================
    # DRAW HEADER
    # ========================================================

    def _draw_header(
        self,
        draw,
        language,
    ):
        """
        Draw title and small subtitle.
        """

        title_font = self._font(
            TITLE_SIZE
        )

        subtitle_font = self._font(
            SUBTITLE_SIZE
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

        # Small subtitle.
        draw.text(
            (
                MARGIN_LEFT,
                HEADER_TOP,
            ),
            subtitle,
            font=subtitle_font,
            fill=ACCENT,
        )

        # Main title.
        draw.text(
            (
                MARGIN_LEFT,
                HEADER_TOP + 27,
            ),
            title,
            font=title_font,
            fill=TEXT_PRIMARY,
        )

    # ========================================================
    # DRAW TIME SCALE
    # ========================================================

    def _draw_time_scale(
        self,
        draw,
        bar_x,
        bar_width,
    ):
        """
        Draws 06 -> 05 hourly scale.

        Each hour is visually separated by a dark vertical line.
        """

        font = self._font(
            TIME_SIZE
        )

        hour_width = (
            bar_width / HOURS
        )

        for index in range(HOURS):

            hour = (
                START_HOUR + index
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
                bbox[2] - bbox[0]
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
    # DRAW HOUR GRID
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
        Draw dark vertical separators for every hour.
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
                width=1,
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
        Draw one booked event on the 24-hour timeline.
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
    # DRAW DAY
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
        Draws one complete 24-hour day.

        Timeline:
            06:00 current day
            ->
            06:00 following day
        """

        day_font = self._font(
            DAY_SIZE
        )

        # ----------------------------------------------------
        # Timeline boundaries
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

        row_end = row_start + timedelta(
            days=1
        )

        # ----------------------------------------------------
        # Date label
        # ----------------------------------------------------

        date_text = self._format_date(
            date,
            language,
        )

        day_name_color = (
            WEEKEND
            if date.weekday() in (5, 6)
            else TEXT_PRIMARY
        )

        # Split day name from date so only
        # Saturday/Sunday gets the weekend color.

        if language == "uk":

            day_name = UKRAINIAN_DAYS[
                date.weekday()
            ]

            month_name = UKRAINIAN_MONTHS[
                date.month
            ]

            date_part = (
                f"{date.day} "
                f"{month_name}"
            )

        else:

            day_name = ENGLISH_DAYS[
                date.weekday()
            ]

            month_name = ENGLISH_MONTHS[
                date.month
            ]

            date_part = (
                f"{date.day:02d} "
                f"{month_name}"
            )

        draw.text(
            (
                MARGIN_LEFT,
                y + 6,
            ),
            f"{day_name},",
            font=day_font,
            fill=day_name_color,
        )

        day_bbox = draw.textbbox(
            (0, 0),
            f"{day_name},",
            font=day_font,
        )

        day_width = (
            day_bbox[2]
            - day_bbox[0]
        )

        draw.text(
            (
                MARGIN_LEFT
                + day_width
                + 7,
                y + 6,
            ),
            date_part,
            font=day_font,
            fill=TEXT_SECONDARY,
        )

        # ----------------------------------------------------
        # Row background
        # ----------------------------------------------------

        draw.rounded_rectangle(
            (
                MARGIN_LEFT - 8,
                y,
                self.width - MARGIN_RIGHT + 8,
                y + BAR_HEIGHT + 12,
            ),
            radius=5,
            fill=DAY_BACKGROUND,
        )

        # ----------------------------------------------------
        # Free time base
        # ----------------------------------------------------

        bar_y = y + 5

        draw.rounded_rectangle(
            (
                bar_x,
                bar_y,
                bar_x + bar_width,
                bar_y + BAR_HEIGHT,
            ),
            radius=5,
            fill=FREE,
        )

        # ----------------------------------------------------
        # Hour divisions
        # ----------------------------------------------------

        self._draw_hour_grid(
            draw,
            bar_x,
            bar_y,
            bar_width,
            BAR_HEIGHT,
        )

        # ----------------------------------------------------
        # Booked events
        # ----------------------------------------------------

        for event in self.events:

            (
                event_start,
                event_end,
                all_day,
            ) = self._parse_event_times(
                event
            )

            # Event doesn't overlap this 24-hour row.
            if event_end <= row_start:
                continue

            if event_start >= row_end:
                continue

            if all_day:

                visible_start = row_start
                visible_end = row_end

                self._draw_busy_interval(
                    draw,
                    row_start,
                    row_end,
                    visible_start,
                    visible_end,
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

        # Draw hour divisions again over the busy areas.
        # This keeps every hour visually separated.
        self._draw_hour_grid(
            draw,
            bar_x,
            bar_y,
            bar_width,
            BAR_HEIGHT,
        )

        return y + ROW_HEIGHT

    # ========================================================
    # DRAW LEGEND
    # ========================================================

    def _draw_legend(
        self,
        draw,
        language,
        y,
    ):
        """
        Draws bottom legend.
        """

        legend_font = self._font(
            15
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

        # Free marker.
        draw.rounded_rectangle(
            (
                MARGIN_LEFT,
                y,
                MARGIN_LEFT + 24,
                y + 24,
            ),
            radius=4,
            fill=FREE,
        )

        draw.text(
            (
                MARGIN_LEFT + 35,
                y + 1,
            ),
            free_text,
            font=legend_font,
            fill=TEXT_SECONDARY,
        )

        # Busy marker.
        busy_x = MARGIN_LEFT + 145

        draw.rounded_rectangle(
            (
                busy_x,
                y,
                busy_x + 24,
                y + 24,
            ),
            radius=4,
            fill=BUSY,
        )

        draw.text(
            (
                busy_x + 35,
                y + 1,
            ),
            busy_text,
            font=legend_font,
            fill=TEXT_SECONDARY,
        )

        # Timezone.
        bbox = draw.textbbox(
            (0, 0),
            timezone_text,
            font=legend_font,
        )

        timezone_width = (
            bbox[2] - bbox[0]
        )

        draw.text(
            (
                self.width
                - MARGIN_RIGHT
                - timezone_width,
                y + 1,
            ),
            timezone_text,
            font=legend_font,
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
        """
        Generate one language version.
        """

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

        self._draw_header(
            draw,
            language,
        )

        bar_x = BAR_X

        bar_width = (
            self.width
            - bar_x
            - BAR_RIGHT_MARGIN
        )

        self._draw_time_scale(
            draw,
            bar_x,
            bar_width,
        )

        now = datetime.now(
            self.timezone
        )

        days_to_show = getattr(
            config,
            "DAYS_TO_SHOW",
            14,
        )

        y = DAY_START_Y

        for offset in range(
            days_to_show
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

        self._draw_legend(
            draw,
            language,
            y + 8,
        )

        image.save(
            output_path,
            "PNG",
        )

        print(
            f"Availability image created: "
            f"{output_path}"
        )

    # ========================================================
    # PUBLIC GENERATE METHOD
    # ========================================================

    def generate(self):
        """
        Generate both English and Ukrainian images.
        """

        english_output = (
            config.OUTPUT_IMAGE
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
