from osgeo import gdal
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
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
	regionNWLat = min(lattitudes, key = lambda x : abs(x - NWCorner[0]))
	regionNWLong = min(longitudes, key = lambda x : abs(x - NWCorner[1]))
	regionSELat = min(lattitudes, key = lambda x : abs(x - SECorner[0]))
	regionSELong = min(longitudes, key = lambda x : abs(x - SECorner[1]))

	NWLatIndex = lattitudes.index(regionNWLat)
	NWLongIndex = longitudes.index(regionNWLong)
	SELatIndex = lattitudes.index(regionSELat)
	SELongIndex = longitudes.index(regionSELong)

	#print(regionSELat, regionNWLat, regionNWLong, regionSELong)
	regionElevData = elevData[SELatIndex:NWLatIndex, NWLongIndex:SELongIndex]
	regionBoundsArray = [regionSELat, regionNWLat, regionNWLong, regionSELong]
	latDimension, longDimension = regionElevData.shape

	regionLatArray = np.arange(regionSELat, regionNWLat, step = (regionNWLat - regionSELat) / latDimension)
	regionLongArray = np.arange(regionNWLong, regionSELong, step = (regionSELong - regionNWLong) / longDimension)

	return regionElevData, regionLatArray, regionLongArray

def dataContourPlot(title = None):
	elevData, regionLatArray, regionLongArray = readGeoData('n41w106', [40.275289, -105.643432], [40.231365, -105.569274])

	scaleLowerLim = int(np.round(np.amin(elevData) * 0.95, -3))
	scaleUpperLim = int(np.round(np.amax(elevData) * 1.05, -3))

	ax = plt.axes(projection = '3d')
	X, Y = np.meshgrid(regionLongArray, regionLatArray)
	surfacePlot = ax.plot_surface(X, Y, elevData, cmap = "terrain")
	ax.set_xlabel('Degrees Longitude')
	ax.set_ylabel('Degrees Lattitude')
	ax.set_zlabel('Elevation (Feet ASL)')

	if title != None:
		plt.title("Elevation Contour Map of " + title)

	cbar = plt.colorbar(surfacePlot, shrink = 0.4, aspect = 10)

	plt.show()