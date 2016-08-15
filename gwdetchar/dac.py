import numpy as np

def find_crossings(timeseries,threshold):
    """Find the times that a timeseries crosses a specific value

    Parameters
    ----------
    timeseries : `~gwpy.timeseries.TimeSeries`
        the input data to test against a threshold
    threshold : `float`
        function will analyze input timeseries and find times when data 
        crosses this threshold

    Returns
    -------
    times : `numpy.ndarray`
        an array of GPS times (`~numpy.float64`) at which the input data 
        crossed the threshold
    """
    if threshold >= 0:
        crossing_idx = np.nonzero(np.diff((timeseries.value >= threshold).astype(int)))[0]+1
    else:
        crossing_idx = np.nonzero(np.diff((timeseries.value > threshold).astype(int)))[0]+1
    
    return timeseries.times.value[crossing_idx]

