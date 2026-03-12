"""
Generated TouchDesigner Extension for Impulsivity
"""
import os
import sys
import numpy as np

# Ensure pyeyesweb is accessible
conda_lib_dir = "C:/Users/Nicola/miniconda3/envs/pwb/Lib/site-packages"
if conda_lib_dir not in sys.path:
    sys.path.insert(0, conda_lib_dir)

from pyeyesweb.mid_level.impulsivity import Impulsivity
from pyeyesweb.data_models.sliding_window import SlidingWindow

class ImpulsivityExt:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        
        self.sliding_window_length = int(self.ownerComp.par.Slidingwindowlength.eval())
        self.direction_change_epsilon = float(self.ownerComp.par.Directionchangeepsilon.eval())
        self.suddenness_algo = str(self.ownerComp.par.Suddennessalgo.eval())


        # Initialize PyEyesWeb Feature
        self.analyzer = Impulsivity(direction_change_epsilon=self.direction_change_epsilon, suddenness_algo=self.suddenness_algo)

        self.sliding_window = SlidingWindow(max_length=self.sliding_window_length, n_columns=1) # TODO shape

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update parameters based on name
        param_handlers = {
            'Slidingwindowlength': lambda v: setattr(self, 'sliding_window_length', int(v)),
            'Directionchangeepsilon': lambda v: (
                setattr(self, 'direction_change_epsilon', float(v)),
                setattr(self.analyzer, 'direction_change_epsilon', float(v))
            ),
            'Suddennessalgo': lambda v: (
                setattr(self, 'suddenness_algo', str(v)),
                setattr(self.analyzer, 'suddenness_algo', str(v))
            ),

        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)
            
    def process_data(self):
        """
        Reads inputs, formats data for Impulsivity, and computes the result.
        """
        chop_in = self.ownerComp.op('in_1')
        if not chop_in or chop_in.numChans == 0:
            return None

        # 3D Array of (Time, Signals, Dims). We assume incoming CHOP is (Signals * Dims).
        vals = [c.eval() for c in chop_in.chans()]
        num_joints = len(vals) // 3
        # Reshape to (N_joints, 3) for the current frame
        vals = np.array(vals).reshape(num_joints, 3) if num_joints > 0 else np.array(vals)
        self.sliding_window.append([vals])
        if self.sliding_window.is_full():
            # Some features expect pure numpy array, some expect SlidingWindow object.
            # PyEyesweb typically accepts numpy array through compute(), or SlidingWindow through __call__().
            try:
                return self.analyzer.compute(self.sliding_window.to_array()[0])
            except:
                return self.analyzer(self.sliding_window)
        return None
