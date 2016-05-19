import netCDF4
import numpy as np

def yearmonth(timevar):

	try:
		calendar = timevar.calendar
	except:
		calendar = 'standard'

	datetimes = netCDF4.num2date(timevar[:], timevar.units, calendar=calendar)
	
	months = np.array([d.month for d in datetimes])

	monthends = months[1:] - months[:-1]
	indices = monthends.nonzero()[0]

	slices = []
	newtimes = []
	start = 0
	for index in indices:
		slices.append(slice(start,index+1))
		newtimes.append(timevar[index])
		start = index+1
	
	slices.append(slice(start, len(datetimes)))
	newtimes.append(timevar[len(datetimes)-1])

	return  slices, newtimes