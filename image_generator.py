"""
Availability image generator.

Creates a public availability image from Google Calendar events.
Event titles and private calendar information are never displayed.
"""

from datetime import datetime, timedelta

import pytz
from PIL import Image, ImageDraw, ImageFont

import config


class AvailabilityImageGenerator:

    def __init__(self, events):
        self.events = events
        self.timezone = pytz.timezone(config.TIMEZONE)

        config.OUTPUT_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.image = Image.new(
            "RGB",
            (config.WIDTH, config.HEIGHT),
            config.BACKGROUND,
        )

        self.draw = ImageDraw.Draw(self.image)

        font_path = self._font_path()

        self.font_header = ImageFont.truetype(
            font_path,
            config.HEADER_SIZE,
        )

        self.font_day = ImageFont.truetype(
            font_path,
            config.DAY_SIZE,
        )

        self.font_small = ImageFont.truetype(
            font_path,
            config.SMALL_SIZE,
        )

    def _font_path(self):
        """
        Returns a font path that works on Windows
        and GitHub Actions Linux runners.
        """

        local_font = getattr(
            config,
            "FONT_PATH",
            None,
        )

        if local_font:
            return str(local_font)

        # GitHub Actions / Linux
        linux_font = (
            "/usr/share/fonts/truetype/dejavu/"
            "DejaVuSans.ttf"
        )

        return linux_font

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

    def _draw_header(self):
        """
        Draws the public header.
        """

        self.draw.text(
            (40, 30),
            "AVAILABILITY",
            font=self.font_header,
            fill=config.TEXT,
        )

    def _draw_time_scale(self):
        """
        Draws hourly time scale.
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

            bbox = self.draw.textbbox(
                (0, 0),
                label,
                font=self.font_small,
            )

            label_width = (
                bbox[2] - bbox[0]
            )

            self.draw.text(
                (
                    x - label_width / 2,
                    y,
                ),
                label,
                font=self.font_small,
                fill=config.TEXT,
            )

    def _draw_day(self, date, y):
        """
        Draws one day.

        Green = available.
        Red = booked.

        Booked intervals are continuous and use
        exact event start/end times, including minutes.
        """

        date_text = date.strftime(
            "%a, %d %b"
        )

        self.draw.text(
            (40, y),
            date_text,
            font=self.font_day,
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
        self.draw.rectangle(
            (
                bar_x,
                bar_y,
                bar_x + bar_width,
                bar_y + bar_height,
            ),
            fill=config.AVAILABLE,
        )

        # Draw continuous booked areas.
        for event in self.events:

            event_start, event_end, all_day = (
                self._parse_event_times(event)
            )

            # Event does not overlap visible period.
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

            self.draw.rectangle(
                (
                    x1,
                    bar_y,
                    x2,
                    bar_y + bar_height,
                ),
                fill=config.BOOKED,
            )

        return y + 70

    def generate(self):
        """
        Generates and saves availability image.
        """

        self._draw_header()

        self._draw_time_scale()

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
                date,
                y,
            )

            if y > config.HEIGHT - 80:
                break

        self.image.save(
            config.OUTPUT_IMAGE,
            "PNG",
        )

        print()

        print(
            f"Availability image created: "
            f"{config.OUTPUT_IMAGE}"
        )
