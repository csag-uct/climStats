import sys
import numpy
import datetime
import glob
import netCDF4

calendars = ['standard', 'noleap', '360_day']
fill_value = 1e10

sourcepath = sys.argv[1]
outfilename = sys.argv[2]
varname = sys.argv[3]

time_units = 'days since 1800-01-01'

filenames = glob.glob(sourcepath + '/*.txt')

def date_fromlong(longdate):
	
	year = int(longdate/1000000)
	month = int((longdate - year*1000000)/10000)
	day = int((longdate - year*1000000 - month*10000)/100)
	hour = int(longdate - year*1000000 - month*10000 - day*100)
	

	return datetime.datetime(year, month, day, hour)

def bruce_to_series(file, metaonly=True):
	
	lines = file.readlines()
	
	ID, latitude, longitude, altitude = tuple(lines[0].split())
	
	parts = lines[1].split()
	startdate, enddate = (date_fromlong(long(parts[0])), date_fromlong(long(parts[1])))
	calendar = calendars[int(parts[2])]
	
	name = lines[2].strip().strip('_')

	print ID, name, latitude, longitude, altitude, startdate, enddate
		
	if not metaonly:
		values = numpy.array([float(line) for line in lines[3:]])
		values[values < -90] = fill_value
	else:
		values = None

	return ID, name, latitude, longitude, altitude, startdate, enddate, calendar, values
	

global_startdate = datetime.datetime(2200,12,31)
global_enddate = datetime.datetime(1800,1,1)

# Quick meta-data pass
count = 0
for filename in filenames:
	print filename
	try:
		file = open(filename)
	except:
		print("cannot open file {}".format(filename))
		continue
	
	try:
		ID, name, latitude, longitude, elevation, startdate, enddate, calendar, values = bruce_to_series(file)
	except:
		print("cannot parse file: {}".format(sys.exc_info()))
		continue

	file.close()
	
	if startdate < global_startdate:
		global_startdate = startdate
		
	if enddate > global_enddate:
		global_enddate = enddate
		
	count += 1

print "Found %d features" % (count)
print "Date range: %s - %s" % (repr(global_startdate), repr(global_enddate))

time_units = "days since {:4d}-{:02d}-{:02d} 12:00".format(global_startdate.year, global_startdate.month, global_startdate.day)

#days = (global_enddate - global_startdate).days + 1
days = netCDF4.date2num(global_enddate, time_units, calendar) - netCDF4.date2num(global_startdate, time_units, calendar) + 1
print '%d days in date range' % (days)


# Create netcdf output file
outdata = netCDF4.Dataset(outfilename, 'w', format='NETCDF4')

# Create dimensions
time_dim = outdata.createDimension('time', days)
feature_dim = outdata.createDimension('feature', count)

# Create the variables
time_var = outdata.createVariable('time', 'f4', ('time',))
time_var.units = time_units
data_var = outdata.createVariable(varname, 'f4', ('time', 'feature',), zlib=True, fill_value=1e10)
data_var.coordinates = 'latitude longitude'

latitude_var = outdata.createVariable('latitude', 'f4', ('feature',))
latitude_var.units = 'degrees_north'

longitude_var = outdata.createVariable('longitude', 'f4', ('feature',))
longitude_var.units = 'degrees_east'

elevation_var = outdata.createVariable('elevation', 'f4', ('feature',))
elevation_var.units = 'meters'
elevation_var.positive = 'up'

id_var = outdata.createVariable('id', str, ('feature',))
name_var = outdata.createVariable('name', str, ('feature',))

# We repopulate the meta-data just in case the ordering of the file listing has changed!

# Slower full data read
index = 0
data_tmp = numpy.empty((days, count), dtype=numpy.float32)
data_tmp[:] = fill_value
print "data_tmp: ", data_tmp.shape

for filename in filenames:
	
	try:
		file = open(filename)
	except:
		continue
	
	try:
		ID, name, latitude, longitude, elevation, startdate, enddate, calendar, values = bruce_to_series(file, metaonly=False)
	except:
		continue

	file.close()
	
	#startdate_offset = (startdate - global_startdate).days
	#enddate_offset = (enddate - global_startdate).days
	startdate_offset = netCDF4.date2num(startdate, time_units, calendar) - netCDF4.date2num(global_startdate, time_units, calendar)
	enddate_offset = netCDF4.date2num(enddate, time_units, calendar) - netCDF4.date2num(global_startdate, time_units, calendar)
	print startdate_offset, enddate_offset
	
	#print startdate_offset, enddate_offset, days
	#data_var[index,startdate_offset:enddate_offset+1] = values
	#print data_tmp.shape
	#print len(values)
	#print data_tmp[startdate_offset:enddate_offset+1, index].shape
	data_tmp[startdate_offset:enddate_offset+1, index] = values


	latitude_var[index] = float(latitude)
	longitude_var[index] = float(longitude)
	elevation_var[index] = float(elevation)
	id_var[index] = ID
	name_var[index] = unicode(name, errors='ignore')
	
	index += 1

data_var[:] = data_tmp

#date = global_startdate
#time_values = []
#while (date <= global_enddate):
#	time_values.append(netCDF4.date2num(date, time_units, calendar))
#	date = date + datetime.timedelta(1)

time_values = []
start_timeval = netCDF4.date2num(global_startdate, time_units, calendar)
for i in range(0,int(days)):
	time_values.append(start_timeval + i)
	
	
time_var[:] = numpy.array(time_values)
time_var.calendar = calendar

outdata.close()
	

	
	
	
