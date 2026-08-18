from pathlib import Path


# ============================================================
# GOOGLE CALENDAR
# ============================================================

TIMEZONE = "Europe/Kyiv"

DAYS_TO_SHOW = 14

SERVICE_ACCOUNT_FILE = "service-account.json"


# Calendars used by CalendarReader
CALENDAR_IDS = [
    "nik.den.hot@gmail.com",
]


# Main calendar
# Kept for compatibility with other project modules.
CALENDAR_ID = "nik.den.hot@gmail.com"


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_DIR = Path("output")

OUTPUT_IMAGE = OUTPUT_DIR / "availability.png"

OUTPUT_IMAGE_UK = OUTPUT_DIR / "availability_uk.png"


# ============================================================
# FONTS
# ============================================================

FONT_PATH = Path("fonts") / "arial.ttf"


# ============================================================
# IMAGE
# ============================================================

WIDTH = 1000

HEIGHT = 1200

BACKGROUND = "#111111"

TEXT = "#FFFFFF"

AVAILABLE = "#D7DED2"

LIMITED = "#D88932"

BOOKED = "#D83A3A"


# ============================================================
# FONT SIZES
# ============================================================

HEADER_SIZE = 46

DAY_SIZE = 30

SMALL_SIZE = 22