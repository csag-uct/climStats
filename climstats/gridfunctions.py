import numpy as np
from shapely.geometry import Polygon


def makegrid(latvar, lonvar):


	# If we have 1D lat/lon vars make them 2D
	if len(latvar.shape) == 1 and len(lonvar.shape) == 1:		
		lonvar, latvar = np.meshgrid(lonvar, latvar)


	shape = latvar.shape
	shape_big = tuple([s+1 for s in shape])

	print shape, shape_big

	lat_midpt = np.zeros(shape_big, dtype=latvar.dtype)
	lon_midpt = np.zeros(shape_big, dtype=latvar.dtype)

	lat_midpt[1:-1,1:-1] = (latvar[:-1,:-1] + latvar[1:,:-1] + latvar[1:,1:] + latvar[:-1,1:])/4.0
	lon_midpt[1:-1,1:-1] = (lonvar[:-1,:-1] + lonvar[1:,:-1] + lonvar[1:,1:] + lonvar[:-1,1:])/4.0

	dlat = latvar[1:,:] - latvar[:-1,:]
	dlon = lonvar[:,1:] - lonvar[:,:-1]

	# Extrapolate the boundary points
	lat_midpt[0,:] = 2 * lat_midpt[1,:] - lat_midpt[2,:]
	lat_midpt[-1,:] = 2 * lat_midpt[-2,:] - lat_midpt[-3,:]
	lat_midpt[:,0] = 2 * lat_midpt[:,1] - lat_midpt[:,2]
	lat_midpt[:,-1] = 2 * lat_midpt[:,-2] - lat_midpt[:,-3]

	lon_midpt[0,:] = 2 * lon_midpt[1,:] - lon_midpt[2,:]
	lon_midpt[-1,:] = 2 * lon_midpt[-2,:] - lon_midpt[-3,:]
	lon_midpt[:,0] = 2 * lon_midpt[:,1] - lon_midpt[:,2]
	lon_midpt[:,-1] = 2 * lon_midpt[:,-2] - lon_midpt[:,-3]


	# Construct the shapely geometries
	polys = []

	for y in range(0,shape_big[0]-1):
		
		row = []

		for x in range(0, shape_big[1]-1):

#			print latvar[y,x], lonvar[y,x]

			coords = []
			coords.append((lon_midpt[y,x],lat_midpt[y,x]))
			coords.append((lon_midpt[y+1,x],lat_midpt[y+1,x]))
			coords.append((lon_midpt[y+1,x+1],lat_midpt[y+1,x+1]))
			coords.append((lon_midpt[y,x+1],lat_midpt[y,x+1]))

			poly = Polygon(coords)

			row.append(poly)

		polys.append(row)

	return shape, polys