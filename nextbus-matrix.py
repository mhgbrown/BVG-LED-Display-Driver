# -*- coding: utf-8 -*-

# NextBus scrolling marquee display for Adafruit RGB LED matrix (64x32).
# Requires rgbmatrix.so library: github.com/adafruit/rpi-rgb-led-matrix

import atexit
import Image
import ImageDraw
import ImageFont
import math
import os
import time
from predict import predict
from rgbmatrix import Adafruit_RGBmatrix

# Configurable stuff ---------------------------------------------------------

# List of bus lines/stops to predict.  Use routefinder.py to look up
# lines/stops for your location, copy & paste results here.  The 4th
# string on each line can then be edited for brevity if desired.
stops = [
  ( 'BVG', 'Tra', 'S Prenzlauer Allee (Berlin)', 'Alexanderplatz', 0 ),
  ( 'BVG', '\(Gl. 1\)', 'S Prenzlauer Allee (Berlin)', '', 0 ),
  ( 'BVG', '\(Gl. 2\)', 'S Prenzlauer Allee (Berlin)', '', 0 ),
  ( 'BVG', '\(Gl. [12]{1}\)', 'S Prenzlauer Allee (Berlin)', '', 1 )]

maxPredictions = 1   # NextBus shows up to 5; limit to 3 for simpler display
minTime        = -1   # Drop predictions below this threshold (minutes)
shortTime      = 3   # Times less than this are displayed in red
midTime        = 7  # Times less than this are displayed yellow

width          = 64  # Matrix size (pixels) -- change for different matrix
height         = 32  # types (incl. tiling).  Other code may need tweaks.
matrix         = Adafruit_RGBmatrix(32, 2) # rows, chain length
fps            = 5  # Scrolling speed (ish)

routeColor     = (  0,   0, 255) # Color for route labels (usu. numbers)
descColor      = (110, 110, 110) # " for route direction/description
longTimeColor  = (  0, 255,   0) # Ample arrival time = green
midTimeColor   = (255, 255,   0) # Medium arrival time = yellow
shortTimeColor = (255,   0,   0) # Short arrival time = red
minsColor      = (110, 110, 110) # Commans and 'minutes' labels
noTimesColor   = (  0,   0, 255) # No predictions = blue

#routeColor     = (255, 255, 255) # Color for route labels (usu. numbers)
#descColor      = (255, 140, 0) # " for route direction/description
#longTimeColor  = (255, 140, 0) # Ample arrival time = green
#midTimeColor   = (255, 140, 0) # Medium arrival time = yellow
#shortTimeColor = (255, 140, 0) # Short arrival time = red
#minsColor      = (255, 140, 0) # Commans and 'minutes' labels
#noTimesColor   = (255, 255, 255) # No predictions = blue

# TrueType fonts are a bit too much for the Pi to handle -- slow updates and
# it's hard to get them looking good at small sizes.  A small bitmap version
# of Helvetica Regular taken from X11R6 standard distribution works well:
font           = ImageFont.load(os.path.dirname(os.path.realpath(__file__))
                   + '/fonts/helvetica-8.pil')
fontYoffset    = -2  # Scoot up a couple lines so descenders aren't cropped


# Main application -----------------------------------------------------------

# Drawing takes place in offscreen buffer to prevent flicker
image       = Image.new('RGB', (width, height))
draw        = ImageDraw.Draw(image)
currentTime = 0.0
prevTime    = 0.0

# Clear matrix on exit.  Otherwise it's annoying if you need to break and
# fiddle with some code while LEDs are blinding you.
def clearOnExit():
	matrix.Clear()

atexit.register(clearOnExit)

# Populate a list of predict objects (from predict.py) from stops[].
# While at it, also determine the widest tile width -- the labels
# accompanying each prediction.  The way this is written, they're all the
# same width, whatever the maximum is we figure here.
tileWidth = font.getsize(
  '88' *  maxPredictions    +          # 2 digits for minutes
  ', ' * (maxPredictions-1) +          # comma+space between times
  ' minutes')[0]                       # 1 space + 'minutes' at end
