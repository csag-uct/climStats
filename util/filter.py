import sys
import numpy
import datetime
import glob
import netCDF4


startdate = datetime.datetime(1960,1,1,12)
enddate = datetime.datetime(2015,12,31,12)

threshold = 0
elevation_gte = False
elevation_lte = False

sourcefilename = sys.argv[1]
targetfilename = sys.argv[3]
varname = sys.argv[2]

geometry = None


if len(sys.argv) > 4:
	
	import shapely
	import ogr
	from shapely.wkb import loads
	from shapely.ops import cascaded_union
	from shapely import speedups
	speedups.enable()	

	shapefilename = sys.argv[4]
	shapefile = ogr.Open(shapefilename)
	boundary = shapefile.GetLayer(0)

	geometries = []
	while True:

			feature = boundary.GetNextFeature()
			if not feature:
					break

			geometries.append(loads(feature.GetGeometryRef().ExportToWkb()))

	geometry = cascaded_union(geometries)
	bounds = geometry.bounds
	print "Got geometry with bounds: ", bounds


source = netCDF4.Dataset(sourcefilename)

time_var = source.variables['time']
time_units = time_var.units
time_vals = time_var[:]
global_startdate_value = time_vals[0]
global_enddate_value = time_vals[-1]
print time_vals
print "Date range: %s - %s" % (netCDF4.num2date(global_startdate_value, time_units), netCDF4.num2date(global_enddate_value, time_units))

latitude_var = source.variables['latitude']
longitude_var = source.variables['longitude']
elevation_var = source.variables['elevation']
id_var = source.variables['id'][:]
print id_var.shape
name_var = source.variables['name'][:]

startdate_value = netCDF4.date2num(startdate, time_units)
enddate_value = netCDF4.date2num(enddate, time_units)
print startdate_value, enddate_value

start_index = numpy.argmax((time_vals == startdate_value))
end_index = numpy.argmax((time_vals == enddate_value))
if end_index == 0:
    end_index = len(time_vals)-1
print "Start_index, end_index", start_index, end_index

#print "Filter index range: %d - %d" % (startdate_index, enddate_index)

data_var = source.variables[varname]

alldata = data_var[start_index:end_index+1,:]

selection = []

for feature in range(0, id_var.shape[0]):
	values = alldata[:,feature]
	
	if not len(values):
		continue
	
	valid = len(values[~values.mask])
	percent = 100.0* valid/alldata.shape[0]
    
	if threshold:
		if percent < threshold:
			continue
			
	if elevation_gte:
		if elevation_var[feature] < elevation_gte:
			continue
			
	if elevation_lte:
		if elevation_var[feature] > elevation_lte:
			continue
			
	if geometry:
		point = shapely.geometry.Point(longitude_var[feature], latitude_var[feature])
		if not point.within(geometry):
			continue

	print "%-15s\t%-25s\t%.2f\t%d" % (id_var[feature], name_var[feature].encode('utf-8', errors='ignore'), elevation_var[feature], percent)
#	print "%20s\t%.2f\t%d" % (id_var[feature], elevation_var[feature], percent)

	selection.append(feature)
			
		
print len(selection)

# Create netcdf output file
target = netCDF4.Dataset(targetfilename, 'w', format='NETCDF4')

# Create dimensions
target_time_dim = target.createDimension('time', end_index - start_index + 1)
target_feature_dim = target.createDimension('feature', len(selection))

# Create the variables
target_time_var = target.createVariable('time', 'f4', ('time',))
target_time_var.units = time_units
target_time_var[:] = time_vals[start_index:end_index+1]


target_latitude_var = target.createVariable('latitude', 'f4', ('feature',))
target_latitude_var.units = 'degrees_north'
target_latitude_var[:] = latitude_var[selection]

target_longitude_var = target.createVariable('longitude', 'f4', ('feature',))
target_longitude_var.units = 'degrees_east'
target_longitude_var[:] = longitude_var[selection]

target_elevation_var = target.createVariable('elevation', 'f4', ('feature',))
target_elevation_var.units = 'meters'
target_elevation_var.positive = 'up'
target_elevation_var[:] = elevation_var[selection]

target_id_var = target.createVariable('id', str, ('feature',))
i = 0
for item in id_var[selection]:
	target_id_var[i] = str(id_var[selection][i])
	i += 1

target_name_var = target.createVariable('name', str, ('feature',))
i = 0
for item in name_var[selection]:
	target_name_var[i] = unicode(name_var[selection][i])
	i += 1


target_data_var = target.createVariable(varname, 'f4', ('time', 'feature',), zlib=True, fill_value=1e10)
attr_names = data_var.ncattrs()
for name in attr_names:
	target_data_var.setncattr(name, data_var.getncattr(name))
	
print target_data_var.shape, alldata.shape
target_data_var[:] = alldata[:,selection]

	


