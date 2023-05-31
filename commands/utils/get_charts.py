import simfile
from simfile.types import Simfile, Chart


def getChartsAsInts(sm: Simfile, default: int = 0):
    """
    Returns a list of charts as integers. 
    If the meter in the simfile is not a number, it will be replaced with the `default` value.
    """
    charts = sm.charts

    def getMeter(c: Chart):
        if c.meter.isdigit():
            return int(c.meter)
        else:
            return default

    return list(map(getMeter, charts))


def getChartsAsStrings(sm: Simfile, difficulty_labels: bool = False):
    """
    Returns a list of charts as strings. 
    Also includes the difficulty label if `difficulty_labels` is True.
    """
    charts = sm.charts
    if difficulty_labels:
        return list(map((lambda c: c.difficulty + c.meter)), charts)
    else:
        return list(map((lambda c: c.difficulty), charts))
