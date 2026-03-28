#!/usr/bin/env python

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
