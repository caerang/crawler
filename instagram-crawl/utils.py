# Copyright 2019, Hyeongdo Lee. All Rights Reserved.
# 
# e-mail: mylovercorea@gmail.com
#
# ==============================================================================
"""
"""
from time import sleep
import random
from functools import wraps
from exceptions import RetryException


def retry(attempt=10, wait=0.3):
    def wrap(func):
        @wraps(func)
        def wrapped_f(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except RetryException:
                if attempt > 1:
                    sleep(wait)
                    return retry(attempt - 1, wait)(func)(*args, **kwargs)
                else:
                    exc = RetryException()
                    exc.__cause__ = None
                    raise exc
        return wrapped_f
    return wrap


def randomized_sleep(average=1):
    _min, _max = average * 1/2, average * 3/2
    sleep(random.uniform(_min, _max))
