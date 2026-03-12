"""
Generated TouchDesigner Extension for GeometricSymmetry
"""
import os
import sys
import numpy as np

# Ensure pyeyesweb is accessible
conda_lib_dir = "C:/Users/Nicola/miniconda3/envs/pwb/Lib/site-packages"
if conda_lib_dir not in sys.path:
    sys.path.insert(0, conda_lib_dir)

from pyeyesweb.low_level.geometric_symmetry import GeometricSymmetry


class GeometricSymmetryExt:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        
        self.joint_pairs = int(self.ownerComp.par.Jointpairs.eval())
        self.center_of_symmetry = int(self.ownerComp.par.Centerofsymmetry.eval())


        # Initialize PyEyesWeb Feature
        self.analyzer = GeometricSymmetry(joint_pairs=self.joint_pairs, center_of_symmetry=self.center_of_symmetry)


    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update parameters based on name
        param_handlers = {
            'Jointpairs': lambda v: (
                setattr(self, 'joint_pairs', int(v)),
                setattr(self.analyzer, 'joint_pairs', int(v))
            ),
            'Centerofsymmetry': lambda v: (
                setattr(self, 'center_of_symmetry', int(v)),
                setattr(self.analyzer, 'center_of_symmetry', int(v))
            ),

        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)
            
    def process_data(self):
        """
        Reads inputs, formats data for GeometricSymmetry, and computes the result.
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
