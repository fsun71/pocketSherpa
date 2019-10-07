from osgeo import gdal
import matplotlib.pyplot as plt
import numpy as np
import os

def readGeoData(mapName, NWCorner = None, SECorner = None, units = 'imperial'):
	#Reads in NGS IMG file and eliminates any null or none values
	mapName.rstrip('.img')
	geo = gdal.Open('data/ngsMaps/' + mapName + '.img')
	gdal_band = geo.GetRasterBand(1)
	elevData = np.flip(np.array(geo.ReadAsArray().astype(np.float)),0)
	nodataval = gdal_band.GetNoDataValue()

	if np.any(elevData == nodataval):
		elevData[elevData == nodataval] = np.nan

	#Sets default corner values given a null/none input for those arguments
	NWCornerDefault = [float(mapName[1:3]), float(mapName[4:])]
	SECornerDefault = [float(mapName[1:3]) - 1, float(mapName[4:]) - 1]

	#Returns entire degree by degree section if given no coordinate input
	if NWCorner == None:
		NWCorner = NWCornerDefault

	if SECorner == None:
		SECorner = SECornerDefault

	#Ensures lattitude values are negative given the map region is in the western hemisphere (true for all of united states)
	if mapName[3] == 'w':
		NWCorner[1] = -np.absolute(NWCorner[1])
		SECorner[1] = -np.absolute(SECorner[1])

	if mapName[3] == 'e':
		NWCorner[1] = np.absolute(NWCorner[1])
		SECorner[1] = np.absolute(SECorner[1])

	#Converts data from meters to feet if units is imperial
	if units == 'imperial':
		elevData = elevData * 3.28084

	#Divides up lattitude and longitude units accordingly
	divisions = len(elevData)
	degResolution = 1/divisions
	lattitudes = [(SECornerDefault[0] + lat*degResolution) for lat in range(divisions)]
	longitudes = [(-np.absolute(NWCornerDefault[1]) + lon*degResolution) for lon in range(divisions)]

	#Finds index of closest matching subdivision to specified corner coordinates
	regionNWLat = lattitudes.index(min(lattitudes, key = lambda x : abs(x - NWCorner[0])))
	regionNWLong = longitudes.index(min(longitudes, key = lambda x : abs(x - NWCorner[1])))
	regionSELat = lattitudes.index(min(lattitudes, key = lambda x : abs(x - SECorner[0])))
	regionSELong = longitudes.index(min(longitudes, key = lambda x : abs(x - SECorner[1])))

	#print(regionSELat, regionNWLat, regionNWLong, regionSELong)
	regionElevData = elevData[regionSELat:regionNWLat, regionNWLong:regionSELong]

	return regionElevData

def dataContourPlot(contourResolution = 10, title = None):
	elevData = readGeoData('n40w107', [39.457476, -106.178689], [39.281785, -106.054310])

	plt.contour(elevData, cmap = "gist_earth", levels = list(range(6000, 15000, contourResolution)))

	if title != None:
		plt.title("Elevation Contour Map of " + title)

	cbar = plt.colorbar()

	plt.show()

dataContourPlot(title = 'North Mosquito and Tenmile Range')