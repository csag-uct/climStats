import sys
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import seaborn
import numpy as np
import dataset


def makegrid(latitudes, longitudes, datashape):


	if len(latitudes.shape) == 1 and len(longitudes.shape) == 1:
		longitudes, latitudes = np.meshgrid(longitudes, latitudes)

	if latitudes.shape == datashape and longitudes.shape == datashape:

		shape_big = tuple([s+1 for s in datashape])
		
		big_lats = np.empty(shape_big, dtype=np.float32)
		big_lons = np.empty(shape_big, dtype=np.float32)

		big_lats[1:-1,1:-1] = (latitudes[:-1,:-1] + latitudes[1:,:-1] + latitudes[1:,1:] + latitudes[:-1,1:])/4.0
		big_lons[1:-1,1:-1] = (longitudes[:-1,:-1] + longitudes[1:,:-1] + longitudes[1:,1:] + longitudes[:-1,1:])/4.0

		dlat = latitudes[1:,:] - latitudes[:-1,:]
		dlon = longitudes[:,1:] - longitudes[:,:-1]

		# Extrapolate the boundary points
		big_lats[0,:] = 2 * big_lats[1,:] - big_lats[2,:]
		big_lats[-1,:] = 2 * big_lats[-2,:] - big_lats[-3,:]
		big_lats[:,0] = 2 * big_lats[:,1] - big_lats[:,2]
		big_lats[:,-1] = 2 * big_lats[:,-2] - big_lats[:,-3]

		big_lons[0,:] = 2 * big_lons[1,:] - big_lons[2,:]
		big_lons[-1,:] = 2 * big_lons[-2,:] - big_lons[-3,:]
		big_lons[:,0] = 2 * big_lons[:,1] - big_lons[:,2]
		big_lons[:,-1] = 2 * big_lons[:,-2] - big_lons[:,-3]

		return big_lats, big_lons

	else:
		return latitudes, longitudes


def plotmap(variable, mode='multi', tstep=0, proj='merc', style='pcolormesh', clevs=20):

	latitudes = variable.coords['latitude'][:]
	longitudes = variable.coords['longitude'][:]

	lats, lons = makegrid(latitudes, longitudes, variable.shape[-2:])

	vmin, vmax = variable[:].min(), variable[:].max()

	llcrnrlat, urcrnrlat = lats.min(), lats.max()
	llcrnrlon, urcrnrlon = lons.min(), lons.max()
	lat_ts = lats.mean()
	lon_0 = lons.mean()

	fig = plt.figure(figsize=(10,14))

	cols, rows = 1, 1

	if mode == 'tstep':
		data = variable[:][tstep]
	elif mode == 'mean':
		data = variable[:].mean(axis=0)
	elif mode == 'multi':
		nplots = variable.shape[0]
		cols = int(np.floor(np.sqrt(nplots)))
		rows = int(np.ceil(np.sqrt(nplots)))

		print nplots, cols, rows

	fig, axes = plt.subplots(rows, cols, squeeze=False)

	for col in range(cols):
		for row in range(rows):
			print col, row, col+cols*row
			if proj == 'merc':
				m = Basemap(projection='merc',llcrnrlat=llcrnrlat,urcrnrlat=urcrnrlat,llcrnrlon=llcrnrlon,urcrnrlon=urcrnrlon,lat_ts=lat_ts,resolution='l', ax=axes[row][col])
			elif proj == 'lcc':
				m = Basemap(projection='lcc',llcrnrlat=llcrnrlat,urcrnrlat=urcrnrlat,llcrnrlon=llcrnrlon,urcrnrlon=urcrnrlon,lat_0=lat_ts,lon_0=lon_0,resolution='l', ax=axes[row][col])

			x, y = m(lons, lats)

			if mode == 'multi':
				data = variable[col+cols*row]

			if style == 'pcolormesh':
				m.pcolormesh(x, y, data, vmin=vmin, vmax=vmax, cmap='Blues')
			elif style == 'contour':
				m.contourf(x, y, data, clevs)
				m.contour(x, y, data, clevs, colors='black')

			m.fillcontinents(color='white',lake_color='aqua',zorder=0)
			m.drawcoastlines(linewidth=1.0)

			plt.tight_layout()

	return plt
