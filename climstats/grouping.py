import pandas as pd
import datetime
import xarray as xr

def yearmonth(times):

	timestamps = [pd.Timestamp(t) for t in times]
	yearmonths = [datetime.datetime(ts.year, ts.month, 1) for ts in timestamps]
	
	return xr.DataArray(yearmonths, name='yearmonths', dims=['time'])