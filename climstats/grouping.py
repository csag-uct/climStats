from collections import OrderedDict
import netCDF4


def yearmonth(timevar):

	result = OrderedDict()

	datetimes = netCDF4.num2date(timevar[:], timevar.units, calendar=timevar.calendar)

	for index in range(0, len(datetimes)):

		yearmonth = datetimes[index].year, datetimes[index].month

		if yearmonth not in result.keys():
			result[yearmonth] = [index]
		else:
			result[yearmonth].append(index)

	return result


