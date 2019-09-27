import requests
import lxml.html as lh
import pandas as pd
import numpy as np
import csv
import sklearn as sk
import urllib.request
import os
import json

def updateSpaceTimeData():
	mountainNames = []
	mountainRoutes = []
	routeMileage = []
	elevGain = []
	routeTimes = []

	for i in range(182):
		if (i == 0):
			url = 'https://www.14ers.com/php14ers/timesmain.php'
		else:
			url = 'https://www.14ers.com/php14ers/timesmain.php?p=on&start=' + str(i*25)

		page = requests.get(url)
		doc = lh.fromstring(page.content)

		mountainRaw = doc.xpath('//table[@id="resultsTable"]/tr/td/span[@class="bold1"]/a')
		routeTimeRaw = doc.xpath('//table[@id="resultsTable"]/tr/td/span[@class="timeformat"]')
		miscRowRaw = doc.xpath('//table[@id="resultsTable"]/tr/td[@class="hide-8"]')

		for i in mountainRaw:
			mountainNames.append(i.text_content())

		for i in routeTimeRaw:
			hmsString = i.text_content()
			y, d, h, m, s = hmsString.split(':')
			routeTime = (int(y) * 31556952) + (int(d) * 86400) + (int(h) * 3600) + (int(m) * 60) + (int(s))
			routeTimes.append(routeTime)

		for i in range(len(miscRowRaw)):
			if (i + 1) % 5 == 1: 
				mrRaw = miscRowRaw[i].text_content()
				mrString = mrRaw[0 : (len(mrRaw)-1)]
				mountainRoutes.append(mrString)

			if (i + 1) % 5 == 3: 
				mrRaw = miscRowRaw[i].text_content()
				mrString = mrRaw[0 : (len(mrRaw)-1)]
				routeMileage.append(mrString)

			if (i + 1) % 5 == 4: 
				mrRaw = miscRowRaw[i].text_content()
				mrString = mrRaw[0 : (len(mrRaw)-1)]
				elevGain.append(mrString)

	routeDataArray = np.array([mountainNames, mountainRoutes, routeMileage, elevGain, routeTimes])
	routeDataDF = pd.DataFrame(routeDataArray.transpose(), columns = ['Mountain','Route','Mileage','Elevation','Route Time'])
	export_csv = routeDataDF.to_csv("data/RouteTimeData.csv", index = None, header = True)

def getRouteNames():
		routeNames = []

		url = "https://www.14ers.com/routes_byriskfactor.php"
		page = requests.get(url)
		doc = lh.fromstring(page.content)

		for riskTableNumber in range(5):
				riskTable = doc.xpath('//div[@id="tabs-1"]/table[@class="data_box2 rowhover alternaterowcolors1 routeList"]['+str(riskTableNumber+1)+']/tr/td/a')

				for i in riskTable:
					value = i.text_content().replace(', ','-')
					routeNames.append(value)

		return routeNames

def getRouteRiskFactors():
	url = "https://www.14ers.com/routes_byriskfactor.php"
	page = requests.get(url)
	doc = lh.fromstring(page.content)

	riskLevels = [1, 2, 3, 4, 5]
	riskFactors = ['Exposure', 'Stability', 'Routefind', 'Commitment']

	exposureDict = {}
	stabilityDict = {}
	routeDict = {}
	commitDict = {}

	def retreiveRisk(tabNum, riskDict):
		for riskTableNumber in range(len(riskLevels)):
			riskTable = doc.xpath('//div[@id="tabs-'+str(tabNum)+'"]/table[@class="data_box2 rowhover alternaterowcolors1 routeList"]['+str(riskTableNumber+1)+']/tr/td/a')

			for i in riskTable:
				value = i.text_content().replace(', ','-')
				riskDict.update({value : riskLevels[riskTableNumber]})

	retreiveRisk(1, exposureDict)
	retreiveRisk(2, stabilityDict)
	retreiveRisk(3, routeDict)
	retreiveRisk(4, commitDict)

	routeNames = getRouteNames()

	riskFactorsDict = {}

	for i in routeNames:
		routeRiskFactors = [exposureDict[i], stabilityDict[i], routeDict[i], commitDict[i]]
		routeRiskFactors.append(np.sum(routeRiskFactors))
		riskFactorsDict.update({i : routeRiskFactors})

	with open('data/riskByRoute.csv', 'w') as riskFile:
		for route in riskFactorsDict.keys():
			riskFile.write("%s,%s,%s,%s,%s,%s\n" % (route, riskFactorsDict[route][0], riskFactorsDict[route][1], riskFactorsDict[route][2], riskFactorsDict[route][3], riskFactorsDict[route][4]))

