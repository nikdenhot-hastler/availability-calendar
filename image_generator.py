"""
Availability image generator.

Creates public availability images from Google Calendar events.

Generated files:
    output/availability.png
    output/availability_uk.png

Event titles and private calendar information are never displayed.
"""

from datetime import datetime, timedelta
from pathlib import Path

import pytz
from PIL import Image, ImageDraw, ImageFont

import config


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


class AvailabilityImageGenerator:

    def __init__(self, events):
        self.events = events
        self.timezone = pytz.timezone(config.TIMEZONE)

        config.OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.font_path = self._font_path()

    def _font_path(self):
        """
        Returns a valid font path on Windows
        and GitHub Actions Linux.
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

        linux_font = Path(
            "/usr/share/fonts/truetype/dejavu/"
            "DejaVuSans.ttf"
        )

        if linux_font.exists():
            return str(linux_font)

        raise FileNotFoundError(
            "No usable font found."
        )

    def _parse_event_times(self, event):
        """
        Returns event start/end as timezone-aware datetimes.
        """

        start_data = event.get("start", {})
        end_data = event.get("end", {})

        # All-day event
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

            return start, end, True

        # Timed event
        start = datetime.fromisoformat(
            start_data["dateTime"]
        )

        end = datetime.fromisoformat(
            end_data["dateTime"]
        )

        if start.tzinfo is None:
            start = self.timezone.localize(start)

        if end.tzinfo is None:
            end = self.timezone.localize(end)

        return (
            start.astimezone(self.timezone),
            end.astimezone(self.timezone),
            False,
        )

    def _create_fonts(self):
        """
        Creates all fonts used by the image.
        """

        return {
            "header": ImageFont.truetype(
                self.font_path,
                config.HEADER_SIZE,
            ),
            "day": ImageFont.truetype(
                self.font_path,
                config.DAY_SIZE,
            ),
            "small": ImageFont.truetype(
                self.font_path,
                config.SMALL_SIZE,
            ),
        }

    def _draw_header(self, draw, font, language):
        """
        Draws the public header.
        """

        if language == "uk":
            title = "ДОСТУПНІСТЬ"
        else:
            title = "AVAILABILITY"

        draw.text(
            (40, 30),
            title,
            font=font,
            fill=config.TEXT,
        )

    def _draw_time_scale(self, draw, font):
        """
        Draws hourly time scale from 08 to 23.
        """

        bar_x = 280
        bar_width = 650

        start_hour = 8
        end_hour = 23

        total_hours = end_hour - start_hour
        hour_width = bar_width / total_hours

        y = 82

        for hour in range(
            start_hour,
            end_hour + 1,
        ):

            x = (
                bar_x
                + (hour - start_hour)
                * hour_width
            )

            label = f"{hour:02d}"

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
                    x - label_width / 2,
                    y,
                ),
                label,
                font=font,
                fill=config.TEXT,
            )

    def _format_date(self, date, language):
        """
        Returns date label in English or Ukrainian.
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

        return date.strftime(
            "%a, %d %b"
        )

    def _draw_day(
        self,
        draw,
        date,
        y,
        font,
    ):
        """
        Draws one day's availability bar.
        """

        date_text = self._format_date(
            date,
            self.language,
        )

        draw.text(
            (40, y),
            date_text,
            font=font,
            fill=config.TEXT,
        )

        bar_x = 280
        bar_y = y + 3
        bar_width = 650
        bar_height = 28

        start_hour = 8
        end_hour = 23

        total_hours = end_hour - start_hour

        day_start = self.timezone.localize(
            datetime(
                date.year,
                date.month,
                date.day,
                start_hour,
                0,
            )
        )

        day_end = self.timezone.localize(
            datetime(
                date.year,
                date.month,
                date.day,
                end_hour,
                0,
            )
        )

        # Full day is available by default.
        draw.rectangle(
            (
                bar_x,
                bar_y,
                bar_x + bar_width,
                bar_y + bar_height,
            ),
            fill=config.AVAILABLE,
        )

        # Draw booked areas.
        for event in self.events:

            (
                event_start,
                event_end,
                all_day,
            ) = self._parse_event_times(event)

            if event_end <= day_start:
                continue

            if event_start >= day_end:
                continue

            if all_day:
                visible_start = day_start
                visible_end = day_end

            else:
                visible_start = max(
                    event_start,
                    day_start,
                )

                visible_end = min(
                    event_end,
                    day_end,
                )

            start_minutes = (
                visible_start.hour * 60
                + visible_start.minute
                - start_hour * 60
            )

            end_minutes = (
                visible_end.hour * 60
                + visible_end.minute
                - start_hour * 60
            )

            total_minutes = (
                total_hours * 60
            )

            x1 = (
                bar_x
                + bar_width
                * start_minutes
                / total_minutes
            )

            x2 = (
                bar_x
                + bar_width
                * end_minutes
                / total_minutes
            )

            draw.rectangle(
                (
                    x1,
                    bar_y,
                    x2,
                    bar_y + bar_height,
                ),
                fill=config.BOOKED,
            )

        return y + 70

    def _generate_language(
        self,
        language,
        output_path,
    ):
        """
        Generates one language version.
        """

        self.language = language

        image = Image.new(
            "RGB",
            (
                config.WIDTH,
                config.HEIGHT,
            ),
            config.BACKGROUND,
        )

        draw = ImageDraw.Draw(image)

        fonts = self._create_fonts()

        self._draw_header(
            draw,
            fonts["header"],
            language,
        )

        self._draw_time_scale(
            draw,
            fonts["small"],
        )

        now = datetime.now(
            self.timezone
        )

        y = 125

        for offset in range(
            config.DAYS_TO_SHOW
        ):

            date = (
                now
                + timedelta(days=offset)
            ).date()

            y = self._draw_day(
                draw,
                date,
                y,
                fonts["day"],
            )

            if y > config.HEIGHT - 80:
                break

        image.save(
            output_path,
            "PNG",
        )

        print(
            f"Availability image created: "
            f"{output_path}"
        )

    def generate(self):
        """
        Generates both English and Ukrainian images.
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
