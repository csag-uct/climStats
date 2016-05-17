import numpy as np
import netCDF4
import datetime
import argparse
import sys
import slicing
import functions
import dataset


parser = argparse.ArgumentParser('Calculate climate statistics on station or gridded CF compliant datasets')
parser.add_argument('source', type=str)
parser.add_argument('-a', '--aggregation', type=str, choices=['month', 'season', 'yearmonth', 'yearseason', 'year'], default='yearmonth')
parser.add_argument('-s', '--statistic', type=str, required=True)
parser.add_argument('-o', '--output', type=str, required=True)
args = parser.parse_args()

if args.statistic:
	parts = args.statistic.split(',')
	statistic = parts[0]
	params = parts[1:]

try:
	source = dataset.Dataset(args.source)
except:
	print("Cannot open source dataset: {}".format(args.source))
	print sys.exc_info()
	sys.exit(1)

print("processing: {}".format(args.source))

try:
	times = source.coordinates['time']
except:
	print("Cannot find time coordinate in dataset coordinates: {}".format(repr(source.coords)))
	sys.exit(1)


print("Found time coordinate variable: {} [{}]".format(source.coordinates['time'].name, len(times)))

if args.aggregation:
	parts = args.aggregation.split(',')
	aggregation = parts[0]
	aggr_params = parts[1:]	

slice_function = eval('slicing.{}'.format(aggregation))
slices, newtimes = slice_function(times, *aggr_params)

print("Aggregating to {} statistics, will produce {} time steps".format(aggregation, len(newtimes)))

outds = netCDF4.Dataset(args.output, 'w', format='NETCDF4_CLASSIC')

for name, dim in source.dimensions.items():
	if name == 'time':
		outds.createDimension(name, len(newtimes))
	else:
		outds.createDimension(name, dim.size)

for key, value in source.attributes.items():
	outds.setncattr(key, value)

if 'history' in source.ds.__dict__.keys():
	history = source.ds.history
else:
	history = ""

commandline = sys.argv[0]
for arg in sys.argv[1:]:
	commandline += ' {}'.format(arg)
outds.setncattr('history', '{}: {}; {}'.format(datetime.datetime.now().isoformat(), commandline, history))

for name, variable in source.coordinates.items():
	outvar = outds.createVariable(name, variable.dtype, dimensions=variable.dimensions)

	for key, value in variable.__dict__.items():
		outvar.setncattr(key, value)

	if name == 'time':
		outvar[:] = newtimes[:]
	else:
		outvar[:] = variable[:]


for name, variable in source.ancil.items():
	outvar = outds.createVariable(name, variable.dtype, dimensions=variable.dimensions)

	for key, value in variable.__dict__.items():
		outvar.setncattr(key, value)
	
	outvar[:] = variable[:]


for name, variable in source.variables.items():
	outvar = outds.createVariable(name, variable.dtype, dimensions=variable.dimensions)

	for key, value in variable.__dict__.items():
		outvar.setncattr(key, value)

	outvar[:] = functions.run(functions.registry[statistic], params, source.variables[name], slices)

outds.close()
		
