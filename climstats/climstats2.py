import numpy as np
import netCDF4
import datetime
import argparse
import sys
import slicing
#import functions
import dataset
import logging

logging.basicConfig(level=logging.DEBUG)


parser = argparse.ArgumentParser('Calculate climate statistics on station or gridded CF compliant datasets')
parser.add_argument('source', type=str)
parser.add_argument('-a', '--aggregation', type=str, choices=['month', 'season', 'yearmonth', 'yearseason', 'year'], default='yearmonth')
parser.add_argument('-s', '--statistic', type=str, required=True)
parser.add_argument('-o', '--output', type=str, required=True)
args = parser.parse_args()

statistic = args.statistic.split(',')
aggregation = args.aggregation.split(',')

# Try and open source dataset
try:
	source = dataset.NetCDF4Dataset(args.source)
except:
	logging.error("cannot open source dataset: {}".format(args.source))
	logging.error(sys.exc_info())
	sys.exit(1)

logging.info("processing: {}".format(args.source))

for name, variable in source.variables.items():
	logging.info(variable)

	# datetimes = netCDF4.num2date(variable.coords['time'][:], variable.coords['time'].units, calendar=variable.coords['time'].calendar)

	#slices, newtimes = slicing.yearmonth(variable.coords['time'])

	variable.subset(time=('2000-1-1', '2012-12-31'))

 	groups = variable.groupby('time.yearmonth')

 	result = groups.apply(np.ma.mean)

 	print result

 	dataset.NetCDF4Dataset.write(result, 'test.nc')

# 	for group, indices in groups.items():
#		print group, variable[indices].mean(axis=0)


