import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

URL = "https://hersheyhsmusic.com/schedule"
OUTPUT = "lobby.png"

response = requests.get(URL, timeout=20)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

# Get visible text
lines = [
    x.strip()
    for x in soup.get_text("\n", strip=True).splitlines()
    if x.strip()
]

# Remove obvious website clutter
ignore = [
    "Practice Room Schedule",
    "Refreshes every 5 minutes",
    "Loading...",
]

lines = [
    line for line in lines
    if line not in ignore
]

# Canvas
WIDTH = 1920
HEIGHT = 1080

img = Image.new("RGB", (WIDTH, HEIGHT), "white")
draw = ImageDraw.Draw(img)

def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(name, size)

# HEADER
draw.text(
    (80, 45),
    "PRACTICE ROOM RESERVATIONS",
    font=font(64, True),
    fill="black"
)

draw.text(
    (82, 125),
    datetime.now().strftime("%A, %B %d, %Y"),
    font=font(32),
    fill="black"
)

# Divider
draw.line((80, 185, 1840, 185), fill="black", width=3)

# Split information into two columns
midpoint = (len(lines) + 1) // 2

columns = [
    lines[:midpoint],
    lines[midpoint:]
]

x_positions = [90, 990]

for col_num, column in enumerate(columns):

    x = x_positions[col_num]
    y = 225

    # Dynamically size text
    available_height = 790
    count = max(len(column), 1)

    line_height = min(48, available_height // count)
    text_size = max(20, min(34, line_height - 7))

    for line in column:

        # Make periods stand out
        if line.lower().startswith("period"):
            f = font(text_size + 5, True)
            y += 10
        else:
            f = font(text_size)

        draw.text(
            (x, y),
            line[:52],
            font=f,
            fill="black"
        )

        y += line_height

img.save(OUTPUT)
print("Created lobby.png")
