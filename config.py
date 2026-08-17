from pathlib import Path


# ============================================================
# GOOGLE CALENDAR
# ============================================================

TIMEZONE = "Europe/Kyiv"

DAYS_TO_SHOW = 14

# Шлях до JSON Service Account
SERVICE_ACCOUNT_FILE = "service-account.json"

# Основний календар.
# Залишаємо цей параметр, тому що main.py його використовує.
CALENDAR_ID = "nik.den.hot@gmail.com"

# Усі календарі, які використовуються для визначення зайнятості.
#
# Service Account має доступ до обох календарів:
# 1. Nik Den
# 2. Volodymyr Medyk
#
# Події з обох календарів об'єднуються.
CALENDAR_IDS = [
    "nik.den.hot@gmail.com",
    "vmedyk@gmail.com",
]


# ============================================================
# OUTPUT
# ============================================================

OUTPUT_DIR = Path("output")

OUTPUT_IMAGE = (
    OUTPUT_DIR
    / "availability.png"
)


# ============================================================
# IMAGE
# ============================================================

# Старі параметри залишаємо, щоб не ламати
# сумісність з іншими файлами проєкту.

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
