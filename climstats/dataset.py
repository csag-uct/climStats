import numpy as np
import cfunits
import copy
import sys
from dateutil import parser

import netCDF4
import grouping

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class DatasetException(Exception):
	"""
	General, very simple Dataset exception class
	"""

	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)

class GroupBy(object):

	def __init__(self, name, variable, coordinate, groups):

		self.name = name
		self.groups = groups
		self.variable = variable
		self.coordinate = coordinate

	def apply(self, func, name=None, outunits=None, tolerance=0.0, scale=1.0, offset=0.0, **params):
		"""
		func: The function to call, must be a callable and take an numpy array or equivalent as its first argument
		name: If specified, the resultant variable will be named using this parameter
		tolerance: The fraction of masked source values (along the axis) tolerated before masking the result
		scale: Scale factor to apply to source values
		offset: Offset to apply to source values
		"""

		logger.debug("{}.apply({}, {}, {}, {}, {}".format(self.__class__.__name__, func.__name__, name, tolerance, scale, offset, params))

		# Identify the axis index of the coordinate
		axis = self.variable.dimensions.index(self.coordinate.dimensions[0])
		logger.debug("axis = {}".format(axis))

		# Create dimensions for the resultant dataset and construct matching slices
		dims = []
		slices = []
		for i in range(0, len(self.variable.dimensions)):

			dim = self.variable.dimensions[i]
			slices.append(slice(0, dim.size))

			# The axis dimension size is the number of groups, others are original size
			if i == axis:
				dims.append((dim.name, len(self.groups), dim.isunlimited))
			else:
				dims.append((dim.name, dim.size, dim.isunlimited))

		# Create an in memory dataset and copy attributes
		ds = Dataset(dimensions=dims)
		ds.attributes = copy.copy(self.variable.dataset.attributes)
		logger.debug("Created {}".format(repr(ds)))

		# If we don't have variable name, construct one from the original name and the function name
		if not name:
			name = "{}_{}".format(self.variable.name, func.__name__)

		# Make the results variable and copy original attributes
		result = Variable(name, ds, [dim.name for dim in self.variable.dimensions], dtype=self.variable.dtype, attributes=self.variable.attributes)
		result.attributes = copy.copy(self.variable.attributes)
		if outunits:
			result.attributes['units'] = outunits
		logger.debug("Created {}".format(result))

		# Make the new coordinate variable
		newcoord = Variable(self.coordinate.name, ds, [self.coordinate.dimensions[0].name], dtype=self.coordinate.dtype)
		newcoord.attributes = copy.copy(self.coordinate.attributes)
		logger.debug("Created {}".format(newcoord))

		# Initialize the source and target slices
		source_slices = copy.copy(slices)
		target_slices = copy.copy(slices)

		# Now we loop through the groups
		index = 0
		for group, indices in self.groups.items():
			
			# Set the source and target slices
			source_slices[axis] = indices
			target_slices[axis] = index

			logger.debug("source[{}]".format(tuple(source_slices)))
			
			source = self.variable[tuple(source_slices)] * scale + offset
			#logger.debug("{} masked values in source data".format(np.ma.count_masked(source)))

			unmasked = func(source, axis=axis, **params)
			mask = np.ma.count(self.variable[tuple(source_slices)], axis=axis)/float(source.shape[axis]) < tolerance

			result[tuple(target_slices)] = np.ma.masked_array(unmasked, mask=mask)
			newcoord[(target_slices[axis],)] = self.coordinate[tuple(source_slices)[axis]][-1]

			logger.debug("{} masked values in target data".format(np.ma.count_masked(result[tuple(target_slices)])))

			index += 1

		# Create the coordinate variables
		for name, variable in self.variable.coords.items():
			if variable != self.coordinate:
				newvar = Variable(variable.name, ds, [dim.name for dim in variable.dimensions], dtype=variable.dtype)
				newvar.attributes = copy.copy(variable.attributes)
				newvar[:] = variable[:]
		
		# Create the ancilary variables
		for name, variable in self.variable.dataset.ancil.items():
			try:
				newvar = Variable(name, ds, [dim.name for dim in variable.dimensions], dtype=variable.dtype)
				newvar[:] = variable[:]
				newvar.attributes = copy.copy(variable.attributes)
			
			# This might fail if the ancil variable uses dimensions not defined through the source variable... ignore these
			except:
				print("WARNING: Error writing ancil variable {}".format(name))
				print(sys.exc_info()[0])

		return ds



