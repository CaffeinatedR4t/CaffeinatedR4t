from PIL import Image
from collections import Counter
import sys

def to_hex(color):
    if len(color) == 4:
        r, g, b, a = color
    else:
        r, g, b = color
    return f"#{r:02x}{g:02x}{b:02x}"

img = Image.open(r"C:\Users\Jeremy yosep pohar\.gemini\antigravity-cli\brain\4f1b2980-852e-4d03-9b61-a1df23aaa5ad\.user_uploaded\uploaded_media_1_1786272727200.png").convert("RGB")
w, h = img.size

# Background color (usually top left)
bg_color = img.getpixel((10, 10))
print(f"Background: {to_hex(bg_color)}")

colors = img.getcolors(maxcolors=100000)
# sort by count
colors = sorted(colors, key=lambda x: x[0], reverse=True)

# Find prominent non-background colors
# We know labels are orangeish, values are blueish/cyanish, ascii is grey/white, dots are darker grey.

def is_orange(c):
    r,g,b = c
    return r > 150 and r > g + 20 and g > b + 20

def is_cyan(c):
    r,g,b = c
    return b > 150 and g > 150 and r < b - 20

def is_white_grey(c):
    r,g,b = c
    return r > 150 and abs(r-g) < 15 and abs(g-b) < 15

def is_dark_grey(c):
    r,g,b = c
    return 50 < r < 120 and abs(r-g) < 15 and abs(g-b) < 15

orange_found = False
cyan_found = False
white_found = False
grey_found = False

for count, color in colors:
    # skip background
    if sum(abs(a-b) for a,b in zip(color, bg_color)) < 20:
        continue
    
    if not orange_found and is_orange(color):
        print(f"Label (Orange): {to_hex(color)}")
        orange_found = True
        
    if not cyan_found and is_cyan(color):
        print(f"Value (Cyan): {to_hex(color)}")
        cyan_found = True
        
    if not white_found and is_white_grey(color) and count > 10:
        print(f"Header/ASCII (White/Grey): {to_hex(color)}")
        white_found = True
        
    if not grey_found and is_dark_grey(color) and count > 10:
        print(f"Dots/Dashes (Dark Grey): {to_hex(color)}")
        grey_found = True
        
    if orange_found and cyan_found and white_found and grey_found:
        break