w = font.getsize('XX')[0]  # Label when no times are available
if w > tileWidth:                      # If that's wider than the route
	tileWidth = w                  # description, use as tile width.
predictList = []                       # Clear list
for s in stops:                        # For each item in stops[] list...
	predictList.append(predict(s)) # Create object, add to predictList[]
	w = font.getsize(s[1] + ' ' + s[3])[0] # Route label
	if(w > tileWidth):                     # If widest yet,
		tileWidth = w                  # keep it
tileWidth += 6                         # Allow extra space between tiles


class tile:
	def __init__(self, x, y, p):
		self.x = x
		self.y = y
		self.predictionSize = 2
		self.p = p  # Corresponding predictList[] object

	def draw(self):
		x     = self.x
		#label = self.p.data[1] 
		
		# Route direction/desc
		label = self.p.displayDirection      
		draw.text((x, self.y + fontYoffset), label, font=font,
		  fill=descColor)
		
		# Route number or code
		label = self.p.displayLine
		draw.rectangle((0, self.y, font.getsize(label)[0], self.y + 8), fill=(0, 0, 0))
		draw.text((0, self.y + fontYoffset), label, font=font,
		  fill=routeColor)
		  
		x = self.x
		if self.p.predictions == []: # No predictions to display
			draw.rectangle((width - font.getsize('XX')[0], self.y, width, self.y + 8), fill=(0, 0, 0))
			draw.text((width - font.getsize('XX')[0] - 1, self.y + fontYoffset),
			  'XX', font=font, fill=noTimesColor)
		else:
			isFirstShown = True
			count        = 0
			for p in self.p.predictions:
				t = p
				m = int(t / 60)
				if   m <= minTime:   continue
				elif m <= shortTime: fill=shortTimeColor
				elif m <= midTime:   fill=midTimeColor
				else:                fill=longTimeColor
				if isFirstShown:
					isFirstShown = False
				else:
					label = ', '
					# The comma between times needs to
					# be drawn in a goofball position
					# so it's not cropped off bottom.
					draw.text((x + 1,
					  self.y + fontYoffset - 2),
					  label, font=font, fill=minsColor)
					x += font.getsize(label)[0]
				label  = str(m)
				self.predictionSize = font.getsize(label)[0]
				draw.rectangle((width - font.getsize(label)[0], self.y, width, self.y + 8), fill=(0, 0, 0))
				draw.text((width - font.getsize(label)[0] - 1, self.y + fontYoffset),
				  label, font=font, fill=fill)
				x     += font.getsize(label)[0]
				count += 1
				if count >= maxPredictions:
					break

# Allocate list of tile objects, enough to cover screen while scrolling
tileList = []
if tileWidth >= width: tilesAcross = 2
else:                  tilesAcross = int(math.ceil(width / tileWidth)) + 1

y = 0;
for pred in predictList:
	tileList.append(tile(0, y * 8, pred))
	y += 1

# Initialization done; loop forever ------------------------------------------
while True:
	# Clear background
	draw.rectangle((0, 0, width, height), fill=(0, 0, 0))

	for t in tileList: 
		
		if font.getsize(t.p.displayDirection)[0] > 0:
			t.x -= 1
		
		if t.x + font.getsize(t.p.displayDirection)[0] - font.getsize(t.p.displayLine)[0] <= 0:
			t.x = width - t.predictionSize
			
		if t.x < width:        # Draw tile if onscreen
			t.draw()

	# Try to keep timing uniform-ish; rather than sleeping a fixed time,
	# interval since last frame is calculated, the gap time between this
	# and desired frames/sec determines sleep time...occasionally if busy
	# (e.g. polling server) there'll be no sleep at all.
	# time.sleep(0.05)
	currentTime = time.time()
	timeDelta   = (1.0 / fps) - (currentTime - prevTime)
	if(timeDelta > 0.0):
		time.sleep(timeDelta)
	prevTime = currentTime

	# Offscreen buffer is copied to screen
	matrix.SetImage(image.im.id, 0, 0)
