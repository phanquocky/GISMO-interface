# encoding: utf-8
"""
@author: anna
@contact: latour@nus.edu.sg
@time: 7/19/22 10:07 AM
@file: timer.py
@desc: Copied from https://realpython.com/python-timer/#python-timers.
"""

import time

class TimerError(Exception):
    """A custom exception Used to report errors in use of Timer class."""

class WallclockTimer:
    """
    Records wall-clock time, including when the program is sleeping.
    """
    def __init__(self, text="Elapsed time: {0:.4f} CPU seconds."):
        self._start_time = None
        self.text = text

    def start(self):
        """Start a new timer."""
        if self._start_time is not None:
            raise TimerError("Timer is running. Use .stop() to stop it.")

        self._start_time = time.perf_counter()

    def stop(self):
        """Stop the timer, and report the elapsed time."""
        if self._start_time is None:
            raise TimerError("Timer is not running. Use .start() to start the timer.")

        elapsed_time = time.perf_counter() - self._start_time
        self._start_time = None
        return self.text.format(elapsed_time)


class ProcessTimer:
    """
    Records CPU time (user + process), hence excluding the time that the process
    is sleeping.
    """
    def __init__(self, text="Elapsed time: {0:.4f} CPU seconds."):
        self._start_time = None
        self.text = text

    def start(self):
        """Start a new timer."""
        if self._start_time is not None:
            raise TimerError("Timer is running. Use .stop() to stop it.")

        self._start_time = time.process_time()

    def stop(self):
        """Stop the timer, and report the elapsed time."""
        if self._start_time is None:
            raise TimerError("Timer is not running. Use .start() to start the timer.")

        elapsed_time = time.process_time() - self._start_time
        self._start_time = None
        return self.text.format(elapsed_time)