def cleanUpSpaceTime():
	#Data cleanup and setup
	routeDataDF = pd.read_csv('data/RouteTimeData.csv')
	dayHikeResult = routeDataDF.loc[(routeDataDF['Route Time'] < 86400)]
	dayHikeResult = dayHikeResult[~dayHikeResult['Mileage'].str.contains('-')]
	dayHikeResult = dayHikeResult[~dayHikeResult['Elevation'].str.contains('-')]
	dayHikeResult["mountainRoutes"] = dayHikeResult["Mountain"] + ": " + dayHikeResult["Route"]

	#TODO: Use Regex to capture more datapoints
	dayHikeResult["mountainRoutes"].replace(["Group: Democrat, Cameron, Lincoln, Bross: Standard Combo", "Group: Harvard, Columbia: Columbia to Harvard Traverse", "Group: Crestone Peak, Crestone Needle: Crestones Traverse", "Group: Evans, Sawtooth, Bierstadt: Bierstadt Sawtooth Evans"], ["Mt. Bross: Democrat-Cameron-Lincoln-Bross", "Mt. Harvard: Harvard and Columbia Traverse", "Crestone Peak: Crestones Traverse", "Mt. Bierstadt: Bierstadt-Sawtooth-Evans"], inplace = True)

	#Grouping results in preparation for master datasheet transfer
	dayHikeResult["Mileage"] = dayHikeResult["Mileage"].map(lambda x: x.rstrip(' mi')).map(lambda x: float(x))
	dayHikeResult["Elevation"] = dayHikeResult["Elevation"].map(lambda x: x.rstrip('\'')).map(lambda x: float(x))
	resultsByRoute = dayHikeResult.groupby(['mountainRoutes'])

	routeNames = getRouteNames()
	routeTimeDict = {}

	for routeName in routeNames:
		try:
			resultValues = resultsByRoute.get_group(routeName).mean()
			resultValuesArray = [resultValues[0], resultValues[1], resultValues[2]]
			routeTimeDict.update({routeName : resultValuesArray})

		except KeyError:
			routeTimeDict.update({routeName : [0, 0, 0]})

	with open('data/peakGeospatial.csv', 'w') as routeDataCSV:
		routeDataCSV.write("%s,%s,%s,%s,%s\n" % ('Route', 'Mountain', 'Mileage', 'Elevation', 'Time'))
		for route in routeTimeDict.keys():
			parentMountain = route.split(':')[0]
			routeDataCSV.write("%s,%s,%s,%s,%s\n" % (route, parentMountain, routeTimeDict[route][0], routeTimeDict[route][1], routeTimeDict[route][2]))

def getTrailheadDifficulty():
	url = "https://www.14ers.com/php14ers/trailheads_bydifficulty.php"
	page = requests.get(url)
	doc = lh.fromstring(page.content)

	diffRatings = [0, 1, 2, 3, 4, 5]
	trailHeadDict = {}

	for diffRating in diffRatings:
		trailHead = doc.xpath('//table[@class="resultsTable"][' + str(diffRating+1) + ']/tr/td[2]')
		trailHeadPeaks = doc.xpath('//table[@class="resultsTable"][' + str(diffRating+1) + ']/tr/td[3]')

		for i in range(len(trailHead)):
			parentPeaks = trailHeadPeaks[i].text_content().split(", ")

			for j in range(len(parentPeaks)):

				#TODO: somehow factor in the multiple trailheads per mountain, create composite score.
				#However, most difficult trailhead per mountain would be good, better more prepared than otherwise...

				#parentPeaks[j] = parentPeaks[j] + ": " + trailHead[i].text_content()
				#trailHeadDiff = trailHead[i].text_content() + "-" + str(diffRating)

				trailHeadDict.update({parentPeaks[j] : str(diffRating)})
	
	del trailHeadDict['']
	del trailHeadDict['Mt. Harvard,']

	with open('data/trailHeadDifficulty.csv', 'w') as trailHeadCSV:
		trailHeadCSV.write("%s,%s\n" % ("Mountain", "Accessibility"))
		for trailHead in trailHeadDict.keys():
			trailHeadCSV.write("%s,%s\n" % (trailHead, trailHeadDict[trailHead]))

