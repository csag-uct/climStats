import numpy as np
import cfunits
import copy
import sys

import netCDF4

class DatasetException(Exception):
	"""
	General, very simple Dataset exception class
	"""

	def __init__(self, value):
		self.value = value

	def __str__(self):
		return repr(self.value)


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

	def __init__(self, name, dataset, dimensions, dtype=np.float32, attributes={}):

		self.name = name
		self._dimensions = []
		self._dtype = dtype
		self.attributes = {}
		self.coords = {}
		self.iscoordinate = False

		# Load dimensions
		for dim in dimensions:
			self._dimensions.append(dataset._dimensions[dim])

		# Load attributes
		for key, value in attributes.items():
			if type(value) in [str, unicode]:
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
		raise NotImplementedError('__getitem__ method not implemented for {}'.format(self.__class__.__name__))

	def copy(self):
		return copy.copy(self)

	def resize(self, newshape, fill=None):
		raise NotImplementedError('resize method not implemented for {}'.format(self.__class__.__name__))

	def __setitem__(self, indices, value):
		"""
		__setitem__(indices, value): Implements array setting with ability to resize/extend along
		the unlimited dimension(s)
		"""
		print indices
		# force indices to be a tuple
		if type(indices) == slice:
			indices = (indices,)

		# Now make it a list
		indices = list(indices)

		# Check index bounds are valid and deal resizing unlimited dimensions
		newshape = list(self.shape)
		for i in range(0, len(indices)):

			start, stop = indices[i].start, indices[i].stop

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

		print 'setitem resizing to ', newshape, ' using ', indices
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


	def makecoords(self):

		for coord, variable in self.dataset.coords.items():
			if set(variable.dimensions).issubset(self.dimensions):
				self.coords[coord] = variable

	def isubset(self, **kwargs):

		print 'subsetting ', self.name, kwargs
		for name, value in kwargs.items():

			if name in self.coords:
				print 'subsetting ', name, ' coordinate with ', value
				coord = self.coords[name]

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

				# Check if the new start is going to go beyond existing subset
				if start > self._subset[i].stop - self._subset[i].start:
					start = self._subset[i].stop
				
				# Check if the new stop is going to go beyond existing subset
				if stop > self._subset[i].stop:
					stop = self._subset[i].stop

				newsubset = list(self._subset)
				newsubset[i] = slice(start, stop)	
				self._subset = tuple(newsubset)

				self._shape = tuple([s.stop - s.start for s in self._subset])

				# Now we need to copy the coordinate variable and subset it
				self.coords[name] = coord.copy()
				self.coords[name]._subset = (self._subset[i],)
				self.coords[name]._shape = (self._subset[i].stop - self._subset[i].start,)

	def subset(self, **kwargs):

		newargs = {}

		for name, value in kwargs.items():
			if name in self.coords:

				coord = self.coords[name]

				if type(value) == tuple:
					start, stop = tuple([coord[:].searchsorted(v) for v in value])
				else:
					start = stop = coord[:].searchsorted(value)

				stop += 1
				newargs[name] = slice(start, stop)

		print 'newargs = ', newargs
		self.isubset(**newargs)



	def __repr__(self):
		return "<Variable: {} {} {}>".format(self.name, self.dtype.__name__, self.shape)


class Variable(BaseVariable):

	def __init__(self, *args, **kwargs):

		super(Variable, self).__init__(*args, **kwargs)
		self._data = np.empty(self.shape, dtype=self.dtype)

	def __getitem__(self, indices):
		return self._data[self._subset][indices]

	def __setitem__(self, indices, value):
		super(Variable, self).__setitem__(indices, value)
		self._data[self._subset][indices] = value

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

	def __getitem__(self, indices):
		return self._data[self._subset][indices]

	def __setitem__(self, indices, value):
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
				self.coords[coordinate] = variable
				self.coords[coordinate].iscoordinate = True

				if coordinate == 'time':
					self.time_dimension = variable.dimensions[0]


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

			NetCDF4Variable(name, self, dimensions=variable.dimensions, attributes=attrs)



if __name__ == "__main__":

	print Dimension('time')
	print Dimension(('time', 120))

	ds = Dataset(dimensions=[('time',0,True), ('latitude',144), ('longitude',72)])
	tvar = Variable('time', ds, dimensions=['time'], attributes={'units':'days since 1977-01-01'})
	var = Variable('test', ds, dimensions=['time', 'latitude', 'longitude'])
	print var
	print var._data
	print var.dataset
	print var.dataset.variables
	print ds.variables
	print ds.coords

	var[:10,] = 42.0
	print var[:10,]

	var[40:50,] = 13.0
	print var[40:60]
	print var.shape

	tvar[:] = np.arange(var.shape[0])+100

	print ds.coords
	print var.coords

	print var._subset
	var.subset(time=(109,120))
	print var._subset
	print var[:]

	print var.coords['time']
	print var.coords['time'][:]
	print ds.coords['time'][:]

	ds = NetCDF4Dataset(sys.argv[1])
	print ds.dimensions
	print ds.coords
	print ds.variables
	print

	print ds.coords['time'][:]

