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
	nodes = []

	for i in range(1, (numRows * numCols) + 1):
		nodes.append(i)

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

	return pathToDest, numRows, numCols