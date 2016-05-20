import numpy as np
import scipy



def days_above(data, params=[0], axis=0):
	return np.ma.masked_less_equal(data, float(params[0])).count(axis=axis)

def days_below(data, params=[0], axis=0):
	return np.ma.masked_greater_equal(data, float(params[0])).count(axis=axis)

def window_sum_above(data, params=[5,0], axis=0):

	window = int(params[0])
	above = float(params[1])

	print 'window_sum_above ', window, above
	shape = list(data.shape)
	tsteps = shape[axis]

	shape[axis] = 1
	result = np.ma.zeros(tuple(shape), dtype=np.int16)

	for i in range(0, tsteps-window):
		result += (data[i:i+window].sum(axis=axis) > above).astype(int)

	return result

def window_mean_above(data, params=[5,0], axis=0):

	window = int(params[0])
	above = float(params[1])

	print 'window_sum_above ', window, above
	shape = list(data.shape)
	tsteps = shape[axis]

	shape[axis] = 1
	result = np.ma.zeros(tuple(shape), dtype=np.int16)

	for i in range(0, tsteps-window):
		result += (data[i:i+window].mean(axis=axis) > above).astype(int)

	return result


def window_min_above(data, params=[5,0], axis=0):

	window = int(params[0])
	above = float(params[1])

	print 'window_sum_above ', window, above
	shape = list(data.shape)
	tsteps = shape[axis]

	shape[axis] = 1
	result = np.ma.zeros(tuple(shape), dtype=np.int16)

	for i in range(0, tsteps-window):
		result += (np.ma.min(data[i:i+window], axis=axis) > above).astype(int)

	return result



registry = {
	'mean': {'function': np.ma.mean, 'units':None },
	'sum': {'function': np.ma.mean, 'units':None },
	'max': {'function': np.ma.mean, 'units':None },
	'min': {'function': np.ma.mean, 'units':None },
	'days_above': {'function': days_above, 'units':'days'},
	'days_below': {'function': days_above, 'units':'days'},
	'window_min_above': {'function': window_min_above, 'units':'days'}
}
