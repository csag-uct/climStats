# Climstats
The climstats package is for manipulation of multi-dimensional array type datasets such as are commonly used in climate science.  The package
consists of the climstats package itself which provides modules to read and write different types of datasets, grouping functions (currently only grouping
on the time axis), and statistical functions that can be applied to groups.

Also included is the climstats command line program which reads datasets and calculates different statistics on different aggregations (also currently only time based aggregations) before writing out a new dataset.

# The climstats command line program

Basic usage:

```
usage: Calculate climate statistics on station or gridded CF compliant datasets
       [-h] -a AGGREGATION -s STATISTIC [-n OUTNAME] [--scale SCALE]
       [--offset OFFSET] [--tolerance TOLERANCE] [--above ABOVE]
       [--below BELOW] [--window_func WINDOW_FUNC] [--window WINDOW]
       [--format FORMAT] [--plot PLOT] -o OUTPUT
       source variable
```
`source` is the source filename (or uri)
`variable` is the name of the variable to process

`-h` just displays the above usage

`-a AGGREGATION` specific the aggregation/grouping function to use.  They are specified as [coordinate].[grouping] where *coordinate* is the coordinate along which the grouping should be applied (mostly time), and *grouping* is the grouping function to use.  Currently these include:

*yearmonth:* Groups on unique year/month combinations and so produces a classic monthly series
*year:* Groups on unique years and so produces a yearly series
*month:* Groups on unique months and so generally will produce 12 groups (unless the source is shorter than a year)
*season:* Groups on unique seasons from the set of (DJF, MAM, JJA, SON) so produces 4 groups (unless the source is shorter than a year)
*yearseason:* Groups on unique year/season combinations so produces seasonal series
*day:* Groups on unique days [note: this should be renamed to yearmonthday to be consistent] so produces daily series
*yearweek:* Groups on unique year/week combinations so produces weekly series

`-s STATISTIC` specifies the statistics function to run on each group to produce the output.  Currently available functions are:

*mean:* Calculates the mean along the grouping axis
*median:* Calculates the median along the grouping axis
*total:* Calculates the total along the grouping axis
*maximum:* Calculates the maximum along the grouping axis
*minimum:* Calculates the minimum along the grouping axis
*percentile90th:* Calculates the value of the 90th percentile of values along the grouping axis
*percentile95th:* Calculates the value of the 95th percentile of values along the grouping axis
*percentile99th:* Calculates the value of the 99th percentile of values along the grouping axis
*days:* Calculates the number of unmasked/valid days along the grouping axis (typically used in combination with --above and/or --below)

`-n OUTNAME` specifies a name for the resultant variable if you don't want it to be the same as the source variable

`--scale` specifies a scaling constat to multiply the source variable by before running a function (typically used to change units)
`--offset` specifies an offset constant to add to the source variable before running a function (typically used to change units, eg. kelvin to C)
`--tolerance` specifies the fraction between 0.0 and 1.0 of missing values to tolerate before setting the result to missing.
`--above` mask all values below this value (typically used for threshold based statistics such as day counts or totals above a threshold)
`--below` mask all values above this value (typically used for threshold based statistics such as day counts or totals below a threshold)
`--window_func` ignore for now
`--window` ignore for now
`--format` specifies options for the output format.  Currently just lets you specify the NETCDF format (NETCDF4, NETCDF4_CLASSIC, etc..)
`--plot` ignore for now
`-o` name of the output file

 










