import numpy as np
import scipy

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


#def spell_days(data, func)


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
	'rolling_maximum': {'function': window_maximum, 'units':None},
	'rolling_days': {'function': window_days, 'units':'days'}
}
