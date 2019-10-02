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
	plotOptimalRoute(2437, xyzDF['elevation'].idxmax())
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
				adjacentNodeDistanceDict.update({i : (adjacentNodeElevation - currentNodeElevation + 200)})

			adjacentNodeDict.update({boundedNodeMatrix[row][column] : adjacentNodeDistanceDict})

	nodeMap = adjacentNodeDict
	return nodeMap

def dijkstra(nodeMap, srcIndex, destIndex):
	inf = float('inf')
	source = (srcIndex + 1)
	dest =  destIndex + 1

	#Establishes starting node and its respective distance value, establishes visited and unvisited node dictionary containers
	visitedNodeMap = {}
	unvisitedNodeMap = {}
	currentDistance = 0
	currentNode = source

	#Establishes storage container for list of nodes that came before the current node, used to determine waypoints of shortest path
	prevNodes = {}

	#Distance/cost map for every node, everything gets infinite distance except the starting node, which gets a value of zero
	#Also creates map of every node's most efficient previous iteration, allowing for paths to be known
	nodes = np.array(range(1, resolution**2 +1))
	for node in nodes:
		defaultDist = inf
		prevNode = None

		if node == source:
			defaultDist = currentDistance

		unvisitedNodeMap.update({node : defaultDist})
		prevNodes.update({node : prevNode})


	while True:
	    for adjacentNode, nodeDistance in nodeMap[currentNode].items():
	    	#Do not investigate the adjacent node if it has already been visited
	        if adjacentNode in visitedNodeMap:
	        	continue
	        #Finds tentative shortest distance to currentNode from origin by summing the current distance up to the node, and the distance to the node itself
	        tentativeDistance = currentDistance + nodeDistance

	        #If the calculated tentative distance to an adjacent node is less than the currently given minimum on the unvisited node map, set the calculated tentative distance as the new minimum
	        #Also set the most efficient previous node on the prevNodes node map
	        if tentativeDistance < unvisitedNodeMap[adjacentNode]:
	            unvisitedNodeMap[adjacentNode] = tentativeDistance
	            prevNodes[adjacentNode] = currentNode

	    #Once the minimum adjacent node to the current node is found, set the minimum adjacent node as the new current node and move the previous current node to the visited dictionary (never to be checked again)
	    visitedNodeMap[currentNode] = currentDistance
	    del unvisitedNodeMap[currentNode]


	    #Break once minimum distance is calculated and stored (see above two lines) for the destination node
	    if currentNode == destIndex:
	    	break

	    #Set list of nodes with non-infinite distances
	    feasibleNodes = []
	    for node in unvisitedNodeMap.items():
	    	if node[1] != inf:
	    		feasibleNodes.append(node)

	    #Find node in entire feasible region with lowest cost/distance value (sort dictionary by ascending value, choose key of first entry)
	    newCurrentNode, currentDistance = sorted(feasibleNodes, key = lambda x: x[1])[0]	

	    #New current node set
	    currentNode = newCurrentNode

	#Generates shortest path to the destination from the source
	currentNode = dest
	pathToDest = [currentNode]

	while True:
		#Stop when we get to the source
		if prevNodes[currentNode] == None:
			break
		#Appends the node prior to the current one being examined to the path array
		pathToDest.append(prevNodes[currentNode])
		#Sets new current node as the 'previous node' in the line above, working our way back the chain
		currentNode = prevNodes[currentNode]

	return pathToDest

def plotOptimalRoute(origin, destination):
	pathToDest = dijkstra(nodeGraphGeneration(resolution), origin, destination)

	lattitudePathArray = []
	longitudePathArray = [] 
	elevationPathArray = []

	for i in pathToDest:
		lattitudePathArray.append(xyzDF.iloc[i-1]['lattitude'])
		longitudePathArray.append(xyzDF.iloc[i-1]['longitude'])
		elevationPathArray.append(xyzDF.iloc[i-1]['elevationFt'])

	X, Y, Z = longitudePathArray, lattitudePathArray, elevationPathArray
	
	fig = plt.figure()
	ax = plt.axes(projection = '3d')

	ax.scatter(X, Y, Z, alpha = 0)

	line = mplot3d.art3d.Line3D(longitudePathArray, lattitudePathArray, elevationPathArray)
	return ax.add_line(line)
	#return ax.scatter(X, Y, Z)

processData()


#plotOptimalRoute(2437, xyzDF['elevation'].idxmax())