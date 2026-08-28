import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import re

URL = "https://hersheyhsmusic.com/schedule"
OUTPUT = "lobby.png"

WIDTH = 1920
HEIGHT = 1080

# --------------------------------------------------
# GET SCHEDULE
# --------------------------------------------------

response = requests.get(URL, timeout=20)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

lines = [
    line.strip()
    for line in soup.get_text("\n", strip=True).splitlines()
    if line.strip()
]

# --------------------------------------------------
# PARSE PERIODS
# --------------------------------------------------

periods = {i: [] for i in range(1, 11)}

current_period = None
i = 0

while i < len(lines):

    line = lines[i]

    # Website outputs "Period" and number separately
    if line == "Period" and i + 1 < len(lines):
        if lines[i + 1].isdigit():
            number = int(lines[i + 1])

            if 1 <= number <= 10:
                current_period = number
                i += 2
                continue

    # Also handle "Period 4" if format changes
    match = re.match(r"^Period\s+(\d+)$", line, re.IGNORECASE)

    if match:
        number = int(match.group(1))

        if 1 <= number <= 10:
            current_period = number
            i += 1
            continue

    if current_period is not None:

        # Ignore unavailable rooms
        if line.lower() == "unavailable":
            i += 1
            continue

        periods[current_period].append(line)

    i += 1


# --------------------------------------------------
# CLEAN ROOM / NAME PAIRS
# --------------------------------------------------

room_names = {
    "Lunch Table",
    "Practice Room 2",
    "Practice Room 3",
    "Practice Room 5 - Percussion",
    "Band Room",
    "Orchestra Room",
    "Piano Lab",
}

reservations = {i: [] for i in range(1, 11)}

for period, entries in periods.items():

    i = 0

    while i < len(entries):

        entry = entries[i]

        if entry in room_names:

            # Next item should be reservation/name
            if i + 1 < len(entries):
                next_entry = entries[i + 1]

                # If next entry isn't another room,
                # treat it as the reservation
                if next_entry not in room_names:
                    reservations[period].append(
                        (entry, next_entry)
                    )
                    i += 2
                    continue

        i += 1


# --------------------------------------------------
# CREATE IMAGE
# --------------------------------------------------

img = Image.new(
    "RGB",
    (WIDTH, HEIGHT),
    (248, 249, 250)
)

draw = ImageDraw.Draw(img)


def font(size, bold=False):
    filename = (
        "DejaVuSans-Bold.ttf"
        if bold
        else "DejaVuSans.ttf"
    )

    return ImageFont.truetype(filename, size)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

draw.text(
    (70, 35),
    "PRACTICE ROOM RESERVATIONS",
    font=font(60, True),
    fill=(25, 25, 25)
)

draw.text(
    (72, 112),
    datetime.now().strftime("%A, %B %d, %Y"),
    font=font(30),
    fill=(80, 80, 80)
)

draw.line(
    (70, 170, 1850, 170),
    fill=(40, 40, 40),
    width=3
)


# --------------------------------------------------
# PERIOD CARDS
# --------------------------------------------------

margin_x = 65
top = 205
gap = 18

columns = 5
rows = 2

card_width = int(
    (WIDTH - (margin_x * 2) - (gap * 4)) / 5
)

card_height = 390


for period in range(1, 11):

    index = period - 1

    row = index // 5
    col = index % 5

    x1 = margin_x + col * (card_width + gap)
    y1 = top + row * (card_height + gap)

    x2 = x1 + card_width
    y2 = y1 + card_height

    # Card background
    draw.rounded_rectangle(
        (x1, y1, x2, y2),
        radius=18,
        fill=(255, 255, 255),
        outline=(205, 210, 215),
        width=2
    )

    # Period header
    draw.rounded_rectangle(
        (x1, y1, x2, y1 + 70),
        radius=18,
        fill=(35, 35, 35)
    )

    # Cover lower rounded corners of header
    draw.rectangle(
        (x1, y1 + 50, x2, y1 + 70),
        fill=(35, 35, 35)
    )

    draw.text(
        (x1 + 20, y1 + 15),
        f"PERIOD {period}",
        font=font(28, True),
        fill="white"
    )

    y = y1 + 92

    period_reservations = reservations[period]

    if not period_reservations:

        draw.text(
            (x1 + 20, y),
            "No reservations",
            font=font(22),
            fill=(145, 145, 145)
        )

    else:

        # Reduce font slightly when period is busy
        count = len(period_reservations)

        if count <= 3:
            room_font = font(20, True)
            name_font = font(19)
            spacing = 83

        elif count <= 4:
            room_font = font(18, True)
            name_font = font(17)
            spacing = 70

        else:
            room_font = font(16, True)
            name_font = font(15)
            spacing = 58

        for room, name in period_reservations:

            if y > y2 - 55:
                break

            draw.text(
                (x1 + 18, y),
                room,
                font=room_font,
                fill=(35, 35, 35)
            )

            draw.text(
                (x1 + 18, y + 28),
                name,
                font=name_font,
                fill=(85, 85, 85)
            )

            y += spacing


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

draw.text(
    (70, 1040),
    "hersheyhsmusic.com/schedule",
    font=font(20),
    fill=(120, 120, 120)
)

img.save(OUTPUT)

print("Created lobby.png")

for period in range(1, 11):
    print(f"Period {period}: {reservations[period]}")