class Dimension(object):
	"""
	Dimension class
	"""

	def __init__(self, dim, size=None):
		
		# Default size value is 0 for unlimited
		self._size = 0
		self._unlimited = False

		# We can accept a simple string
		if type(dim) == str:
			self.name = dim

		# Or a tuple of form (name, size, [unlimited])
		elif type(dim) == tuple:
			self.name, self._size = dim[:2]
			if len(dim) == 3:
				self._unlimited = dim[2]



	@property
	def size(self):
	    return self._size

	@property
	def isunlimited(self):
	    return self._unlimited
	
	def __unicode__(self):
		return u'[{}: {}]'.format(self.name, self.size)

	def __repr__(self):
		return '[{}: {}]'.format(self.name, self.size)


class BaseVariable(object):

	def __init__(self, name, dataset, dimensions, attributes={}, dtype=np.float32, fillvalue=1e10):
#		print("{}.__init__: {}".format(self.__class__.__name__, dtype))

		self.name = name
		self._dimensions = []
		self._dtype = dtype
		self._fillvalue = fillvalue
		self.attributes = {}
		self.coords = {}
		self.iscoordinate = False

		# Load dimensions
		for dim in dimensions:
			self._dimensions.append(dataset._dimensions[dim])

		# Load attributes
		for key, value in attributes.items():
			self.attributes[key] = value

		shape = [dim.size for dim in self._dimensions]
		self._shape = tuple(shape)

		self._subset = tuple([slice(0,stop) for stop in self.shape])

		self.dataset = dataset
		dataset.addVariable(self)


	@property
	def shape(self):
	    return self._shape

	@property
	def dimensions(self):
	    return self._dimensions
	
	@property
	def dtype(self):
	    return self._dtype

	def __getitem__(self, indices):
		"""
		Just merges indices with the variables current subset
		"""
		newindices = []

		if type(indices) != tuple:
			indices = (indices,)


		for i in range(len(indices)):

			if type(indices[i]) == list:
				newindices.append(np.array(indices[i]) + self._subset[i].start)

			elif type(indices[i]) == np.ndarray:
				newindices.append(indices[i] + self._subset[i].start)

			elif type(indices[i]) == int:
				newindices.append(indices[i] + self._subset[i].start)

			elif type(indices[i]) == slice:
				start = indices[i].start
				stop = indices[i].stop

				if not start:
					start = self._subset[i].start
				else:
					start += self._subset[i].start

				if not stop:
					stop = self._subset[i].stop
				else:
					stop += self._subset[i].start

				newindices.append(slice(start, stop))


