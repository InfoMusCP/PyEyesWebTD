"""
Extension classes enhance TouchDesigner components with python.
"""
import os
import sys
import numpy as np

from TDStoreTools import StorageManager
import TDFunctions as TDF

parent_dir = os.path.dirname(project.folder)
lib_dir = os.path.join(project.folder, "pyeyesweb_env", "Lib", "site-packages")

if lib_dir not in sys.path:
    sys.path.insert(0, os.path.normpath(lib_dir))

from pyeyesweb.low_level import Equilibrium


class EquilibriumExt:
    """
    Equilibrium PyEyesWeb Extension
    """

    def __init__(self, ownerComp):
        self.ownerComp = ownerComp

        def _safe_eval(par_name, default_val, expected_type):
            par = getattr(self.ownerComp.par, par_name, None)
            if par is not None:
                val = par.eval()
                if val == '' or val is None:
                    par.val = default_val
                    return default_val
                try:
                    result = expected_type(val)
                    if result == 0 and default_val != 0:
                        par.val = default_val
                        return default_val
                    return result
                except (ValueError, TypeError):
                    pass
            return default_val

        # Map initialization parameters
        margin_mm = _safe_eval('Marginmm', 100.0, float)
        y_weight = _safe_eval('Yweight', 0.5, float)
        axis1 = _safe_eval('Axis1', 0, int)
        axis2 = _safe_eval('Axis2', 1, int)

        self.feature = Equilibrium(
            left_foot_idx=0,
            right_foot_idx=1,
            barycenter_idx=2,
            margin_mm=margin_mm,
            y_weight=y_weight,
            axes=(axis1, axis2)
        )

    def _build_parameters(self):
        page_name = "Equilibrium"
        
        for page in self.ownerComp.customPages:
            if page.name == page_name:
                page.destroy()
                
        page = self.ownerComp.appendCustomPage(page_name)
        
        # --- Algorithm Tuning ---
        
        p = page.appendFloat("Marginmm", label="Margin (mm)")[0]
        p.default = 100.0
        p.val = 100.0
        p.min = 0.0
        p.normMax = 500.0
        
        p = page.appendFloat("Yweight", label="Y Weight")[0]
        p.default = 0.5
        p.val = 0.5
        p.min = 0.01
        p.normMax = 2.0

        p = page.appendInt("Axis1", label="First Axis (0=X, 1=Y, 2=Z)")[0]
        p.default = 0
        p.val = 0
        p.min = 0
        p.normMax = 2

        p = page.appendInt("Axis2", label="Second Axis (0=X, 1=Y, 2=Z)")[0]
        p.default = 1
        p.val = 1
        p.min = 0
        p.normMax = 2
        
        print(f"[{self.ownerComp.name}] Custom Parameters Rebuilt Successfully.")

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        param_handlers = {
            "Marginmm": lambda v: setattr(self.feature, 'margin', float(v)),
            "Yweight": lambda v: setattr(self.feature, 'y_weight', float(v)),
            "Axis1": lambda v: setattr(self.feature, 'axes', (int(v), self.feature.axes[1])),
            "Axis2": lambda v: setattr(self.feature, 'axes', (self.feature.axes[0], int(v)))
        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def ProcessCook(self, scriptOp):
        scriptOp.clear()
        
        # This feature operates on 3 points natively (left foot, right foot, barycenter)
        if len(scriptOp.inputs) != 3:
            return
            
        points = []
        for input_chop in scriptOp.inputs:
            arr = input_chop.numpyArray()
            if arr.shape[1] == 0:
                return
                
            # Extract first sample of all available dimensions
            pt = arr[:, 0]
            points.append(pt)
            
        # Ensure points have exactly the same number of dimensions by trimming to the min dimension
        min_dim = min(len(p) for p in points) if points else 0
        if min_dim < 2:
            return
            
        frame_data = np.array([p[:min_dim] for p in points])

        # Ensure we have enough dimensions for the selected axes
        max_axis = max(self.feature.axes)
        if frame_data.shape[1] <= max_axis:
            return

        results = self.feature.compute(frame_data)
        
        # Determine validness
        is_valid = getattr(results, 'is_valid', True)
        
        if not is_valid:
            # Clear if not valid
            return

        if not scriptOp.isTimeSlice:
            scriptOp.numSamples = 1

        val_chan = scriptOp.appendChan('equilibrium_value')
        ang_chan = scriptOp.appendChan('equilibrium_angle')
        
        val = results.value if hasattr(results, 'value') else 0.0
        ang = results.angle if hasattr(results, 'angle') else 0.0
        
        val_float = float(val) if val is not None else 0.0
        ang_float = float(ang) if ang is not None else 0.0
        
        for i in range(scriptOp.numSamples):
            val_chan[i] = val_float
            ang_chan[i] = ang_float

        return
