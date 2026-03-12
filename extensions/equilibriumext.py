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
        left_foot_idx = _safe_eval('Leftfootidx', 0, int)
        right_foot_idx = _safe_eval('Rightfootidx', 1, int)
        barycenter_idx = _safe_eval('Barycenteridx', 2, int)
        margin_mm = _safe_eval('Marginmm', 100.0, float)
        y_weight = _safe_eval('Yweight', 0.5, float)

        self.feature = Equilibrium(
            left_foot_idx=left_foot_idx,
            right_foot_idx=right_foot_idx,
            barycenter_idx=barycenter_idx,
            margin_mm=margin_mm,
            y_weight=y_weight
        )
        
        # Equilibrium is a StaticFeature (per-frame point cloud analysis).
        # No SlidingWindow is instantiated.

    def _build_parameters(self):
        page_name = "Equilibrium"
        
        for page in self.ownerComp.customPages:
            if page.name == page_name:
                page.destroy()
                
        page = self.ownerComp.appendCustomPage(page_name)
        
        # --- Algorithm Tuning ---
        p = page.appendInt("Leftfootidx", label="Left Foot Joint Index")[0]
        p.default = 0
        p.val = 0
        p.min = 0
        p.normMax = 32
        
        p = page.appendInt("Rightfootidx", label="Right Foot Joint Index")[0]
        p.default = 1
        p.val = 1
        p.min = 0
        p.normMax = 32
        
        p = page.appendInt("Barycenteridx", label="Barycenter Joint Index")[0]
        p.default = 2
        p.val = 2
        p.min = 0
        p.normMax = 32
        
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
        
        print(f"[{self.ownerComp.name}] Custom Parameters Rebuilt Successfully.")

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        param_handlers = {
            "Leftfootidx": lambda v: setattr(self.feature, 'left_foot_idx', int(float(v))),
            "Rightfootidx": lambda v: setattr(self.feature, 'right_foot_idx', int(float(v))),
            "Barycenteridx": lambda v: setattr(self.feature, 'barycenter_idx', int(float(v))),
            "Marginmm": lambda v: setattr(self.feature, 'margin', float(v)),
            "Yweight": lambda v: setattr(self.feature, 'y_weight', float(v))
        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def ProcessCook(self, scriptOp):
        scriptOp.clear()
        
        # This feature operates on a point cloud natively (n_joints, 2) minimum 
        # so we expect 2 or 3 incoming CHOP channels (tx, ty, tz) representing spatial data for the current frame.
        if len(scriptOp.inputs) == 0:
            return
            
        input_chop = scriptOp.inputs[0]
        if input_chop.numChans < 2:
            return
            
        # Reconstruct spatial structure
        tx = input_chop.chan('tx') or input_chop.chans()[0]
        ty = input_chop.chan('ty') or input_chop.chans()[1]
        
        # Shape: (n_joints, 2+) representing the current frame
        frame_data = np.column_stack([tx.vals, ty.vals])

        results = self.feature.compute(frame_data)
        
        val_chan = scriptOp.appendChan('equilibrium_value')
        val = results.value if hasattr(results, 'value') else None
        val_chan[0] = val if val is not None else 0.0
        
        ang_chan = scriptOp.appendChan('equilibrium_angle')
        ang = results.angle if hasattr(results, 'angle') else None
        ang_chan[0] = ang if ang is not None else 0.0

        return
