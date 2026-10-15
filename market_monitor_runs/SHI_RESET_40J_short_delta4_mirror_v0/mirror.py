"""User-directed strict short4h-delta mirror; isolated research sensitivity."""
import numpy as np


def short_mirror(directions, features):
    result=directions.copy()
    for row in features.itertuples():
        i=int(row.signal_index)
        if result[i]<0 and not (row.window4_usable and np.isfinite(row.delta4_pct) and row.delta4_pct<0):
            result[i]=0
    return result