#		print "._data[{}]".format(tuple(newindices))

		return self._data[tuple(newindices)]


	def copy(self):
		return copy.copy(self)

	def resize(self, newshape, fill=None):
		raise NotImplementedError('resize method not implemented for {}'.format(self.__class__.__name__))

	def __setitem__(self, indices, value):
		"""
		__setitem__(indices, value): Implements array setting with ability to resize/extend along
		the unlimited dimension(s)
		"""

		# force indices to be a tuple
		if type(indices) == slice or type(indices) == int:
			indices = (indices,)

		# Now make it a list
		indices = list(indices)

		# Check index bounds are valid and deal with resizing unlimited dimensions
		newshape = list(self.shape)
		for i in range(0, len(indices)):

			if type(indices[i]) == slice:
				start, stop = indices[i].start, indices[i].stop
			elif type(indices[i]) == int:
				start, stop = indices[i], indices[i]+1

			# replace Nones
			if not start:
				start = 0
			if not stop:
				stop = self.shape[i]

			indices[i] = slice(start, stop)

			if indices[i].stop > self.shape[i]:

				if self._dimensions[i].isunlimited:
					newshape[i] = indices[i].stop
				else:
					raise IndexError('index {} out of bounds for variable with shape {}'.format(indices[i], self.shape))

		newshape = tuple(newshape)
		
		# See if the shape has changed
		if newshape != self.shape:

			self.resize(tuple(newshape))

			# Resize associated coordinate variables
			coord_indices = []
			for coord, variable in self.coords.items():
				for dim in variable.dimensions:
					try:
						coord_indices.append(variable.dimensions.index(dim))
					except:
						continue

				newshape = tuple([newshape[i] for i in coord_indices])
				
				if len(newshape):
					variable.resize(newshape)

		self._data[indices] = value

	def makecoords(self):

		# Reset to empty dict
		self.coords = {}

		# Find all coordinates relevant to this variable
		for coord, variable in self.dataset.coords.items():
			if set(variable.dimensions).issubset(self.dimensions):
				self.coords[coord] = variable



	def isubset(self, **kwargs):

		print 'subsetting ', self.name, self._subset, kwargs
		for name, value in kwargs.items():

			if name in self.coords:
				coord = self.coords[name]
				print 'subsetting ', name, ' coordinate ', coord[:], ' with ', value

				# For now we can't do multi dimensional coordinate variables
				if len(coord.shape) > 1:
					raise NotImplementedError("multi dimensional coordinate subsetting not yet implemented")

				# Find the relevant dimension
				i = self.dimensions.index(coord.dimensions[0])

				if type(value) == tuple:
					start, stop = value
				if type(value) == int:
					start, stop = value, value+1
				if type(value) == slice:
					start, stop = value.start, value.stop

				print 'start, stop = ', start, stop

				# Add to original start
				start += self._subset[i].start
				stop += self._subset[i].stop

				if start >= self._subset[i].stop:
					start = self._subset[i].stop - 1

				if stop > self._subset[i].stop:
					stop = self._subset[i].stop	

				print 'new start, stop = ', start, stop

				newsubset = list(self._subset)
				newsubset[i] = slice(start, stop)	
				self._subset = tuple(newsubset)

				self._shape = tuple([s.stop - s.start for s in self._subset])

				# Now we need to copy the coordinate variable and subset it
				self.coords[name] = coord.copy()
				self.coords[name]._subset = (self._subset[i],)
				self.coords[name]._shape = (self._subset[i].stop - self._subset[i].start,)


	def isubset_copy(self, **kwargs):

		newvar = self.copy()

		print 'subsetting ', newvar.name, newvar._subset, kwargs
		for name, value in kwargs.items():

			if name in newvar.coords:
				coord = newvar.coords[name]
				print 'subsetting ', name, ' coordinate ', coord[:], ' with ', value

				# For now we can't do multi dimensional coordinate variables
				if len(coord.shape) > 1:
					raise NotImplementedError("multi dimensional coordinate subsetting not yet implemented")

				# Find the relevant dimension
				i = newvar.dimensions.index(coord.dimensions[0])

				if type(value) == tuple:
					start, stop = value
				if type(value) == int:
					start, stop = value, value+1
				if type(value) == slice:
					start, stop = value.start, value.stop

				print 'start, stop = ', start, stop

				# Add to original start
				start += newvar._subset[i].start
				stop += newvar._subset[i].stop

				if start >= newvar._subset[i].stop:
					start = newvar._subset[i].stop - 1

				if stop > newvar._subset[i].stop:
					stop = newvar._subset[i].stop	

				print 'new start, stop = ', start, stop

				newsubset = list(newvar._subset)
				newsubset[i] = slice(start, stop)	
				newvar._subset = tuple(newsubset)

				newvar._shape = tuple([s.stop - s.start for s in newvar._subset])

				# Now we need to copy the coordinate variable and subset it
				newvar.coords[name] = coord.copy()
				newvar.coords[name]._subset = (newvar._subset[i],)
				newvar.coords[name]._shape = (newvar._subset[i].stop - newvar._subset[i].start,)

		return newvar


	def subset(self, **kwargs):

		newargs = {}

		for name, value in kwargs.items():
			if name in self.coords:

				coord = self.coords[name]
				print "subset using ", coord[:], coord._subset

				if type(value) == tuple:
					start, stop = value
				else:
					start = stop = value

				print "subset start, stop ", start, stop

				# try and coerce into datetimes
				try:
					start = netCDF4.date2num(parser.parse(start), coord.attributes['units'])
				except:
					pass

				try:
					stop = netCDF4.date2num(parser.parse(stop), coord.attributes['units'])
				except:
					pass

				print "subset start, stop ", start, stop

				newargs[name] = slice(coord[:].searchsorted(start), coord[:].searchsorted(stop)+1)

		print 'newargs = ', newargs
		self.isubset(**newargs)


	def groupby(self, param):

		coordname, funcname = param.split('.')

		# Get the coordinate variable
		coordinate = self.coords[coordname]

		# Try and get the function
		try:
			func = eval('grouping.{}'.format(funcname))
		except:
			pass

		# Run the grouping funciton on the coordinate variable
		groups = func(coordinate)

		# Check if we can convert any groups to slices (1 dimensionsal coordinate only for now!)
		if len(coordinate.shape) == 1:

			for key, indices in groups.items():
				if (indices[-1] - indices[0] + 1) == len(indices):
					groups[key] = slice(indices[0], indices[-1] + 1)

		return GroupBy(funcname, self, coordinate, groups)



	def __repr__(self):
		return "<Variable: {} {} {}>".format(self.name, self.shape, self.dtype)