def getTopo():
	topoArray = [ 'graystorreys', 'evansgroup', 'longspeak', 'quandarypeak', 'lincolngroup', 'mtsherman','maroongroup', 'pikespeak', 'mtelbert', 'harvardgroup', 'laplatapeak', 'mtantero', 'shavanogroup', 'mtprinceton', 'mtyale', 'belfordgroup', 'mtholycross', 'huronpeak', 'castlegroup', 'capitolpeak', 'snowmassmtn', 'uncompahgrepeak', 'wilsongroup', 'mtsneffels', 'handiespeak', 'redcloudgroup', 'wetterhornpeak', 'sanluispeak', 'blancagroup', 'crestonegroup', 'kitcarsongroup', 'culebrapeak', 'mtlindsey']
	
	for i in topoArray:
		topoURL = "https://14ers.com/photos/" + i + "/bigtopo.jpg"
		urllib.request.urlretrieve(topoURL, "data/topoMaps/" + i +".jpg")

def getDistance():
	peakGPS = pd.read_csv('data/peakGPS.csv')
	latCoords = peakGPS.values[: , 1]
	longCoords = peakGPS.values[: , 2]

	baseRequest = "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial"

	#USAFA Visitor Center Cadet Parking Area
	originPoint = "&origins=39.007085,-104.896722"

	destString = "&destinations="

	for i in range(len(peakGPS)):
	# 	mtnCoord = [longCoords[i],latCoords[i]]
	# 	mtnCoords.append(mtnCoord)
		if i != 0:
			destString = destString + '|' + str(longCoords[i]) + ',' + str(latCoords[i])
		else: 
			destString = destString + str(longCoords[i]) + ',' + str(latCoords[i])

	apiKey = "&key=AIzaSyCrMWKfqCfy9ANE4eYARxDEWQb066qzAVo"

	distanceMatrixRequest = baseRequest + originPoint + destString + apiKey

	call = requests.post(distanceMatrixRequest)

	callPython = json.loads(call.text)


