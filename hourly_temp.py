from PIL import Image, ImageFont, ImageDraw
import sys

X_FACTOR = 2
LEFT_MARGIN = 10
Y_FACTOR = 20
BOTTOM_MARGIN = 10
im = Image.new("RGB", (LEFT_MARGIN + X_FACTOR * (7*31 + 4*30 + 28) + 1, Y_FACTOR * 4 + BOTTOM_MARGIN))
width, height = im.size
pix = im.load()

months = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]

accum = [] # will be [0, 31, 31+28, 31+28+31, ...]
days_so_far = 0
for month in months:
    accum.append(days_so_far)
    days_so_far += month

# Start by painting everything white
for i in range(width):
    for j in range(height):
        pix[i, j] = (255, 255, 255)

# Ticks on X-axis
prev = LEFT_MARGIN
for x in months:
    prev += X_FACTOR * x
    for y in range(BOTTOM_MARGIN):
        pix[prev, Y_FACTOR * 4 + y] = (255,0,0)

# Ticks on Y-axis
prev = 0
for x in range(LEFT_MARGIN):
    for h in range(4+1):
        pix[x, h * Y_FACTOR] = (0, 0, 0)

# Helps to find y pixel for a particular hour of the day
def hour_bucket(hour):
    if hour < 6:
        return 0
    elif hour < 12:
        return 1
    elif hour < 18:
        return 2
    else:
        return 3

# Colors depending on temperature
SWELTERING = (150, 75, 70) # red brown
HOT = (174, 91, 91) # red pink
WARM = (198, 117, 98) # red orange
COMFORTABLE = (232, 203, 124) # yellow
COOL = (142, 190, 116) # light green
COLD = (117, 167, 120) # green 
VERY_COLD = (104, 148, 105) # dark green
FREEZING = (133, 194, 212) # blue
FRIGID = (30, 30, 30) # dark grey

#frigid < -9°C < freezing < 0°C < very cold < 7°C < cold < 13°C < cool < 18°C < comfortable < 24°C < warm < 29°C < hot < 35°C < sweltering. The shaded overlays indicate night and civil twilight.

def kelvin(c):
    return c + 273.15

def temp_color(t):
    if t < kelvin(-9):
        return FRIGID
    elif t < kelvin(0):
        return FREEZING
    elif t < kelvin(7):
        return VERY_COLD
    elif t < kelvin(13):
        return COLD
    elif t < kelvin(18):
        return COOL
    elif t < kelvin(24):
        return COMFORTABLE
    elif t < kelvin(29):
        return WARM
    elif t < kelvin(35):
        return HOT
    else:
        return SWELTERING


# Draw data
with open(sys.argv[1], 'r') as filer:
    for line in filer:
        line = line[:-1] # get rid of CR or LF at end of line
        sy, sm, sd, sh, stemp = line.split()
        y = int(sy)
        m = int(sm)
        d = int(sd)
        h = int(sh)
        temp = float(stemp)

        for x in range(X_FACTOR):
            for y in range(Y_FACTOR):
                pix[LEFT_MARGIN + X_FACTOR * (accum[m] + (d-1)) + x, Y_FACTOR * hour_bucket(h) + y] = temp_color(temp)

#im.save("test.png", "PNG")
im.show()
