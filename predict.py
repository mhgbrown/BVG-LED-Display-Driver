# -*- coding: utf-8 -*-

# http://ip-api.com/json?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query

# NextBus prediction class.  For each route/stop, NextBus server is polled
# automatically at regular intervals.  Front-end app just needs to init
# this with stop data, which can be found using the routefinder.py script.

# predictions need to be the the things that are leaving the soonest
# that don't leave now
# and that are on different gleises
#	which means, gl. 1 and 2 for s-bahn
# 	and different directions for tram -> we can't determine from the 
# 	information given how to differentiate between different directions
#	
# maybe we can hint the system
# provide a list of stations 
# be able to say soonest +X
# (BVG, matcher/line, =/- (matcher/line), stop, direction, [X])

import sys
import threading
import time
import urllib
import json
import re
from xml.dom.minidom import parseString

class predict:
	interval  = 30  # Default polling interval = 2 minutes
	initSleep = 0   # Stagger polling threads to avoid load spikes

	# predict object initializer.  1 parameter, a 4-element tuple:
	# First element is agengy tag (e.g. 'actransit')
	# Second is line tag (e.g. '210')
	# Third is stop tag (e.g. '0702630')
	# Fourth is direction -- not a tag, this element is human-readable
	# and editable (e.g. 'Union Landing') -- for UI purposes you may
	# want to keep this short.  The other elements MUST be kept
	# verbatim as displayed by the routefinder.py script.
	# Each predict object spawns its own thread and will perform
	# periodic server queries in the background, which can then be
	# read via the predictions[] list (est. arrivals, in seconds).
	def __init__(self, data):
		self.data 				= data
		self.predictions   		= []
		self.displayDirection 	= ''
		self.displayLine		= ''
		self.lastQueryTime 		= time.time()
		t                  		= threading.Thread(target=self.thread)
		t.daemon           		= True
		t.start()

	# Periodically get predictions from server ---------------------------
	def thread(self):
		initSleep          = predict.initSleep
		predict.initSleep += 5   # Thread staggering may
		time.sleep(initSleep)    # drift over time, no problem
		while True:
			dom = predict.req(self.data[2])
			newList = []
			
			# Connection error
			if dom is None:
				self.displayLine = 'XX'
				self.displayDirection = 'Error'
			else:
				self.lastQueryTime = time.time()
				matches = []
				soonestCount = 0;
				lineRegex = re.compile(self.data[1])
				directionRegex = re.compile(self.data[3])
				for stopInfo in dom[0][1]:
					lineMatches = lineRegex.findall(stopInfo['line'])
					if (lineMatches) and (self.data[3] in stopInfo['end']) and (stopInfo['remaining'] > 0):
						if soonestCount == self.data[4]:
							self.displayLine = stopInfo['line']
							self.displayDirection = stopInfo['end']
							newList.append(stopInfo['remaining'])
							if lineMatches[0] != stopInfo['line']:
								self.displayLine = self.displayLine.replace(lineMatches[0], '').strip()
							break
						
						if lineMatches[0] in matches:
							soonestCount += 1
						else:
							matches.append(lineMatches[0])
						# if we've seen what the regex matched before +1
						# if its a new thing, don't +1								
			
			# set new list of predictions
			self.predictions = newList
			time.sleep(predict.interval)

	# Open URL, send request, read & parse JSON response
	@staticmethod
	def req(station):
		jsonData = None
		try:
			connection = urllib.urlopen(
			  'https://bvg-grabber-api.herokuapp.com/actual' +
			  '?station=' + station)
			raw = connection.read()
			connection.close()
			# TODO support ü, ß, etc.
			raw = raw.decode('utf8').encode('ascii', 'replace')
			jsonData = json.loads(raw)
		except:
			print "Something happened while trying to get predictions..."
			print sys.exc_info()
		finally:
			return jsonData

	# Set polling interval (seconds) -------------------------------------
	@staticmethod
	def setInterval(i):
		interval = i