def processJSON():
	peakGPS = pd.read_csv('data/peakGPS.csv')

	jsonDict = {
		"destination_addresses" : [
	      "Pikes Peak Toll Rd, Cascade, CO 80809, USA",
	      "825 Longs Peak Rd, Estes Park, CO 80517, USA",
	      "16 Mount Evans Hwy, Idaho Springs, CO 80452, USA",
	      "Bierstadt Trail, Idaho Springs, CO 80452, USA",
	      "Continental Divide Trail, Dillon, CO 80435, USA",
	      "Torreys Peak Trail, Dillon, CO 80435, USA",
	      "Aspen, CO 81611, USA",
	      "Aspen, CO 81611, USA",
	      "Aspen, CO 81611, USA",
	      "Aspen, CO 81611, USA",
	      "9998 Co Rd 9, Snowmass, CO 81654, USA",
	      "Unnamed Road, Carbondale, CO 81623, USA",
	      "Aspen, CO 81611, USA",
	      "Blue Lakes Rd, Breckenridge, CO 80424, USA",
	      "Co Rd 8, Leadville, CO 80461, USA",
	      "Crest Dr, Breckenridge, CO 80424, USA",
	      "Crest Dr, Breckenridge, CO 80424, USA",
	      "Blue River, CO 80424, USA",
	      "Co Rte 2B, Leadville, CO 80461, USA",
	      "Westcliffe, CO 81252, USA",
	      "Westcliffe, CO 81252, USA",
	      "Co Rd 120, Westcliffe, CO 81252, USA",
	      "Westcliffe, CO 81252, USA",
	      "Westcliffe, CO 81252, USA",
	      "Gardner, CO 81040, USA",
	      "Gardner, CO 81040, USA",
	      "SAND DUNES MO, CO 81101, USA",
	      "Gardner, CO 81040, USA",
	      "Weston, CO 81091, USA",
	      "Notch Mountain Rd, Minturn, CO 81645, USA",
	      "Mt. Massive Trail, Leadville, CO 80461, USA",
	      "Black Cloud Trail, Buena Vista, CO 81211, USA",
	      "La Plata Peak Trail, Buena Vista, CO 81211, USA",
	      "Buena Vista, CO 81211, USA",
	      "Continental Divide Trail, Buena Vista, CO 81211, USA",
	      "Buena Vista, CO 81211, USA",
	      "Buena Vista, CO 81211, USA",
	      "Continental Divide Trail, Buena Vista, CO 81211, USA",
	      "Buena Vista, CO 81211, USA",
	      "Buena Vista, CO 81211, USA",
	      "Nathrop, CO 81236, USA",
	      "Salida, CO 81201, USA",
	      "Salida, CO 81201, USA",
	      "Nathrop, CO 81236, USA",
	      "Blue Lakes Trail, Colorado, USA",
	      "Lake City, CO 81235, USA",
	      "Lake City, CO 81235, USA",
	      "Unnamed Road, Lake City, CO 81235, USA",
	      "Lake City, CO 81235, USA",
	      "Unnamed Road, Lake City, CO 81235, USA",
	      "Dolores, CO 81323, USA",
	      "Telluride, CO 81435, USA",
	      "Dolores, CO 81323, USA",
	      "Forest Rd 682, Durango, CO 81301, USA",
	      "Forest Rd 682, Durango, CO 81301, USA",
	      "Forest Rd 682, Durango, CO 81301, USA",
	      "Forest Rd 682, Durango, CO 81301, USA",
	      "County Rd 14 DD, Colorado, USA"
	   ],
	   "origin_addresses" : [ "2346 Academy Dr, U.S. Air Force Academy, CO 80840, USA" ],
	   "rows" : [
	      {
	         "elements" : [
	            {
	               "distance" : {
	                  "text" : "48.0 mi",
	                  "value" : 77198
	               },
	               "duration" : {
	                  "text" : "1 hour 25 mins",
	                  "value" : 5107
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "129 mi",
	                  "value" : 207090
	               },
	               "duration" : {
	                  "text" : "2 hours 27 mins",
	                  "value" : 8797
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "116 mi",
	                  "value" : 187126
	               },
	               "duration" : {
	                  "text" : "2 hours 29 mins",
	                  "value" : 8928
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "116 mi",
	                  "value" : 186874
	               },
	               "duration" : {
	                  "text" : "2 hours 28 mins",
	                  "value" : 8873
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "136 mi",
	                  "value" : 218607
	               },
	               "duration" : {
	                  "text" : "2 hours 50 mins",
	                  "value" : 10192
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "110 mi",
	                  "value" : 177728
	               },
	               "duration" : {
	                  "text" : "2 hours 5 mins",
	                  "value" : 7492
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "190 mi",
	                  "value" : 305308
	               },
	               "duration" : {
	                  "text" : "4 hours 10 mins",
	                  "value" : 15024
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "189 mi",
	                  "value" : 304569
	               },
	               "duration" : {
	                  "text" : "4 hours 9 mins",
	                  "value" : 14956
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "185 mi",
	                  "value" : 297453
	               },
	               "duration" : {
	                  "text" : "3 hours 58 mins",
	                  "value" : 14273
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "185 mi",
	                  "value" : 297453
	               },
	               "duration" : {
	                  "text" : "3 hours 58 mins",
	                  "value" : 14273
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "198 mi",
	                  "value" : 319318
	               },
	               "duration" : {
	                  "text" : "4 hours 19 mins",
	                  "value" : 15525
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "261 mi",
	                  "value" : 420329
	               },
	               "duration" : {
	                  "text" : "4 hours 53 mins",
	                  "value" : 17598
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "185 mi",
	                  "value" : 297420
	               },
	               "duration" : {
	                  "text" : "3 hours 58 mins",
	                  "value" : 14275
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "117 mi",
	                  "value" : 188599
	               },
	               "duration" : {
	                  "text" : "2 hours 22 mins",
	                  "value" : 8514
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "113 mi",
	                  "value" : 181259
	               },
	               "duration" : {
	                  "text" : "2 hours 22 mins",
	                  "value" : 8493
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "116 mi",
	                  "value" : 187246
	               },
	               "duration" : {
	                  "text" : "2 hours 30 mins",
	                  "value" : 8979
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "115 mi",
	                  "value" : 185701
	               },
	               "duration" : {
	                  "text" : "2 hours 26 mins",
	                  "value" : 8749
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "116 mi",
	                  "value" : 185960
	               },
	               "duration" : {
	                  "text" : "2 hours 26 mins",
	                  "value" : 8787
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "165 mi",
	                  "value" : 265245
	               },
	               "duration" : {
	                  "text" : "3 hours 9 mins",
	                  "value" : 11340
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "114 mi",
	                  "value" : 182781
	               },
	               "duration" : {
	                  "text" : "2 hours 45 mins",
	                  "value" : 9877
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "114 mi",
	                  "value" : 182781
	               },
	               "duration" : {
	                  "text" : "2 hours 45 mins",
	                  "value" : 9877
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "113 mi",
	                  "value" : 181249
	               },
	               "duration" : {
	                  "text" : "2 hours 42 mins",
	                  "value" : 9739
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "114 mi",
	                  "value" : 182781
	               },
	               "duration" : {
	                  "text" : "2 hours 45 mins",
	                  "value" : 9877
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "180 mi",
	                  "value" : 290211
	               },
	               "duration" : {
	                  "text" : "3 hours 32 mins",
	                  "value" : 12745
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "161 mi",
	                  "value" : 258672
	               },
	               "duration" : {
	                  "text" : "2 hours 45 mins",
	                  "value" : 9894
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "161 mi",
	                  "value" : 258672
	               },
	               "duration" : {
	                  "text" : "2 hours 45 mins",
	                  "value" : 9894
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "177 mi",
	                  "value" : 285441
	               },
	               "duration" : {
	                  "text" : "3 hours 23 mins",
	                  "value" : 12186
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "161 mi",
	                  "value" : 258672
	               },
	               "duration" : {
	                  "text" : "2 hours 45 mins",
	                  "value" : 9894
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "194 mi",
	                  "value" : 311751
	               },
	               "duration" : {
	                  "text" : "3 hours 29 mins",
	                  "value" : 12533
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "171 mi",
	                  "value" : 274963
	               },
	               "duration" : {
	                  "text" : "3 hours 19 mins",
	                  "value" : 11952
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "152 mi",
	                  "value" : 245380
	               },
	               "duration" : {
	                  "text" : "3 hours 20 mins",
	                  "value" : 11990
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "154 mi",
	                  "value" : 247807
	               },
	               "duration" : {
	                  "text" : "3 hours 29 mins",
	                  "value" : 12536
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "147 mi",
	                  "value" : 235875
	               },
	               "duration" : {
	                  "text" : "2 hours 52 mins",
	                  "value" : 10331
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "139 mi",
	                  "value" : 223596
	               },
	               "duration" : {
	                  "text" : "3 hours 2 mins",
	                  "value" : 10903
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "136 mi",
	                  "value" : 218831
	               },
	               "duration" : {
	                  "text" : "2 hours 48 mins",
	                  "value" : 10102
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "134 mi",
	                  "value" : 215034
	               },
	               "duration" : {
	                  "text" : "2 hours 40 mins",
	                  "value" : 9614
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "132 mi",
	                  "value" : 212757
	               },
	               "duration" : {
	                  "text" : "2 hours 37 mins",
	                  "value" : 9406
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "136 mi",
	                  "value" : 218831
	               },
	               "duration" : {
	                  "text" : "2 hours 48 mins",
	                  "value" : 10102
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "120 mi",
	                  "value" : 193380
	               },
	               "duration" : {
	                  "text" : "2 hours 34 mins",
	                  "value" : 9214
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "123 mi",
	                  "value" : 197458
	               },
	               "duration" : {
	                  "text" : "2 hours 25 mins",
	                  "value" : 8674
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "123 mi",
	                  "value" : 198528
	               },
	               "duration" : {
	                  "text" : "2 hours 59 mins",
	                  "value" : 10713
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "142 mi",
	                  "value" : 229206
	               },
	               "duration" : {
	                  "text" : "2 hours 47 mins",
	                  "value" : 10018
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "143 mi",
	                  "value" : 230734
	               },
	               "duration" : {
	                  "text" : "2 hours 50 mins",
	                  "value" : 10194
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "132 mi",
	                  "value" : 212968
	               },
	               "duration" : {
	                  "text" : "2 hours 52 mins",
	                  "value" : 10329
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "300 mi",
	                  "value" : 482405
	               },
	               "duration" : {
	                  "text" : "6 hours 12 mins",
	                  "value" : 22330
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "253 mi",
	                  "value" : 407234
	               },
	               "duration" : {
	                  "text" : "5 hours 17 mins",
	                  "value" : 19002
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "256 mi",
	                  "value" : 412335
	               },
	               "duration" : {
	                  "text" : "5 hours 38 mins",
	                  "value" : 20304
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "330 mi",
	                  "value" : 531410
	               },
	               "duration" : {
	                  "text" : "7 hours 19 mins",
	                  "value" : 26345
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "261 mi",
	                  "value" : 419873
	               },
	               "duration" : {
	                  "text" : "5 hours 18 mins",
	                  "value" : 19100
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "263 mi",
	                  "value" : 422822
	               },
	               "duration" : {
	                  "text" : "5 hours 25 mins",
	                  "value" : 19494
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "317 mi",
	                  "value" : 510288
	               },
	               "duration" : {
	                  "text" : "6 hours 13 mins",
	                  "value" : 22407
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "317 mi",
	                  "value" : 510279
	               },
	               "duration" : {
	                  "text" : "6 hours 13 mins",
	                  "value" : 22405
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "317 mi",
	                  "value" : 510296
	               },
	               "duration" : {
	                  "text" : "6 hours 13 mins",
	                  "value" : 22408
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "374 mi",
	                  "value" : 602410
	               },
	               "duration" : {
	                  "text" : "7 hours 45 mins",
	                  "value" : 27893
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "374 mi",
	                  "value" : 602410
	               },
	               "duration" : {
	                  "text" : "7 hours 45 mins",
	                  "value" : 27893
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "374 mi",
	                  "value" : 602410
	               },
	               "duration" : {
	                  "text" : "7 hours 45 mins",
	                  "value" : 27893
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "374 mi",
	                  "value" : 602410
	               },
	               "duration" : {
	                  "text" : "7 hours 45 mins",
	                  "value" : 27893
	               },
	               "status" : "OK"
	            },
	            {
	               "distance" : {
	                  "text" : "235 mi",
	                  "value" : 377967
	               },
	               "duration" : {
	                  "text" : "5 hours 7 mins",
	                  "value" : 18414
	               },
	               "status" : "OK"
	            }
	         ]
	      }
	   ],
	   "status" : "OK"
	}

	mountainNames = peakGPS['Mountain']
	drivingDistArray = []
	drivingTimeArray = []

	for i in range(58):
		try:
			drivingTimeArray.append(jsonDict['rows'][0]['elements'][i]['duration']['value'])
			drivingDistArray.append(float(jsonDict['rows'][0]['elements'][i]['distance']['text'].rstrip(' mi')))
		except:
			drivingTimeArray.append(0)
			drivingDistArray.append(0)

	mountainDriving = pd.DataFrame({'Mountain' : peakGPS['Mountain'], 'Driving Mileage' : drivingDistArray, 'Driving Time' : drivingTimeArray})
	return mountainDriving

