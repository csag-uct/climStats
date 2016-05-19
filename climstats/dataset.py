import netCDF4
import cfunits

class Dataset(object):

	def __init__(self, uri):

		self.ds = netCDF4.Dataset(uri)
#		print self.ds.dimensions

		self.dimensions = self.ds.dimensions
		self.attributes = self.ds.__dict__
		self.variables = {}
		self.coordinates = {}
		self.ancil = {}

		# Find the coordinate variables
		for name, variable in self.ds.variables.items():
			units, coordinate = self.cf_coordinate(variable.__dict__)

			print name, units, coordinate
			
			if coordinate:
				self.coordinates[coordinate] = variable

				if coordinate == 'time':
					self.time_variable = variable
					self.time_dimensions = variable.dimensions

				if coordinate == 'latitude':
					self.lat_variable = variable
					self.lat_dimensions = variable.dimensions

				if coordinate == 'longitude':
					self.lon_variable = variable
					self.lon_dimensions = variable.dimensions

		# Find the data variables (with time dimension)
		for name, variable in self.ds.variables.items():

			if name not in self.coordinates:
				if set(self.time_dimensions).issubset(variable.dimensions):
					self.variables[name] = variable

		# All other variables are ancilary
		for name, variable in self.ds.variables.items():

			if name not in self.coordinates and name not in self.variables:
				self.ancil[name] = variable


	@classmethod
	def cf_coordinate(cls, attrs):

		if 'units' in attrs.keys():

			units = cfunits.Units(attrs['units'])

			if units.islatitude:
				return units, 'latitude'
			if units.islongitude:
				return units, 'longitude'
			if units.isreftime:
				return units, 'time'
			else:
				return units, False

		else:
			return False, False


if __name__ == "__main__":

	import sys

	ds = dataset(sys.argv[1])

	print ds.time_dimensions
	print ds.lat_dimensions
	print ds.lon_dimensions
	print ds.coordinates.keys()
	print ds.variables.keys()
	print ds.ancil.keys()