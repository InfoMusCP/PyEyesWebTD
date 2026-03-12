"""
Generated TouchDesigner Extension for MultiScaleEntropyDominance
"""
import os
import sys
import numpy as np

# Ensure pyeyesweb is accessible
conda_lib_dir = "C:/Users/Nicola/miniconda3/envs/pwb/Lib/site-packages"
if conda_lib_dir not in sys.path:
    sys.path.insert(0, conda_lib_dir)

from pyeyesweb.analysis_primitives.mse_dominance import MultiScaleEntropyDominance
from pyeyesweb.data_models.sliding_window import SlidingWindow

class MultiScaleEntropyDominanceExt:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        
        self.sliding_window_length = int(self.ownerComp.par.Slidingwindowlength.eval())
        self.m = float(self.ownerComp.par.M.eval())
        self.r = float(self.ownerComp.par.R.eval())
        self.max_scale = float(self.ownerComp.par.Maxscale.eval())
        self.min_points = float(self.ownerComp.par.Minpoints.eval())
        self.methods = str(self.ownerComp.par.Methods.eval())


        # Initialize PyEyesWeb Feature
        self.analyzer = MultiScaleEntropyDominance(m=self.m, r=self.r, max_scale=self.max_scale, min_points=self.min_points, methods=self.methods)

        self.sliding_window = SlidingWindow(max_length=self.sliding_window_length, n_columns=1) # TODO shape

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update parameters based on name
        param_handlers = {
            'Slidingwindowlength': lambda v: setattr(self, 'sliding_window_length', int(v)),
            'M': lambda v: (
                setattr(self, 'm', float(v)),
                setattr(self.analyzer, 'm', float(v))
            ),
            'R': lambda v: (
                setattr(self, 'r', float(v)),
                setattr(self.analyzer, 'r', float(v))
            ),
            'Maxscale': lambda v: (
                setattr(self, 'max_scale', float(v)),
                setattr(self.analyzer, 'max_scale', float(v))
            ),
            'Minpoints': lambda v: (
                setattr(self, 'min_points', float(v)),
                setattr(self.analyzer, 'min_points', float(v))
            ),
            'Methods': lambda v: (
                setattr(self, 'methods', str(v)),
                setattr(self.analyzer, 'methods', str(v))
            ),

        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)
            
    def process_data(self):
        """
        Reads inputs, formats data for MultiScaleEntropyDominance, and computes the result.
        """
        chop_in = self.ownerComp.op('in_1')
        if not chop_in or chop_in.numChans == 0:
            return None

        # 2D Array of Features. Each CHOP channel is a feature.
        vals = [c.eval() for c in chop_in.chans()]
        self.sliding_window.append([vals])
        if self.sliding_window.is_full():
            # Some features expect pure numpy array, some expect SlidingWindow object.
            # PyEyesweb typically accepts numpy array through compute(), or SlidingWindow through __call__().
            try:
                return self.analyzer.compute(self.sliding_window.to_array()[0])
            except:
                return self.analyzer(self.sliding_window)
        return None
