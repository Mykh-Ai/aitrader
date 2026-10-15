from pathlib import Path
import sys
import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parent))
from mirror import short_mirror


def test_strict_negative_boundary_zero_positive_and_unavailable():
    f=pd.DataFrame({"signal_index":range(6),"window4_usable":[True,True,True,True,True,False],
                    "delta4_pct":[-2.,-1e-10,0.,.04,np.nan,-2.]})
    d=-np.ones(6,dtype=int)
    np.testing.assert_array_equal(short_mirror(d,f),[-1,-1,0,0,0,0])
    np.testing.assert_array_equal(d,-np.ones(6,dtype=int))


def test_only_existing_short_candidates_are_changed():
    f=pd.DataFrame({"signal_index":[0,2,3,5],"window4_usable":[False,True,True,True],"delta4_pct":[np.nan,-2.,4.,2.]})
    d=np.array([1,0,0,-1,0,1])
    np.testing.assert_array_equal(short_mirror(d,f),[1,0,0,0,0,1])


def test_mirror_filter_is_prefix_invariant_without_any_outcome_columns():
    f=pd.DataFrame({"signal_index":range(4),"window4_usable":True,"delta4_pct":[2.,-2.,-1.,3.]})
    d=np.array([1,-1,-1,-1])
    np.testing.assert_array_equal(short_mirror(d,f)[:2],short_mirror(d[:2],f.iloc[:2]))
