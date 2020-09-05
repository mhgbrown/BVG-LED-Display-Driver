# -*- coding: utf-8 -*-

# http://ip-api.com/json?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query
# https://v5.bvg.transport.rest/stops/nearby?latitude=52.52725&longitude=13.4123

import sys
import urllib
import json

class station:
    def req(self, url):
        jsonData = None
        try:
			connection = urllib.urlopen(url)
			raw = connection.read()
			connection.close()
			# TODO support ü, ß, etc.
			raw = raw.decode('utf8').encode('ascii', 'replace')
			jsonData = json.loads(raw)
        except:
			print "Something happened while making the request..."
			print sys.exc_info()
        finally:
			return jsonData
    
    def fetch(self):
        location = self.get_location()
        stop_ids = self.get_stops(location[0], location[1])
        return stop_ids
            
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
stop_ids = my_station.fetch()
print stop_ids
