import requests
import pandas as pd
import csv
import json
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
import topoMapReader as tMap
import gpxConverter as gpx

name = ''
mapName = ''
XYCoordDict = {}
nodeElevationDict = {}

def generateNodeElevationDict():
	global regionHighPt
	global regionLowPt
	global trailHeadPt
	global peakPt

	NWCorner = [39.665, -105.825]
	SECorner = [39.630, -105.78]

	tHeadCoords = [39.660825, -105.784673]
	peakCoords = []

	#Last point in nodeElevationDict
	NECorner = [NWCorner[0], SECorner[1]]
	#First point in nodeElevationDict
	SWCorner = [SECorner[0], NWCorner[1]]

	elevData, regionLatRange, regionLongRange = tMap.readGeoData(mapName = 'n40w106', NWCorner = NWCorner, SECorner = SECorner)
	numRows, numCols = elevData.shape

	elevDataFlat = elevData.flatten()
	numDataPoints = len(elevDataFlat)

	#Sets a corresponding lattitude/longitude pair for each node value 
	for i in range(numRows):
		latIncrement = ((NECorner[0] - SWCorner[0])/numRows) * i
		latComponent = np.round(SWCorner[0] + latIncrement, 6)

		for j in range(numCols):
			cellValue = (i * numCols) + j + 1

			longIncrement = ((NECorner[1] - SWCorner[1])/numCols) * j
			longComponent = np.round(NWCorner[1] + longIncrement, 6)

			XYCoordDict.update({cellValue : [latComponent, longComponent]})

	for i in range(numDataPoints):
		nodeElevationDict.update({i+1 : elevDataFlat[i]})

	maxPtIndex = max(nodeElevationDict, key=nodeElevationDict.get)
	maxPtElev = nodeElevationDict[maxPtIndex]

	minPtIndex = min(nodeElevationDict, key=nodeElevationDict.get)
	minPtElev = nodeElevationDict[minPtIndex]

	regionHighPt = (maxPtIndex, maxPtElev)
	regionLowPt = (minPtIndex, minPtElev)

	XYFlatten = []

	for XYPair in XYCoordDict:
		XYFlatten.append(XYCoordDict[XYPair][0] / XYCoordDict[XYPair][1])

	if len(tHeadCoords) == 0:
		trailHeadPt = 0
	else:
		tHeadFlatten = tHeadCoords[0] / tHeadCoords[1]
		tHeadKeyVal = min(XYFlatten, key = lambda x : abs(x - tHeadFlatten))
		tHeadIndex = XYFlatten.index(tHeadKeyVal) + 1
		tHeadElev = nodeElevationDict[tHeadIndex]

		trailHeadPt = (tHeadIndex, tHeadElev)

	if len(peakCoords) == 0:
		peakPt = 0
	else:
		peakFlatten = peakCoords[0] / peakCoords[1]
		peakKeyVal = min(XYFlatten, key = lambda x : abs(x - peakFlatten))
		peakIndex = XYFlatten.index(peakKeyVal) + 1
		peakElev = nodeElevationDict[peakIndex]

		peakPt = (peakIndex, peakElev)

	return nodeElevationDict, numRows, numCols

def nodeGraphGeneration():
	nodeMatrix = []
	adjacentNodeDict = {}

	nodeElevationDict, numRows, numCols = generateNodeElevationDict()

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
				peakXY = XYCoordDict[regionHighPt[0]]
				nodeXY = XYCoordDict[i]
				distanceHeuristic = np.sqrt((peakXY[0] - nodeXY[0])**2 + (peakXY[1] - nodeXY[1])**2)
				#Distance modified to account for human energy conserving behavior
				adjacentNodeDistanceDict.update({i : ((adjacentNodeElevation - currentNodeElevation) ** 2 * distanceHeuristic)})

			adjacentNodeDict.update({boundedNodeMatrix[row][column] : adjacentNodeDistanceDict})

	nodeMap = adjacentNodeDict

	return nodeMap, numRows, numCols

