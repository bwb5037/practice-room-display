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

ensemble_names = {
    "String Orchestra",
    "Concert Orchestra",
    "Symphonic Band",
    "Wind Symphony",
}

reservations = {i: [] for i in range(1, 11)}

for period, entries in periods.items():

    i = 0

    while i < len(entries):

        if entries[i] not in room_names:
            i += 1
            continue

        room = entries[i]
        j = i + 1
        students = []

        while j < len(entries) and entries[j] not in room_names:

            candidate = entries[j].strip()

            if candidate.lower() == "unavailable":
                j += 1
                continue

            parts = [
                part.strip()
                for part in candidate.split(",")
                if part.strip()
            ]

            for part in parts:

                # Remove any ensemble/class labels
                if any(
                    part.lower() == ensemble.lower()
                    for ensemble in ensemble_names
                ):
                    continue

                # Ignore period markers
                if part.lower().startswith("period"):
                    continue

                students.append(part)

            j += 1

        if students:

            # Remove duplicates but preserve order
            students = list(dict.fromkeys(students))

            reservations[period].append(
                (room, ", ".join(students))
            )

        i = j


# --------------------------------------------------
# COMBINE DUPLICATE ROOMS
# --------------------------------------------------

combined = {i: {} for i in range(1, 11)}

for period, items in reservations.items():

    for room, student_string in items:

        if room not in combined[period]:
            combined[period][room] = []

        for student in [
            s.strip()
            for s in student_string.split(",")
            if s.strip()
        ]:

            if student not in combined[period][room]:
                combined[period][room].append(student)


reservations = {i: [] for i in range(1, 11)}

for period in range(1, 11):

    for room, students in combined[period].items():

        clean_students = []

        for student in students:

            # Split again in case a combined string slipped through
            parts = [
                p.strip()
                for p in student.split(",")
                if p.strip()
            ]

            for part in parts:

                if part in ensemble_names:
                    continue

                if part not in clean_students:
                    clean_students.append(part)

        if clean_students:
            reservations[period].append(
                (room, ", ".join(clean_students))
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
