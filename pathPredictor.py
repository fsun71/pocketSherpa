import requests
import pandas as pd
import csv
import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d

def getXYZData():
	upperLeftCornerLat = 39.67
	upperLeftCornerLong = -105.825
	bottomRightCornerLat = 39.63
	bottomRightCornerLong = -105.785

	latRange = abs(upperLeftCornerLat - bottomRightCornerLat)
	longRange = abs(upperLeftCornerLong - bottomRightCornerLong)

	resolution = 25
	latRes = latRange / resolution
	longRes = longRange / resolution

	latArray = []
	longArray = []
	xyArray = []
	xyzArray = []

	for i in range(resolution):
		increment = i * latRes
		latArray.append(np.round(bottomRightCornerLat + increment, 4))

	for i in range(resolution):
		increment = i * longRes
		longArray.append(np.round(upperLeftCornerLong + increment, 4))

	for latitude in latArray:
		for longitude in longArray:
			xyArray.append([latitude, longitude])

	apiKey = "&key=AIzaSyCrMWKfqCfy9ANE4eYARxDEWQb066qzAVo"

	for coordinate in xyArray:
		lattitude = coordinate[0]
		longitude = coordinate[1]

		elevation = 0

		elevationRequestUrl = 'https://maps.googleapis.com/maps/api/elevation/json?locations=' + str(lattitude) + ',' + str(longitude) + apiKey
		call = requests.post(elevationRequestUrl)
		elevationRequestResult = json.loads(call.text)

		elevation = elevationRequestResult['results'][0]['elevation']

		xyzArray.append([coordinate[0], coordinate[1], elevation])

	xyzDF = pd.DataFrame(xyzArray, columns = ['lattitude', 'longitude', 'elevation'])
	xyzCSV = xyzDF.to_csv('data/graystorreysXYZ.csv')

def processData():
	xyzDF = pd.read_csv('data/graystorreysXYZ.csv')
	xyzDF['elevationFt'] = np.round(xyzDF['elevation'] * 3.28084, 6)

	xDataArray = []
	yDataArray = []
	zDataArray = []

	for i in range(25):
		tempContainerX = []
		tempContainerY = []
		tempContainerZ = []
		for j in range(25):
			tempContainerX.append(xyzDF['longitude'][(i*25)+j])
			tempContainerY.append(xyzDF['lattitude'][(i*25)+j])
			tempContainerZ.append(xyzDF['elevationFt'][(i*25)+j])

		xDataArray.append(tempContainerX)
		yDataArray.append(tempContainerY)
		zDataArray.append(tempContainerZ)

	X, Y, Z = np.array(xDataArray), np.array(yDataArray), np.array(zDataArray)
	
	fig = plt.figure()
	ax = plt.axes(projection = '3d')

	ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap='viridis', edgecolor='none')
	x_range = [xyzDF['longitude'].min(), xyzDF['longitude'].max()]
	y_range = [xyzDF['lattitude'].min(), xyzDF['lattitude'].max()]

	# plt.xlim(x_range)
	# plt.ylim(y_range)

	plt.show()

processData()