class Variable(BaseVariable):

	def __init__(self, *args, **kwargs):
		#print("{}.__init__: {} {}".format(self.__class__.__name__, args,kwargs))
		super(Variable, self).__init__(*args, **kwargs)

		if self.dtype == str:
			self._data = np.empty(self.shape, dtype=object)
		else:
			self._data = np.ma.empty(self.shape, dtype=self.dtype)

#	def __getitem__(self, indices):
#		print("{}.__getitem__: {}".format(self.__class__.__name__, indices))
#		return self._data[self._subset][indices]

#	def __setitem__(self, indices, value):
#		print("{}.__setitem__: {}".format(self.__class__.__name__, indices))
#		print value
#		super(Variable, self).__setitem__(indices, value)

#		self._data[self._subset][indices] = value
#		print 

	def copy(self):
		new  = super(Variable, self).copy()
		new._data = self._data.copy()
		return new

	def resize(self, newshape, fill=None):
		self._data.resize(tuple(newshape), refcheck=False)
		self._shape = tuple(newshape)
		self._subset = tuple([slice(0,stop) for stop in self.shape])


class NetCDF4Variable(BaseVariable):

	def __init__(self, *args, **kwargs):
		super(NetCDF4Variable, self).__init__(*args, **kwargs)
		self._data = self.dataset.ncfile.variables[self.name]

#	def __getitem__(self, indices):
#		print("{}.__getitem__: {}".format(self.__class__.__name__, indices))
#		return self._data[self._subset][indices]

	def __setitem__(self, indices, value):
#		print("{}.__setitem__: {}".format(self.__class__.__name__, indices))
		super(NetCDF4Variable, self).__setitem__(indices, value)
		self._data[self._subset][indices] = value



class Dataset(object):

	def __init__(self, dimensions=[], attributes={}, variables={}):

		self._dimensions = {}
		self.attributes = {}

		self._allvariables = {}
		self.variables = {}
		self.ancil = {}
		self.coords = {}


		# Load dimensions
		for dim in dimensions:
				newdim = Dimension(dim)
				self._dimensions[newdim.name] = newdim

		# Load attributes
		for key, value in attributes.items():
			if type(value) in [str, unicode]:
				self.attributes[key] = value

		# Load variables
		for variable in variables:
			
			if not 'dtype' in variable:
				dtype = np.float32
			else:
				dtype = eval('type({})'.format(variable['dtype']))

			newvar = Variable(variable['name'], self, variable['dims'], dtype=dtype)

	@property
	def dimensions(self):
	    return self._dimensions
	

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

	def make_coords(self):

		# Find the coordinate variables
		for name, variable in self._allvariables.items():

			units, coordinate = self.cf_coordinate(variable.attributes)

			#print name, units, coordinate
			
			if coordinate:

				# Ignore not valid time coordinates!
				if coordinate == 'time' and name != 'time':
					continue

				self.coords[coordinate] = variable
				self.coords[coordinate].iscoordinate = True

				if name == 'time' and coordinate == 'time':
					self.time_dimension = variable.dimensions[0]
					variable.units = units.units
					# Try and set the calendar attribute
					try:
						variable.calendar = variable.attributes['calendar']
					except:
						variable.calendar = 'standard'


		# Find the data variables (with time dimension)
		for name, variable in self._allvariables.items():

			if name not in self.coords:
				if self.time_dimension in variable.dimensions:
					self.variables[name] = variable

		# All other variables are ancilary
		for name, variable in self._allvariables.items():

			if name not in self.coords and name not in self.variables:
				self.ancil[name] = variable

		# Call makecoords on all variables
		for name, variable in self.variables.items():
			variable.makecoords()


	def addVariable(self, variable):

		if variable.name in self.variables:
			raise DatasetException("ERROR: variable {} already exists in dataset {}".format(variable.name, self))
		else:
			self._allvariables[variable.name] = variable
			try:
				self.make_coords()
			except:
				pass

	def __repr__(self):
		return "<{}: dims[{}] variables[{}]>".format(self.__class__.__name__, self.dimensions.keys(), self.variables.keys())


