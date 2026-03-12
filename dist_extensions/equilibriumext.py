"""
Generated TouchDesigner Extension for Equilibrium
"""
import os
import sys
import numpy as np

# Ensure pyeyesweb is accessible
conda_lib_dir = "C:/Users/Nicola/miniconda3/envs/pwb/Lib/site-packages"
if conda_lib_dir not in sys.path:
    sys.path.insert(0, conda_lib_dir)

from pyeyesweb.low_level.equilibrium import Equilibrium


class EquilibriumExt:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        
        self.left_foot_idx = int(self.ownerComp.par.Leftfootidx.eval())
        self.right_foot_idx = int(self.ownerComp.par.Rightfootidx.eval())
        self.barycenter_idx = int(self.ownerComp.par.Barycenteridx.eval())
        self.margin_mm = float(self.ownerComp.par.Marginmm.eval())
        self.y_weight = float(self.ownerComp.par.Yweight.eval())


        # Initialize PyEyesWeb Feature
        self.analyzer = Equilibrium(left_foot_idx=self.left_foot_idx, right_foot_idx=self.right_foot_idx, barycenter_idx=self.barycenter_idx, margin_mm=self.margin_mm, y_weight=self.y_weight)


    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update parameters based on name
        param_handlers = {
            'Leftfootidx': lambda v: (
                setattr(self, 'left_foot_idx', int(v)),
                setattr(self.analyzer, 'left_foot_idx', int(v))
            ),
            'Rightfootidx': lambda v: (
                setattr(self, 'right_foot_idx', int(v)),
                setattr(self.analyzer, 'right_foot_idx', int(v))
            ),
            'Barycenteridx': lambda v: (
                setattr(self, 'barycenter_idx', int(v)),
                setattr(self.analyzer, 'barycenter_idx', int(v))
            ),
            'Marginmm': lambda v: (
                setattr(self, 'margin_mm', float(v)),
                setattr(self.analyzer, 'margin_mm', float(v))
            ),
            'Yweight': lambda v: (
                setattr(self, 'y_weight', float(v)),
                setattr(self.analyzer, 'y_weight', float(v))
            ),

        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)
            
    def process_data(self):
        """
        Reads inputs, formats data for Equilibrium, and computes the result.
        """
        chop_in = self.ownerComp.op('in_1')
        if not chop_in or chop_in.numChans == 0:
            return None

        # 2D Array formatting: grouping channels by 3 (X,Y,Z)
        vals = [c.eval() for c in chop_in.chans()]
        # Assuming 3 CHOP channels per joint (tx, ty, tz)
        num_joints = len(vals) // 3
        vals = np.array(vals).reshape(num_joints, 3) if num_joints > 0 else np.array(vals)
        return self.analyzer.compute(vals)
        return None
