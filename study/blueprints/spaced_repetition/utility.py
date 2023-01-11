import math

def projectMemoryRetention(t, threshold, steepness, change, T=0):
    """Project memory retention at a given x (named t) with constants threshold,
    steepnesss, and change assuming revision on every day where there the retention
    is less than threshold"""
    memoryRetention = math.pow(math.e, -steepness * (math.pow(change, T) * t))
    if memoryRetention < threshold:
        t = t - math.log(threshold) / (-steepness * (math.pow(change, T)))
        return projectMemoryRetention(t, threshold, steepness, change, T=T+1)
    return [T, memoryRetention]

def calculateMemoryRetention(t, T, steepness, change):
    """Return memory retention given time since studying, times studied,
    and the constants steepness and change"""
    if T == 0:
        return 0
    memoryRetention = math.pow(math.e, -steepness * math.pow(change, T) * t)
    return memoryRetention

def getDaysOfRevision(t, T, threshold, steepness, change, absoluteDayLimit=500, absoluteDay=0):
    """Return a list of days from the given value on which the user would revise
    if following the spaced repetition suggestions. Limit controls how many days
    from t to go up to"""
    if absoluteDay >= absoluteDayLimit:
        return []
    memoryRetention = calculateMemoryRetention(t, T, steepness, change)
    if memoryRetention < threshold:
        days = [[t+absoluteDay, memoryRetention]]
        days.extend(getDaysOfRevision(0, T+1, threshold, steepness, change, absoluteDayLimit, absoluteDay+1))
        return days
    else:
        return getDaysOfRevision(t+1, T, threshold, steepness, change, absoluteDayLimit, absoluteDay+1)

def calculateTimeUntilBelowThreshold(t, T, threshold, steepness, change):
    """Return number of days until the the memory retention falls below the given
    threshold form now based on the number of times studied and time already passed since studying"""
    memoryRetention = calculateMemoryRetention(t, T, steepness, change)
    timeUntil = 0
    while memoryRetention > threshold:
        timeUntil += 1
        memoryRetention = calculateMemoryRetention(t+timeUntil, T, steepness, change)
    return timeUntil