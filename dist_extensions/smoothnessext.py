"""
Generated TouchDesigner Extension for Smoothness
"""
import os
import sys
import numpy as np

# Ensure pyeyesweb is accessible
conda_lib_dir = "C:/Users/Nicola/miniconda3/envs/pwb/Lib/site-packages"
if conda_lib_dir not in sys.path:
    sys.path.insert(0, conda_lib_dir)

from pyeyesweb.low_level.smoothness import Smoothness
from pyeyesweb.data_models.sliding_window import SlidingWindow

class SmoothnessExt:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        
        self.sliding_window_length = int(self.ownerComp.par.Slidingwindowlength.eval())
        self.rate_hz = float(self.ownerComp.par.Ratehz.eval())
        self.use_filter = bool(self.ownerComp.par.Usefilter.eval())
        self.metrics = str(self.ownerComp.par.Metrics.eval())


        # Initialize PyEyesWeb Feature
        self.analyzer = Smoothness(rate_hz=self.rate_hz, use_filter=self.use_filter, metrics=self.metrics)

        self.sliding_window = SlidingWindow(max_length=self.sliding_window_length, n_columns=1) # TODO shape

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update parameters based on name
        param_handlers = {
            'Slidingwindowlength': lambda v: setattr(self, 'sliding_window_length', int(v)),
            'Ratehz': lambda v: (
                setattr(self, 'rate_hz', float(v)),
                setattr(self.analyzer, 'rate_hz', float(v))
            ),
            'Usefilter': lambda v: (
                setattr(self, 'use_filter', bool(v)),
                setattr(self.analyzer, 'use_filter', bool(v))
            ),
            'Metrics': lambda v: (
                setattr(self, 'metrics', str(v)),
                setattr(self.analyzer, 'metrics', str(v))
            ),

        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)
            
    def process_data(self):
        """
        Reads inputs, formats data for Smoothness, and computes the result.
        """
        chop_in = self.ownerComp.op('in_1')
        if not chop_in or chop_in.numChans == 0:
            return None

        # 1D Array (Single channel speed/value)
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