def dijkstra(nodeMapOutput, srcIndex, destIndex):
	inf = float('inf')
	source = (srcIndex + 1)
	dest =  destIndex + 1

	nodeMap = nodeMapOutput[0]
	numRows = nodeMapOutput[1]
	numCols = nodeMapOutput[2]

	#Establishes starting node and its respective distance value, establishes visited and unvisited node dictionary containers
	visitedNodeMap = {}
	unvisitedNodeMap = {}
	currentDistance = 0
	currentNode = source

	#Establishes storage container for list of nodes that came before the current node, used to determine waypoints of shortest path
	prevNodes = {}

	#Distance/cost map for every node, everything gets infinite distance except the starting node, which gets a value of zero
	#Also creates map of every node's most efficient previous iteration, allowing for paths to be known
	nodes = np.array(range(1, (numRows * numCols) + 1))
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

	        if currentNode == destIndex:
	        	break
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

	return pathToDest, numRows, numCols

def plotOptimalRoute(origin, destination):
	#Need to get lat long elev data
	pathToDest, numRows, numCols = dijkstra(nodeGraphGeneration(), origin, destination)

	longitudePathArray = []
	lattitudePathArray = []
	elevationPathArray = []

	for i in pathToDest:
		longitudePathArray.append(XYCoordDict[i][1])
		lattitudePathArray.append(XYCoordDict[i][0])
		elevationPathArray.append(nodeElevationDict[i])

	originDestX = [XYCoordDict[origin][1], XYCoordDict[destination][1]]
	originDestY = [XYCoordDict[origin][0], XYCoordDict[destination][0]]
	originDestZ = [nodeElevationDict[origin], nodeElevationDict[destination]]

	X, Y, Z = longitudePathArray, lattitudePathArray, elevationPathArray

	return [X, Y, Z, originDestX, originDestY, originDestZ], numRows, numCols

def coordinateExport():
	#Fetches data regarding the optimal path coordinates, origin, destination, numRows, and numCols
	if trailHeadPt != 0 and peakPt != 0:
		pathXYZ, numRows, numCols = plotOptimalRoute(trailHeadPt[0], peakPt[0])
	elif trailHeadPt != 0 and peakPt == 0: 
		pathXYZ, numRows, numCols = plotOptimalRoute(trailHeadPt[0], regionHighPt[0])
	elif trailHeadPt == 0 and peakPt != 0: 
		pathXYZ, numRows, numCols = plotOptimalRoute(regionLowPt[0], peakPt[0])
	else:
		pathXYZ, numRows, numCols = plotOptimalRoute(regionLowPt[0], regionHighPt[0])

	pathX = pathXYZ[0]
	pathY = pathXYZ[1]

	optimalXY = []

	for coord in range(len(pathX)):
		optimalXY.append([pathX[coord], pathY[coord]])

	# routeDataArray = np.array(optimalXY)
	# routeDataDF = pd.DataFrame(routeDataArray)
	# export_csv = routeDataDF.to_csv("optimalRoute2.csv", index = None, header = True)

	gpx.toGPX(pathX, pathY)