class NetCDF4Dataset(Dataset):

	def __init__(self, uri):

		self.ncfile = netCDF4.Dataset(uri)

		dimensions = []
		for name, dim in self.ncfile.dimensions.items():
			dimensions.append((dim.name, dim.size, dim.isunlimited()))

		super(NetCDF4Dataset, self).__init__(dimensions=dimensions)

		for name, variable in self.ncfile.variables.items():
			attrs = {}
			for key in variable.ncattrs():
				attrs[key] = variable.getncattr(key)

			NetCDF4Variable(name, self, dimensions=variable.dimensions, attributes=attrs, dtype=variable.dtype)

	@classmethod
	def write(cls, dataset, filename):

		ncfile = netCDF4.Dataset(filename, 'w', format='NETCDF4')

		for key, value in dataset.attributes:
			ncfile.setncattr(key, value)

		for name, dim in dataset.dimensions.items():
			print 'writing dimension', name, dim
			ncfile.createDimension(name, dim.size)


		for name, variable in dataset._allvariables.items():
			print 'writing variable ', name, variable, variable.dtype

			if variable.dtype == object:
				dtype = str
			else:
				dtype = variable.dtype

			var = ncfile.createVariable(name, dtype, [dim.name for dim in variable.dimensions])

			for key, value in variable.attributes.items():
				var.setncattr(key, value)

			var[:] = variable[:]

		ncfile.close()


if __name__ == "__main__":

	print Dimension('time')
	print Dimension(('time', 120))

	ds = Dataset(dimensions=[('time',0,True), ('latitude',144), ('longitude',72)])
	tvar = Variable('time', ds, dimensions=['time'], attributes={'units':'days since 1977-01-01'})
	var = Variable('test', ds, dimensions=['time', 'latitude', 'longitude'])
	print var
	print tvar
#	print var._data
#	print var.dataset
	print ds.variables
	print ds.coords
	print

	var[:10,] = 42.0
#	print var[:10,]
	print ds.variables
	print ds.coords
	print

	var[40:50,] = 13.0
#	print var[40:60]
	print ds.variables
	print ds.coords
	print

	tvar[:] = np.arange(var.shape[0])+100
	print ds.variables
	print ds.coords
	print


	print 'subsetting'
	print var.isubset_copy(time=(109,120))
	print var
	print var.coords
	print

	print 'subsetting2'
	print var.isubset_copy(time=(109,120))
	print var
	print var.coords
	print 


	print 'NetCDF4Dataset'
	ds = NetCDF4Dataset(sys.argv[1])
	print ds.dimensions
	print ds.coords
	print ds.variables
	print ds.variables['pr'].attributes
	print

	ds.variables['pr'].subset(time='2016-12-31')
	print ds.variables['pr'].coords
	print netCDF4.num2date(ds.variables['pr'].coords['time'][:], ds.variables['pr'].coords['time'].attributes['units'])
	print

	ds.variables['pr'].subset(time='1800-12-31')
	print ds.variables['pr'].coords
	print netCDF4.num2date(ds.variables['pr'].coords['time'][:], ds.variables['pr'].coords['time'].attributes['units'])
	print

	ds.variables['pr'].subset(time=('1977-1-1', '1977-1-30'))
	print ds.variables['pr'].coords
	print netCDF4.num2date(ds.variables['pr'].coords['time'][:], ds.variables['pr'].coords['time'].attributes['units'])
