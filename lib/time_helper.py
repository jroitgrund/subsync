from datetime import time


def time_from_millis(milliseconds):
    sec, milli = divmod(milliseconds, 1000)
    minutes, sec = divmod(sec, 60)
    hours, minutes = divmod(minutes, 60)
    return time(hours, minutes, sec, milli * 1000)
