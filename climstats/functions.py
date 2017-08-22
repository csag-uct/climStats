import numpy as np
import scipy.stats
import matplotlib.pyplot as plt

from numba import jit

def make_percentile_function(percentile):

	def f(data, axis):
		data = np.ma.filled(data, np.nan)
		return np.nanpercentile(data, percentile, axis=axis)

	return f

def not_masked(data, axis):
	return data.getmaskarray().all(axis=0).astype(np.int16)

def generic(data, func, axis=0, above=None, below=None, **kwargs):

	# Mask less than above and greater than below
	if above != None:
		data = np.ma.masked_array(data, data <= above)
	if below != None:
		data = np.ma.masked_array(data, data >= below)

	#print func(data, axis=axis)
	#print np.ma.count(data, axis=axis)

	return np.ma.filled(func(data, axis=axis), fill_value=0.0)

	
def mean(data, **kwargs):
	return generic(data, np.ma.mean, **kwargs)

def total(data, **kwargs):
	return generic(data, np.ma.sum, **kwargs)

def maximum(data, **kwargs):
	return generic(data, np.ma.max, **kwargs)

def minimum(data, **kwargs):
	return generic(data, np.ma.min, **kwargs)

def median(data, **kwargs):
	return generic(data, make_percentile_function(50), **kwargs)

def percentile90th(data, **kwargs):
	return generic(data, make_percentile_function(90), **kwargs)

def percentile95th(data, **kwargs):
	return generic(data, make_percentile_function(95), **kwargs)

def percentile99th(data, **kwargs):
	return generic(data, make_percentile_function(99), **kwargs)

def days(data, axis=0, **kwargs):
	return generic(data, np.ma.count, **kwargs)

#@jit(nopython=True)
def maximum_spell(data, axis=0, above=1e20, below=1e20, **kwargs):

	# Mask less than above and greater than below
	if above != 1e20:
		data = np.ma.masked_array(data, data <= above)
	if below != 1e20:
		data = np.ma.masked_array(data, data >= below)

	onezeros = (~np.ma.getmaskarray(data)).astype(int)

	print(onezeros[:,1])
	shape = list(onezeros.shape)

	#shape[axis] -= 1

	tmp = np.zeros(onezeros.shape)

	for i in range(1,onezeros.shape[axis]):
		tmp[i] = tmp[i-1] + onezeros[i]
		tmp[i] *= onezeros[i]

	result = np.ma.filled(tmp.max(axis=axis), fill_value=0.0)
	print(result)
	
	return result


def window_generic(data, func, axis=0, window=1, above=None, below=None, window_func=np.ma.sum):

	# Mask less than above and greater than below
	if above:
		data = np.ma.masked_less(data, above)
	if below:
		data = np.ma.masked_greater(data, below)

	tsteps = data.shape[axis]

	shape = list(data.shape)
	
	shape[axis] = 1
	result = np.ma.zeros(tuple(shape), dtype=np.int16)

	shape[axis] = tsteps - window + 1
	tmp = np.ma.zeros(tuple(shape), dtype=np.int16)

	for i in range(0, tsteps-window):
		tmp[i] = window_func(data[i:i+window], axis=axis)

	result[:] = func(tmp, axis=axis)

	return result

def window_mean(data, **kwargs):
	return window_generic(data, np.ma.mean, **kwargs)

def window_total(data, **kwargs):
	return window_generic(data, np.ma.sum, **kwargs)

def window_maximum(data, **kwargs):
	return window_generic(data, np.ma.max, **kwargs)

def window_minimum(data, **kwargs):
	return window_generic(data, np.ma.min, **kwargs)

def window_days(data, **kwargs):
	return window_generic(data, np.ma.count, window_func=not_masked, **kwargs)


def spi(data, length, fit_start=None, fit_end=None):
	
	result = np.empty(data.shape)
	result[:] = 1e10

	length = int(length)

	print('spi length', length)
	print('spi data.shape', data.shape)
	

	for index in np.ndindex(data.shape[1:]):
		
		slices = [slice(None)]
		slices.extend(index)

		values = data[slices]
		
		if values.count():
			print(index)

			tave = []
			for i in range(length, data.shape[0]):
				tave.append(values[i-length:i].mean(axis=0))
			tave = np.array(tave)

			if fit_start and fit_end:
				fit_start, fit_end = int(fit_start), int(fit_end)				
				shape, loc, scale = scipy.stats.gamma.fit(tave[fit_start-length:fit_end-length])
			else:
				shape, loc, scale = scipy.stats.gamma.fit(tave)

			dist = scipy.stats.gamma(shape, loc=loc, scale=scale)
			cdfs = dist.cdf(tave)*0.9999
			spi = scipy.stats.norm.ppf(cdfs)

#			print 'values(min, mean, max)', tave.min(), tave.mean(), tave.max()
#			print 'shape, loc, scale = ', shape, loc, scale
#			print 'cdf(min, mean, max) = ', cdfs.min(), cdfs.mean(), cdfs.max()
#			print 'spi(min, mean, median, max) = ', spi.min(), spi.mean(), np.median(spi), spi.max()
#			print

			result[slices][length:] = spi

	return np.ma.masked_greater(result, 1e9)

registry = {
	'mean': {'function': mean, 'units':None },
	'total': {'function': total, 'units':None },
	'maximum': {'function': maximum, 'units':None },
	'minimum': {'function': minimum, 'units':None },
	'median': {'function': median, 'units':None},
	'percentile90th': {'function': percentile90th, 'units':None},
	'percentile95th': {'function': percentile95th, 'units':None},
	'percentile99th': {'function': percentile99th, 'units':None},
	'days': {'function': days, 'units':'days'},
	'maxspell':{'function':maximum_spell, 'units':'days'},
	'rolling_maximum': {'function': window_maximum, 'units':None},
	'rolling_days': {'function': window_days, 'units':'days'},
	'spi': {'function':spi, 'units':'spi'}
}
