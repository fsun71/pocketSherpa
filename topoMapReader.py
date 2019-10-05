from osgeo import gdal
import matplotlib.pyplot as plt
import numpy as np
import os

def readGeoData(mapName, NWCorner = None, SECorner = None, units = 'imperial'):
	#Reads in NGS IMG file and eliminates any null or none values
	geo = gdal.Open('data/ngsMaps/' + mapName + '.img')
	gdal_band = geo.GetRasterBand(1)
	elevData = geo.ReadAsArray().astype(np.float)
	nodataval = gdal_band.GetNoDataValue()

	if np.any(elevData == nodataval):
		elevData[elevData == nodataval] = np.nan

	#Sets default corner values given a null/none input for those arguments
	NWCornerDefault = [float(mapName[1:3]), float(mapName[4:])]
	SECornerDefault = [float(mapName[1:3]) - 1, float(mapName[4:]) - 1]

	if NWCorner == None:
		NWCorner = NWCornerDefault

	if SECorner == None:
		SECorner = SECornerDefault

	SECorner = np.absolute(SECorner)

	#Converts data from meters to feet if units is imperial
	if units == 'imperial':
		elevData = elevData * 3.28084

	#Divides up lattitude and longitude units accordingly
	divisions = len(elevData)
	degResolution = 1/divisions
	lattitudes = [(SECornerDefault[0] + lat*degResolution) for lat in range(divisions)]
	longitudes = [(NWCornerDefault[1] - lon*degResolution) for lon in range(divisions)]

	#Finds index of closest matching subdivision to specified corner coordinates
	regionNWLat = lattitudes.index(min(lattitudes, key = lambda x : abs(x - NWCorner[0])))
	regionNWLong = longitudes.index(min(longitudes, key = lambda x : abs(x - NWCorner[1])))
	regionSELat = lattitudes.index(min(lattitudes, key = lambda x : abs(x - SECorner[0])))
	regionSELong = longitudes.index(min(longitudes, key = lambda x : abs(x - SECorner[1])))

	regionElevData = elevData[regionSELat:regionNWLat][regionNWLong:regionSELong]
	return regionElevData

# fig = plt.figure()
# ax = fig.add_subplot(111)

# plt.contour(elevData, cmap = "gist_earth", levels = list(range(6000, 15000, 200)))
# plt.title("Elevation Contours of North Mosquito and Tenmile Range")

# cbar = plt.colorbar()

# plt.show()
