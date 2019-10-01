import requests
import pandas as pd
import csv
import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d

resolution = 50

def getXYZData():
	# upperLeftCornerLat = 39.67
	# upperLeftCornerLong = -105.825
	# bottomRightCornerLat = 39.61
	# bottomRightCornerLong = -105.775

	upperLeftCornerLat = 39.645
	upperLeftCornerLong = -105.834
	bottomRightCornerLat = 39.63
	bottomRightCornerLong = -105.8

	latRange = abs(upperLeftCornerLat - bottomRightCornerLat)
	longRange = abs(upperLeftCornerLong - bottomRightCornerLong)

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

xyzDF = pd.read_csv('data/graystorreysXYZ.csv')

def processData():
	xyzDF['elevationFt'] = np.round(xyzDF['elevation'] * 3.28084, 6)

	xDataArray = []
	yDataArray = []
	zDataArray = []

	for i in range(resolution):
		tempContainerX = []
		tempContainerY = []
		tempContainerZ = []
		for j in range(resolution):
			tempContainerX.append(xyzDF['longitude'][(i*resolution)+j])
			tempContainerY.append(xyzDF['lattitude'][(i*resolution)+j])
			tempContainerZ.append(xyzDF['elevationFt'][(i*resolution)+j])

		xDataArray.append(tempContainerX)
		yDataArray.append(tempContainerY)
		zDataArray.append(tempContainerZ)

	X, Y, Z = np.array(xDataArray), np.array(yDataArray), np.array(zDataArray)
	
	fig = plt.figure()
	ax = plt.axes(projection = '3d')

	ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap='terrain', edgecolor='none')
	x_range = [xyzDF['longitude'].min(), xyzDF['longitude'].max()]
	y_range = [xyzDF['lattitude'].min(), xyzDF['lattitude'].max()]

	# plt.xlim(x_range)
	# plt.ylim(y_range)

	plt.title('Grays and Torreys 3D Topographic Map')
	ax.set_xlabel('Degrees longitude')
	ax.set_ylabel('Degrees lattitude')
	ax.set_zlabel('Elevation ASL (feet)')
	plt.show()

def generateNodeElevationDict():
	elevationArray = np.array(xyzDF['elevation'])

	nodeElevationValuesDict = {}

	for i in range(2500):
		nodeElevationValuesDict.update({i+1 : elevationArray[i]})

	return nodeElevationValuesDict

def nodeGraphGeneration(resolution):
	nodeMatrix = []

	nodeElevationDict = generateNodeElevationDict()

	for i in range(resolution):
		nodeRow = []
		for j in range(resolution):
			nodeRow.append(i*resolution + (j+1))
		nodeMatrix.append(nodeRow)


	boundedNodeMatrix =  [np.zeros(resolution + 2, dtype = int)]

	for i in nodeMatrix:
		i = np.insert(i, 0, 0)
		i = np.insert(i, resolution + 1, 0)
		boundedNodeMatrix.append(i)

	boundedNodeMatrix.append(np.zeros(resolution + 2, dtype = int))
	adjacentNodeDict = {}

	for row in range(1, resolution+1):
		for column in range(1, resolution+1):
			adjacentNodeMatrix = [boundedNodeMatrix[row-1][column], boundedNodeMatrix[row-1][column+1], boundedNodeMatrix[row][column+1], boundedNodeMatrix[row+1][column+1], boundedNodeMatrix[row+1][column], boundedNodeMatrix[row+1][column-1], boundedNodeMatrix[row][column-1], boundedNodeMatrix[row-1][column-1]]
			adjacentNodeMatrix = np.sort(adjacentNodeMatrix, kind = 'mergesort')
			adjacentNodeMatrix = np.trim_zeros(adjacentNodeMatrix)



			adjacentNodeDistanceDict = {}

			for i in adjacentNodeMatrix:
				adjacentNodeElevation = nodeElevationDict[i]
				currentNodeElevation = nodeElevationDict[boundedNodeMatrix[row][column]]
				adjacentNodeDistanceDict.update({i : (adjacentNodeElevation - currentNodeElevation + 180)})

			adjacentNodeDict.update({boundedNodeMatrix[row][column] : adjacentNodeDistanceDict})

	nodeGraph = adjacentNodeDict
	return nodeGraph

def dijkstra(graph, srcIndex, destIndex):
	inf = float('inf')
	source = (srcIndex + 1)
	dest =  destIndex + 1

	visitedNodes = {}
	unvisitedNodes = {}

	nodes = np.array(range(1, resolution**2 +1))
	for node in nodes:
		defaultDist = inf
		if node == source:
			defaultDist = 0
		unvisitedNodes.update({node : defaultDist})

	currentNode = source
	currentDistance = 0

	while True:
	    for neighbour, distance in graph[currentNode].items():
	        if neighbour not in unvisitedNodes: continue
	        newDistance = currentDistance + distance
	        if unvisitedNodes[neighbour] is None or unvisitedNodes[neighbour] > newDistance:
	            unvisitedNodes[neighbour] = newDistance
	    visitedNodes[currentNode] = currentDistance
	    del unvisitedNodes[currentNode]
	    if not unvisitedNodes: break
	    candidates = [node for node in unvisitedNodes.items() if node[1]]
	    currentNode, currentDistance = sorted(candidates, key = lambda x: x[1])[0]		
	    if currentNode == destIndex:
	    	break

	print(visitedNodes[dest])

# Used to get the 180 figure in the nodeGraphGeneration function
# function now deprecated
# def getMostNegative():
# 	distMatrix = nodeGraphGeneration(resolution)

# 	minKeys = []
# 	for i in range(1, 2501):
# 		tempContainer = []
# 		for j in distMatrix[i].values():
# 			tempContainer.append(j)
# 		minKeys.append(min(tempContainer))
	
# 	mostNegative = min(np.round(minKeys, -1))

# 	return -1 * mostNegative

dijkstra(nodeGraphGeneration(resolution), 2437, xyzDF['elevation'].idxmax())