def renderVisualData3D():
	#Fetches data regarding the optimal path coordinates, origin, destination, numRows, and numCols
	if trailHeadPt != 0 and peakPt != 0:
		pathXYZ, numRows, numCols = plotOptimalRoute(trailHeadPt[0], peakPt[0])
	elif trailHeadPt != 0 and peakPt == 0: 
		pathXYZ, numRows, numCols = plotOptimalRoute(trailHeadPt[0], regionHighPt[0])
	elif trailHeadPt == 0 and peakPt != 0: 
		pathXYZ, numRows, numCols = plotOptimalRoute(regionLowPt[0], peakPt[0])
	else:
		pathXYZ, numRows, numCols = plotOptimalRoute(regionLowPt[0], regionHighPt[0])

	#Optimal Path coordinates set
	pathX = pathXYZ[0]
	pathY = pathXYZ[1]
	pathZ = pathXYZ[2]

	#Origin/Destination information set
	originDestX = pathXYZ[3]
	originDestY = pathXYZ[4]
	originDestZ = pathXYZ[5]

	xDataArray = []
	yDataArray = []
	zDataArray = []

	for i in range(numRows):
		tempContainerX = []
		tempContainerY = []
		tempContainerZ = []

		for j in range(numCols):
			tempContainerX.append(XYCoordDict[(i*numCols) + j + 1][1])
			tempContainerY.append(XYCoordDict[(i*numCols) + j + 1][0])
			tempContainerZ.append(nodeElevationDict[(i*numCols) + j + 1])

		xDataArray.append(tempContainerX)
		yDataArray.append(tempContainerY)
		zDataArray.append(tempContainerZ)

	X, Y, Z = np.array(xDataArray), np.array(yDataArray), np.array(zDataArray)
	
	fig = plt.figure()
	ax = plt.axes(projection = '3d')


	ax.scatter(pathX, pathY, pathZ, alpha = 0)

	line = mplot3d.art3d.Line3D(pathX, pathY, pathZ, color = 'red', linewidth = 4)
	ax.add_line(line)

	surfacePlot = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap='terrain', edgecolor='none', alpha = 0.5)
	ax.scatter(originDestX, originDestY, originDestZ, color = 'red', s = 100, alpha = 1, marker = '^')
	# x_range = [xyzDF['longitude'].min(), xyzDF['longitude'].max()]
	# y_range = [xyzDF['lattitude'].min(), xyzDF['lattitude'].max()]

	fig.colorbar(surfacePlot, shrink = 0.4, aspect = 10)
	plt.title(mapName + ' 3D Topographic Map')
	ax.set_xlabel('Degrees longitude')
	ax.set_ylabel('Degrees lattitude')
	ax.set_zlabel('Elevation ASL (feet)')
	plt.show()

def renderVisualData2D():
	#Fetches data regarding the optimal path coordinates, origin, destination, numRows, and numCols
	if trailHeadPt != 0 and peakPt != 0:
		pathXYZ, numRows, numCols = plotOptimalRoute(trailHeadPt[0], peakPt[0])
	elif trailHeadPt != 0 and peakPt == 0: 
		pathXYZ, numRows, numCols = plotOptimalRoute(trailHeadPt[0], regionHighPt[0])
	elif trailHeadPt == 0 and peakPt != 0: 
		pathXYZ, numRows, numCols = plotOptimalRoute(regionLowPt[0], peakPt[0])
	else:
		pathXYZ, numRows, numCols = plotOptimalRoute(regionLowPt[0], regionHighPt[0])

	#Optimal Path coordinates set
	pathX = pathXYZ[0]
	pathY = pathXYZ[1]
	pathZ = pathXYZ[2]

	#Origin/Destination information set
	originDestX = pathXYZ[3]
	originDestY = pathXYZ[4]
	originDestZ = pathXYZ[5]

	xDataArray = []
	yDataArray = []	
	zDataArray = []

	for i in range(numRows):
		tempContainerX = []
		tempContainerY = []
		tempContainerZ = []

		for j in range(numCols):
			tempContainerX.append(XYCoordDict[(i*numCols) + j + 1][1])
			tempContainerY.append(XYCoordDict[(i*numCols) + j + 1][0])
			tempContainerZ.append(nodeElevationDict[(i*numCols) + j + 1])

		xDataArray.append(tempContainerX)
		yDataArray.append(tempContainerY)
		zDataArray.append(tempContainerZ)

	#Prepares data for visualization
	plotLevels = np.array(range(9000, 14500, 40))
	X, Y, Z = np.array(xDataArray), np.array(yDataArray), np.array(zDataArray)
	fig = plt.figure()
	ax = plt.axes()

	#Draws contour map and optimal path
	surfacePlot = plt.contourf(X, Y, Z, levels = plotLevels, cmap = 'terrain')
	plt.plot(pathX, pathY, linewidth = 3, color = 'red')

	def on_pick(event):
		x, y = artist.get_xdata(), artist.get_ydata()
	
	#Assorted labeling and legends
	fig.colorbar(surfacePlot, shrink = 0.4, aspect = 10)
	plt.title(mapName + 'Regional Contour Map')
	ax.set_xlabel('Degrees longitude')
	ax.set_ylabel('Degrees lattitude')
	plt.show()

generateNodeElevationDict()
renderVisualData3D()
#coordinateExport()
#renderVisualData2D()