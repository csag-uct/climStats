import numpy as np
import netCDF4
import datetime
import argparse
import sys
import slicing
import functions
import dataset
import logging

logging.basicConfig(level=logging.DEBUG)


parser = argparse.ArgumentParser('Calculate climate statistics on station or gridded CF compliant datasets')
parser.add_argument('source', type=str)
parser.add_argument('variable', type=str)
parser.add_argument('-a', '--aggregation', type=str, required=True)
parser.add_argument('-s', '--statistic', type=str, required=True)
parser.add_argument('-o', '--output', type=str, required=True)
args = parser.parse_args()

varname = args.variable
statistic = args.statistic.split(',')[0]
params = args.statistic.split(',')[1:]
#aggregation = args.aggregation.split(',')


# Try and open source dataset
try:
	source = dataset.NetCDF4Dataset(args.source)
except:
	logging.error("cannot open source dataset: {}".format(args.source))
	logging.error(sys.exc_info())
	sys.exit(1)

logging.info("processing variable {} from {} ".format(varname, args.source))

variable = source.variables[varname]

groups = variable.groupby(args.aggregation)

result = groups.apply(functions.registry[statistic]['function'], params=params, name=varname, tolerance=0.8)

dataset.NetCDF4Dataset.write(result, args.output)



