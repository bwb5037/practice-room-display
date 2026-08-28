import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import re

URL = "https://hersheyhsmusic.com/schedule"
OUTPUT = "lobby.png"

WIDTH = 1920
HEIGHT = 1080

ROOM_NAMES = [
    "Practice Room 5 - Percussion",
    "Practice Room 3",
    "Practice Room 2",
    "Music Library",
    "Orchestra Room",
    "Band Room",
    "Lunch Table",
    "Piano Lab",
]

ENSEMBLE_NAMES = [
    "String Orchestra",
    "Concert Orchestra",
    "Symphonic Band",
    "Wind Symphony",
]

# --------------------------------------------------
# GET PAGE
# --------------------------------------------------

response = requests.get(URL, timeout=20)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Get text, but normalize it carefully.
raw_lines = [
    x.strip()
    for x in soup.stripped_strings
    if x.strip()
]

# --------------------------------------------------
# NORMALIZE LINES
# --------------------------------------------------

lines = []

for text in raw_lines:

    # Some HTML elements contain room + ensemble + student
    # all in one BeautifulSoup string.
    # Split student names away from ensemble names.

    working = text

    # If this begins with a room, process specially
    room_found = None

    for room in ROOM_NAMES:
        if working.startswith(room):
            room_found = room
            break

    if room_found:

        remainder = working[len(room_found):].strip()

        # Remove ensemble names from beginning
        ensemble_text = remainder

        for ensemble in ENSEMBLE_NAMES:
            ensemble_text = ensemble_text.replace(ensemble, "")

        ensemble_text = ensemble_text.replace(",", " ").strip()

        # Keep original room line
        lines.append(working)

        # If anything remains after removing ensemble names,
        # it should be student text
        if ensemble_text:
            lines.append(ensemble_text)

    else:
        lines.append(working)


# --------------------------------------------------
# PARSE PERIODS
# --------------------------------------------------

periods = {i: [] for i in range(1, 11)}
current_period = None

for line in lines:

    match = re.fullmatch(r"Period\s+(\d+)", line, re.IGNORECASE)

    if match:

        number = int(match.group(1))

        if 1 <= number <= 10:
            current_period = number

        continue

    if current_period is not None:
        periods[current_period].append(line)


# --------------------------------------------------
# PARSE RESERVATIONS
# --------------------------------------------------

reservations = {i: [] for i in range(1, 11)}


def get_room(line):

    for room in ROOM_NAMES:

        if line.startswith(room):
            return room

    return None


for period, entries in periods.items():

    i = 0

    while i < len(entries):

        line = entries[i]

        room = get_room(line)

        if room is None:
            i += 1
            continue

        # Remove room name
        remainder = line[len(room):].strip()

        # Remove ensemble names
        student_text = remainder

        for ensemble in ENSEMBLE_NAMES:
            student_text = student_text.replace(ensemble, "")

        student_text = student_text.strip(" ,")

        # If student name is embedded in same HTML string
        if student_text:

            reservations[period].append(
                (room, student_text)
            )

            i += 1
            continue

        # Otherwise student should be next line
        if i + 1 < len(entries):

            candidate = entries[i + 1].strip()

            if (
                candidate.lower() != "unavailable"
                and get_room(candidate) is None
                and not candidate.lower().startswith("period")
            ):

                # Make sure candidate isn't only an ensemble
                cleaned = candidate

                for ensemble in ENSEMBLE_NAMES:
                    cleaned = cleaned.replace(ensemble, "")

                cleaned = cleaned.strip(" ,")

                if cleaned:
                    reservations[period].append(
                        (room, cleaned)
                    )

        i += 2


# --------------------------------------------------
# COMBINE DUPLICATE ROOMS
# --------------------------------------------------

combined = {i: {} for i in range(1, 11)}

for period, items in reservations.items():

    for room, names in items:

        combined[period].setdefault(room, [])

        for name in names.split(","):

            name = name.strip()

            if name and name not in combined[period][room]:
                combined[period][room].append(name)


reservations = {i: [] for i in range(1, 11)}

for period in range(1, 11):

    for room, names in combined[period].items():

        reservations[period].append(
            (room, ", ".join(names))
        )


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


# HEADER

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
# CARDS
# --------------------------------------------------

margin_x = 65
top = 205
gap = 18

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

    draw.rounded_rectangle(
        (x1, y1, x2, y2),
        radius=18,
        fill=(255, 255, 255),
        outline=(205, 210, 215),
        width=2
    )

    draw.rounded_rectangle(
        (x1, y1, x2, y1 + 70),
        radius=18,
        fill=(35, 35, 35)
    )

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

    items = reservations[period]

    if not items:

        draw.text(
            (x1 + 20, y),
            "No reservations",
            font=font(22),
            fill=(145, 145, 145)
        )

    else:

        count = len(items)

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

        for room, names in items:

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
                names,
                font=name_font,
                fill=(85, 85, 85)
            )

            y += spacing


draw.text(
    (70, 1040),
    "hersheyhsmusic.com/schedule",
    font=font(20),
    fill=(120, 120, 120)
)

img.save(OUTPUT)

print("Created lobby.png")

print("\n--- PARSED RESERVATIONS ---")

for period in range(1, 11):
    print(f"Period {period}: {reservations[period]}")
