import matplotlib.pyplot as plt
import seaborn as sb
import netCDF4
import numpy as np
import dataset
import sys


ds = dataset.NetCDF4Dataset(sys.argv[1])

variable = ds.variables[sys.argv[2]]

times = variable.coords['time']
realtimes = netCDF4.num2date(times[:], times.attributes['units'])
print realtimes[0], realtimes[-1]

ids = ds.ancil['id']
print ids[:]
names = ds.ancil['name']

if len(sys.argv) < 4:
	for name in names:
		print name, ids[list(names[:]).index(name)]

else:
	index = list(ids[:]).index(sys.argv[3])
	#print names[index]

	values = variable[:,index]
	print values

	if len(sys.argv) > 4:
		plottype = sys.argv[4]
	else:
		plottype = 'line'

	if plottype == 'line':
		plt.plot(realtimes, values)
	if plottype == 'bar':
		widths = [(realtimes[i] - realtimes[i+1]).days for i in range(len(realtimes)-1)]
		widths.append(widths[-1])

		widths = np.array(widths)
		widths = widths * 0.7

		plt.bar(realtimes, values, width=widths)

	plt.savefig("{}.png".format(sys.argv[3]))