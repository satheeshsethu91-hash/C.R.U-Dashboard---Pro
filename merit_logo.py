import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont

# Image size and colors
width, height = 311, 117
bg_color = (15, 30, 60)  # Navy
border_color = (255, 255, 255)
text_color = (255, 255, 255)

# Create image
img = Image.new('RGB', (width, height), bg_color)
draw = ImageDraw.Draw(img)

# Border
draw.rectangle([0, 0, width-1, height-1], outline=border_color, width=7)

# Font
try:
    font = ImageFont.truetype("arial.ttf", 60)
except:
    font = ImageFont.load_default()

# Text
text = "MERIT"
text_width, text_height = draw.textsize(text, font=font)
x, y = (width - text_width)//2, (height - text_height)//2
draw.text((x, y), text, fill=text_color, font=font)

# Save
img.save("merit_logo.png")
