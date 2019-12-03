import numpy as np
import pandas as pd

def toGPX(pathX, pathY):
	GPXFile = open("optimalRouteGPX.gpx", "w")
	GPXFile.write('<gpx xmlns="http://www.topografix.com/GPX/1/1" version="1.1" creator="14ers.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd">')
	GPXFile.write('<rte>')
	GPXFile.write('<name>Optimal path generate by pocketSherpa</name>')

	for coord in range(len(pathX)):
		GPXFile.write('<rtept lon=' + str(pathX[coord]) + 'lat=' + str(pathY[coord]) + '>')
		GPXFile.write('<ele>3430.84</ele>')
		GPXFile.write('</rtept>')

	GPXFile.write('</rte>')
	GPXFile.write('</gpx>')