from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import re

URL = "https://hersheyhsmusic.com/schedule"
OUTPUT = "lobby.png"

WIDTH = 1920
HEIGHT = 1080

ROOM_NAMES = [
    "PRACTICE ROOM 5 - PERCUSSION",
    "PRACTICE ROOM 3",
    "PRACTICE ROOM 2",
    "MUSIC LIBRARY",
    "ORCHESTRA ROOM",
    "BAND ROOM",
    "LUNCH TABLE",
    "PIANO LAB",
]

# --------------------------------------------------
# LOAD LIVE PAGE
# --------------------------------------------------

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page(
        viewport={"width": 1920, "height": 1080}
    )

    page.goto(
        URL,
        wait_until="networkidle",
        timeout=60000
    )

    page.wait_for_timeout(3000)

    text = page.locator("body").inner_text()

    browser.close()


lines = [
    line.strip()
    for line in text.splitlines()
    if line.strip()
]


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def is_room(line):
    return line.upper() in ROOM_NAMES


def display_room(line):
    mapping = {
        "PRACTICE ROOM 5 - PERCUSSION":
            "Practice Room 5 - Percussion",

        "PRACTICE ROOM 3":
            "Practice Room 3",

        "PRACTICE ROOM 2":
            "Practice Room 2",

        "MUSIC LIBRARY":
            "Music Library",

        "ORCHESTRA ROOM":
            "Orchestra Room",

        "BAND ROOM":
            "Band Room",

        "LUNCH TABLE":
            "Lunch Table",

        "PIANO LAB":
            "Piano Lab",
    }

    return mapping[line.upper()]


# --------------------------------------------------
# PARSE LIVE SCHEDULE
# --------------------------------------------------

reservations = {
    i: []
    for i in range(1, 11)
}

current_period = None
i = 0

while i < len(lines):

    line = lines[i]

    # -------------------------------
    # PERIOD
    # 1
    # -------------------------------

    if (
        line.upper() == "PERIOD"
        and i + 1 < len(lines)
        and lines[i + 1].isdigit()
    ):

        number = int(lines[i + 1])

        if 1 <= number <= 10:
            current_period = number

        i += 2
        continue

    # -------------------------------
    # ROOM
    # -------------------------------

    if (
        current_period is not None
        and is_room(line)
    ):

        room = display_room(line)

        if i + 1 >= len(lines):
            i += 1
            continue

        next_line = lines[i + 1]

        # ROOM -> Unavailable
        if next_line.lower() == "unavailable":
            i += 2
            continue

        # Otherwise:
        #
        # ROOM
        # ENSEMBLE
        # STUDENT(S)

        if i + 2 < len(lines):

            student_line = lines[i + 2]

            # Make sure the supposed student line
            # isn't actually another structural item.

            if (
                student_line.lower() != "unavailable"
                and student_line.upper() != "PERIOD"
                and not is_room(student_line)
            ):

                reservations[current_period].append(
                    (
                        room,
                        student_line
                    )
                )

                i += 3
                continue

    i += 1


# --------------------------------------------------
# COMBINE DUPLICATE ROOMS
# --------------------------------------------------

combined = {
    i: {}
    for i in range(1, 11)
}

for period, items in reservations.items():

    for room, names in items:

        combined[period].setdefault(
            room,
            []
        )

        for name in names.split(","):

            name = name.strip()

            if (
                name
                and name not in combined[period][room]
            ):
                combined[period][room].append(name)


reservations = {
    i: []
    for i in range(1, 11)
}

for period in range(1, 11):

    for room, names in combined[period].items():

        reservations[period].append(
            (
                room,
                ", ".join(names)
            )
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

    return ImageFont.truetype(
        filename,
        size
    )


# HEADER

draw.text(
    (70, 35),
    "PRACTICE ROOM RESERVATIONS",
    font=font(60, True),
    fill=(25, 25, 25)
)

draw.text(
    (72, 112),
    datetime.now().strftime(
        "%A, %B %d, %Y"
    ),
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

card_width = int(
    (
        WIDTH
        - (margin_x * 2)
        - (gap * 4)
    ) / 5
)

card_height = 390


for period in range(1, 11):

    index = period - 1
    row = index // 5
    col = index % 5

    x1 = (
        margin_x
        + col * (card_width + gap)
    )

    y1 = (
        top
        + row * (card_height + gap)
    )

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
        (
            x1,
            y1 + 50,
            x2,
            y1 + 70
        ),
        fill=(35, 35, 35)
    )

    draw.text(
        (x1 + 20, y1 + 15),
        f"PERIOD {period}",
        font=font(28, True),
        fill=(255, 255, 255)
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


# FOOTER

draw.text(
    (70, 1040),
    "hersheyhsmusic.com/schedule",
    font=font(20),
    fill=(120, 120, 120)
)


# SAVE

img.save(OUTPUT)

print("Created lobby.png")
print("")
print("--- PARSED RESERVATIONS ---")

for period in range(1, 11):
    print(
        f"Period {period}: "
        f"{reservations[period]}"
    )
