#!/usr/bin/env python

import os
import math
import random

def almost_equal(x, y,
        proportional_tolerance = 1e-6):
    abs_tol = max(math.fabs(x), math.fabs(y)) * proportional_tolerance
    diff = math.fabs(x - y)
    if (diff > abs_tol):
        return False
    return True

def get_safe_seed(rng = None):
    """
    Get a random seed (int) between 0 and 2^31, which is safe to write and read
    across systems and is safe for seeding numpy (which must be between 0 and
    2^32-1).

    Parameters
    ----------
    rng : `random.Random` object
        An instance of a `random.Random` object

    Returns
    -------
    int
        A random integer from the range 1 to 2^31-1 (inclusive)
    """
    if not rng:
        return random.randint(1, (2**31)-1)
    return rng.randint(1, (2**31)-1)

def get_safe_seeds(rng, n):
    return (get_safe_seed(rng) for _ in range(n))

def get_numpy_rng(self, seed = None):
    import numpy as np
    if seed is None:
        return np.random.default_rng()
    return np.random.default_rng(seed)

def arg_is_dir_or_new_dir(path):
    """
    Returns the passed string if it is a valid path to a directory, or its
    parent is a valid directory. Otherwise raises an `ArgumentTypeError`.

    Examples
    --------
    >>> d = os.path.abspath(os.path.dirname(__file__))
    >>> returned = arg_is_dir_or_new_dir(d)
    >>> returned == d
    True
    >>> new_dir = os.path.join(d, "probably-not-a-dir-in-this-dir")
    >>> returned = arg_is_dir_or_new_dir(new_dir)
    >>> returned == new_dir
    True
    """
    if os.path.isdir(path):
        return path
    elif os.path.exists(path):
        msg = 'path {0!r} exists but is not a directory'.format(path)
    elif os.path.sep not in path:
        # just dir name which can be created in working dir with mkdir
        return path
    elif os.path.isdir(os.path.dirname(path)):
        # path doesn't exist, but is in an existing parent directory
        return path
    else:
        msg = '{0!r} is not a directory nor is its parent'.format(path)
    raise argparse.ArgumentTypeError(msg)
