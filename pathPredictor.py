import requests
import pandas as pd
import csv
import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
import topoMapReader as tMap

resolution = 50
name = ''
mapName = ''

def getXYZData(upperLeftCornerLat, upperLeftCornerLong, bottomRightCornerLat, bottomRightCornerLong):

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
	xyzCSV = xyzDF.to_csv('data/' + name + 'XYZ.csv')

def generateNodeElevationDict():

	elevationArray = np.array(xyzDF['elevation'])

	nodeElevationValuesDict = {}

	for i in range(resolution**2):
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

				adjacentNodeDistanceDict.update({i : ((adjacentNodeElevation - currentNodeElevation) / currentNodeElevation)**2})

			adjacentNodeDict.update({boundedNodeMatrix[row][column] : adjacentNodeDistanceDict})

	nodeMap = adjacentNodeDict
	return nodeMap

def generateNodeElevationDictNew():
	elevData, regionLatRange, regionLongRange = tMap.readGeoData(mapName = 'n41w106', NWCorner = [40.286528, -105.635828], SECorner = [40.228733, -105.568827])
	numRows, numCols = elevData.shape

	elevDataFlat = elevData.flatten()
	numDataPoints = len(elevDataFlat)

	nodeElevationDict = {}

	for i in range(numDataPoints):
		nodeElevationDict.update({i+1 : elevDataFlat[i]})

	return nodeElevationDict, numRows, numCols

def nodeGraphGenerationNew():
	nodeMatrix = []
	adjacentNodeDict = {}

	nodeElevationDict, numRows, numCols = generateNodeElevationDictNew()

	#Creates 2D Matrix of node ids, the shape of which is determined by the number size of the user selected region
	for i in range(numRows):
		nodeRow = []
		for j in range(numCols):
			nodeRow.append(i*numCols + (j+1))
		nodeMatrix.append(nodeRow)

	#Adds zero array first row
	boundedNodeMatrix = [np.zeros(numCols + 2, dtype = int)]

	#Adds zeros on either end of each row, and appends them to boundedNodeMatrix
	for i in nodeMatrix:
		i = np.insert(i, 0, 0)
		i = np.insert(i, numCols + 1, 0)
		boundedNodeMatrix.append(i)
	#Adds zero array for last row
	boundedNodeMatrix.append(np.zeros(numCols + 2, dtype = int))

	#Iterates through each cell in the table
	for row in range(1, numRows+1):
		for column in range(1, numCols+1):
			#Adjacent nodes to a current node are discovered (eight nodes surrounding the current node, similar to the 5 on a standard keyboard numPad)
			adjacentNodeMatrix = [boundedNodeMatrix[row-1][column], boundedNodeMatrix[row-1][column+1], boundedNodeMatrix[row][column+1], boundedNodeMatrix[row+1][column+1], boundedNodeMatrix[row+1][column], boundedNodeMatrix[row+1][column-1], boundedNodeMatrix[row][column-1], boundedNodeMatrix[row-1][column-1]]
			adjacentNodeMatrix = np.sort(adjacentNodeMatrix, kind = 'mergesort')
			adjacentNodeMatrix = np.trim_zeros(adjacentNodeMatrix)

			#Dictionary containing respective distances
			adjacentNodeDistanceDict = {}

			#Stores distances of each node to their eight neighbors in a dictionary
			for i in adjacentNodeMatrix:
				adjacentNodeElevation = nodeElevationDict[i]
				currentNodeElevation = nodeElevationDict[boundedNodeMatrix[row][column]]

				#Distance modified to account for human energy conserving behavior
				adjacentNodeDistanceDict.update({i : ((adjacentNodeElevation - currentNodeElevation) / currentNodeElevation)**2})

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

	longitudePathArray = [] 
	lattitudePathArray = []
	elevationPathArray = []

	for i in pathToDest:
		longitudePathArray.append(xyzDF.iloc[i-1]['longitude'])
		lattitudePathArray.append(xyzDF.iloc[i-1]['lattitude'])
		elevationPathArray.append(xyzDF.iloc[i-1]['elevationFt'])

	originDestX = [xyzDF.iloc[origin]['longitude'], xyzDF.iloc[destination]['longitude']]
	originDestY = [xyzDF.iloc[origin]['lattitude'], xyzDF.iloc[destination]['lattitude']]
	originDestZ = [xyzDF.iloc[origin]['elevationFt'], xyzDF.iloc[destination]['elevationFt']]

	X, Y, Z = longitudePathArray, lattitudePathArray, elevationPathArray
	return [X, Y, Z, originDestX, originDestY, originDestZ]

def renderVisualData():
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

	pathXYZ = plotOptimalRoute(2144, xyzDF['elevation'].idxmax())

	pathX = pathXYZ[0]
	pathY = pathXYZ[1]
	pathZ = pathXYZ[2]

	originDestX = pathXYZ[3]
	originDestY = pathXYZ[4]
	originDestZ = pathXYZ[5]

	ax.scatter(pathX, pathY, pathZ, alpha = 0)

	line = mplot3d.art3d.Line3D(pathX, pathY, pathZ, color = 'red', linewidth = 4)
	ax.add_line(line)

	surfacePlot = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap='terrain', edgecolor='none', alpha = 0.5)
	ax.scatter(originDestX, originDestY, originDestZ, color = 'red', s = 100, alpha = 1, marker = '^')
	x_range = [xyzDF['longitude'].min(), xyzDF['longitude'].max()]
	y_range = [xyzDF['lattitude'].min(), xyzDF['lattitude'].max()]

	fig.colorbar(surfacePlot, shrink = 0.4, aspect = 10)
	plt.title(mapName + ' 3D Topographic Map')
	ax.set_xlabel('Degrees longitude')
	ax.set_ylabel('Degrees lattitude')
	ax.set_zlabel('Elevation ASL (feet)')
	plt.show()

# if __name__ == '__main__':
# 	name = 'graystorreys'
# 	mapName = 'Grays and Torreys'
# 	#coordinates = []
# 	#getXYZData(*coordinates)
# 	xyzDF = pd.read_csv('data/' + name + 'XYZ.csv')
# 	renderVisualData()