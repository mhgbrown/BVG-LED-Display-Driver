# -*- coding: utf-8 -*-

# http://ip-api.com/json?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query
# https://v5.bvg.transport.rest/stops/nearby?latitude=52.52725&longitude=13.4123

import sys
import urllib
import json
import datetime
import dateutil.parser
from dateutil import tz

# we get all the stops
# then maybe this is what we do over and over again
# we iterate of the stops, getting departures
# we get all the departures for the all the stops
# we sort by departure time, we print the top 4
  
class station:
    def req(self, url):
	print 'req: ' + url
        jsonData = None
        try:
			connection = urllib.urlopen(url)
			raw = connection.read()
			connection.close()
			# TODO support ü, ß, etc.
			raw = raw.decode('utf8').encode('ascii', 'replace')
			print raw
			jsonData = json.loads(raw)
        except:
			print "Something happened while making the request..."
			print sys.exc_info()
        finally:
			return jsonData
    
    def fetch(self):
        location = self.get_location()
        stop_ids = self.get_stops(location[0], location[1])
	upcoming_departures = []
	depart_at = datetime.datetime.now(tz = tz.tzlocal())
	for stop_id in stop_ids:
	    departures = self.get_departures(stop_id, depart_at)
	    print departures
	    upcoming_departures += self.extract_and_format_departures(departures, depart_at)
	
	# sorted(upcoming_departures, key=lambda x: x[2])
        return sorted(upcoming_departures, key=lambda x: x[2])

    # goal is to get the first 4 departures where the time until next departure
    # is >= 1
    # go through all the departure
    # the output we want is
    # Name, Direction, seconds remaining until next departure
    # in the future we might want to display two numbers for the next two departures
    def extract_and_format_departures(self, departures=[], depart_at=None, departure_inclusion_threshold=60, max_num_departures=4):
	formatted_departures = []
	
	if depart_at is None:
	   depart_at = datetime.datetime.now(tz = tz.tzlocal())
	
	for departure in departures:
	   when = dateutil.parser.isoparse(departure['when'])
	   when_difference = when - depart_at
	   if when_difference.seconds < departure_inclusion_threshold:
		continue
		
	   formatted_departures.append((departure['line']['name'], departure['direction'], when_difference.seconds))
	   if len(formatted_departures) >= max_num_departures:
		break
		
	# print formatted_departures
	return formatted_departures
	
    def get_departures(self, stop_id, when=None, duration=10):
	if when is None:
	   when = datetime.datetime.now(tz = tz.tzlocal())
	   
        depature_data = self.req(
            'https://v5.bvg.transport.rest/stops/' +
            str(stop_id) + '/departures' +
            '?duration=' + str(duration) +
	    '&when=' + when.isoformat())
	return depature_data
            
    def get_stops(self, lat, lon):
        print 'fetching stops at ' + str(lat) + ', ' + str(lon)
        stop_data = self.req(
            'https://v5.bvg.transport.rest/stops/nearby' +
            '?latitude=' + str(lat) +
            '&longitude=' + str(lon))
        stop_ids = []
        for stop in stop_data[:4]:
            stop_ids.append(stop['id'])
        return stop_ids
            
    def get_location(self):
        print 'fetching current location...'
        location_data = self.req('http://ip-api.com/json?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query')
        return location_data['lat'], location_data['lon']

my_station = station()
departures = my_station.fetch()
print departures
