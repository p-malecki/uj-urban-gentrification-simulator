import numpy as np

def gini_coefficient(x):
    x = np.asarray(x, dtype=np.float64)
    if np.amin(x) < 0:
        x -= np.amin(x)
    x += 0.0000001
    x = np.sort(x)
    index = np.arange(1, x.shape[0] + 1)
    n = x.shape[0]
    return (np.sum((2 * index - n - 1) * x)) / (n * np.sum(x))
