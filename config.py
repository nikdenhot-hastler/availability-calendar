from pathlib import Path

# ===== Google Calendar =====

TIMEZONE = "Europe/Kyiv"
DAYS_TO_SHOW = 14

# Шлях до JSON Service Account
SERVICE_ACCOUNT_FILE = "service-account.json"

# Email або ID календаря
CALENDAR_ID = "nik.den.hot@gmail.com"


# ===== Output =====

OUTPUT_DIR = Path("output")
OUTPUT_IMAGE = OUTPUT_DIR / "availability.png"


# ===== Image =====

WIDTH = 1000
HEIGHT = 1200

BACKGROUND = "#111111"

TEXT = "#FFFFFF"

AVAILABLE = "#35C759"

LIMITED = "#FFCC00"

BOOKED = "#FF453A"

HEADER_SIZE = 46

DAY_SIZE = 30

SMALL_SIZE = 22