def mergePeakData():
	peakGeospatialDF = pd.read_csv('data/peakGeospatial.csv')
	peakUsageDF = pd.read_csv('data/peakUsage.csv')
	peakRiskDF = pd.read_csv('data/riskByRoute.csv')
	peakTrailHeadDF = pd.read_csv('data/trailHeadDifficulty.csv')
	peakGPS = pd.read_csv('data/peakGPS.csv')
	peakRangeElev = pd.read_csv('data/peakRangeElev.csv')
	drivingInfo = processJSON()

	peakData = pd.merge(peakGeospatialDF, peakUsageDF, on = 'Mountain')
	peakData = pd.merge(peakData, peakRangeElev, on = 'Mountain')
	peakData = pd.merge(peakData, peakTrailHeadDF, on ='Mountain')
	peakData = pd.merge(peakData, peakGPS, on ='Mountain')
	peakData = pd.merge(peakData, drivingInfo, on = 'Mountain')
	peakData = pd.merge(peakData, peakRiskDF, on ='Route')

	peakData = peakData.loc[~(peakData['Mileage']==0)]

	#Correcting a weird data reading on the mileage of Maroon Traverse here
	peakData.set_value(130, 'Mileage', 9.5)

	peakData['riskQuotient'] = (peakData['TotalRisk'] / 20)
	peakData['populationQuotient'] = peakData['Users'] / peakData['Users'].max()
	peakData['geospatialQuotient'] = ((peakData['Mileage'] / peakData['Mileage'].max()) + (peakData['Elevation'] / peakData['Elevation'].max()) + (peakData['Time'] / peakData['Time'].max()))
	peakData['geospatialQuotient'] = peakData['geospatialQuotient'] / peakData['geospatialQuotient'].max()
	peakData['accessibilityQuotient'] = (peakData['Accessibility'] + 1) / 6
	peakData['travelQuotient'] = peakData['Driving Time'] / peakData['Driving Time'].max()
	peakData['route_id'] = np.array(range(119))

	peakData.to_csv('data/masterPeakData.csv')

def totalUpdate():
	print("Retreiving updated travel and route travel data...")
	updateSpaceTimeData()

	print("Cleaning up route travel and geospatial data...")
	cleanUpSpaceTime()

	print("Retreiving route risk factor information...")
	getRouteRiskFactors()

	print("Retreiving route accessibility information...")
	getTrailheadDifficulty()

	print("Merging collected data...")
	mergePeakData()

	print("Update complete!")

mergePeakData()