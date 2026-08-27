import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

URL = "https://hersheyhsmusic.com/schedule"
OUTPUT = "lobby.png"

response = requests.get(URL, timeout=20)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")
text = soup.get_text("\n", strip=True)

lines = [line.strip() for line in text.splitlines() if line.strip()]

periods = {}
current_period = None

for line in lines:
    if line.startswith("Period "):
        current_period = line
        periods[current_period] = []
    elif current_period:
        if line not in {
            "Unavailable",
            "Loading...",
            "Refreshes every 5 minutes",
            "Schedule date",
            "Today",
        }:
            periods[current_period].append(line)

# Create 1920 x 1080 image
img = Image.new("RGB", (1920, 1080), "white")
draw = ImageDraw.Draw(img)

# Fonts
try:
    title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 72)
    date_font = ImageFont.truetype("DejaVuSans.ttf", 38)
    period_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 38)
    text_font = ImageFont.truetype("DejaVuSans.ttf", 28)
except:
    title_font = ImageFont.load_default()
    date_font = ImageFont.load_default()
    period_font = ImageFont.load_default()
    text_font = ImageFont.load_default()

draw.text(
    (80, 50),
    "Practice Room Reservations",
    font=title_font,
    fill="black"
)

draw.text(
    (82, 145),
    datetime.now().strftime("%A, %B %d, %Y"),
    font=date_font,
    fill="black"
)

x_positions = [80, 680, 1280]
y_start = 230
column = 0
y = y_start

for period, entries in periods.items():
    if y > 900:
        column += 1
        if column >= len(x_positions):
            break
        y = y_start

    x = x_positions[column]

    draw.text((x, y), period, font=period_font, fill="black")
    y += 55

    for entry in entries:
        if y > 930:
            column += 1
            if column >= len(x_positions):
                break
            x = x_positions[column]
            y = y_start

        draw.text((x + 20, y), entry, font=text_font, fill="black")
        y += 38

    y += 30

img.save(OUTPUT)
print(f"Created {OUTPUT}")
