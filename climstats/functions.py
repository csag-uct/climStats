import numpy as np
import scipy


def setup(variable, slices, axis=0):

	shape = list(variable.shape)
	shape[axis] = len(slices)
	shape = tuple(shape)

	result = np.ma.zeros(shape, dtype=variable.dtype)
	mask = np.ma.getmaskarray(result)
	time = np.ma.zeros((len(slices),), dtype=np.float32)

	return result, mask, time


def run(func, params, variable, slices, axis=0, *args, **kwargs):


	if 'valid' in kwargs.keys():
		valid = kwargs['valid']
	else:
		valid = 1.0

	result, mask, time = setup(variable, slices, axis)

	for i in range(0, len(slices)):
		#print slices[i]

		data = variable[slices[i]]

		mask[i] = data.count(axis=axis) < float(slices[i].stop - slices[i].start) * valid
		result[i] = func(data, params=params, axis=axis, *args, **kwargs)

	return np.ma.masked_array(result, mask)


def days_above(data, params=[0], axis=0):
	return np.ma.masked_less_equal(data, float(params[0])).count(axis=axis)

def days_below(data, params=[0], axis=0):
	return np.ma.masked_greater_equal(data, float(params[0])).count(axis=axis)

def heatwave_tnc(data, params=[35.0], axis=0):
	
	shape = list(data.shape)
	tsteps = shape[axis]

	shape[axis] = 1
	result = np.zeros(tuple(shape), dtype=np.int16)

	for i in range(0, tsteps-3):
		result += int(data[i,i+3].min(axis=axis) > params[0])

	return result


registry = {
	'mean':np.ma.mean,
	'sum':np.ma.sum,
	'days_above':days_above,
	'heatwave_tnc': heatwave_tnc
}
