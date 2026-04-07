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

from pyeyesweb.low_level import KineticEnergy


class KineticEnergyExt:
    """
    KineticEnergy PyEyesWeb Extension
    """

    def __init__(self, ownerComp):
        self.ownerComp = ownerComp

        par_weights = getattr(self.ownerComp.par, 'Weights', None)
        if par_weights is not None:
            weights_val = self._parse_weights_str(par_weights.eval())
        else:
            weights_val = 1.0
            
        self.feature = KineticEnergy(weights=weights_val)

    @staticmethod
    def _parse_weights_str(val):
        if not isinstance(val, str):
            val = str(val)
        try:
            parts = [float(x.strip()) for x in val.split(',') if x.strip()]
            if len(parts) == 1:
                return parts[0]
            elif len(parts) > 1:
                return parts
        except ValueError:
            pass
        return 1.0

    def _build_parameters(self):
        page_name = "KineticEnergy"
        
        for page in self.ownerComp.customPages:
            if page.name == page_name:
                page.destroy()
                
        page = self.ownerComp.appendCustomPage(page_name)
        
        # --- Algorithm Tuning ---
        p = page.appendStr("Weights", label="Mass/Weights (Comma separated)")[0]
        p.default = "1.0"
        p.val = "1.0"
        
        print(f"[{self.ownerComp.name}] Custom Parameters Rebuilt Successfully.")

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        param_handlers = {
            "Weights": lambda v: setattr(self.feature, 'weights', self._parse_weights_str(v))
        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def ProcessCook(self, scriptOp):
        scriptOp.clear()
        
        # Expects physical VELOCITIES (n_joints x dims)
        if len(scriptOp.inputs) == 0:
            return
            
        input_chop = scriptOp.inputs[0]
        if input_chop.numChans == 0:
            return
            
        # Dynamically reshape incoming signals into (n_joints, N_dims)
        # Assuming channels are structured sequentially like tx0, ty0, tz0, tx1, ty1, tz1 or similar
        # Since TD CHOPs are (N_Channels, Samples) we'll just parse the flat sample array of this frame
        # We assume 3D data by default. If input channels < 3 it just passes safely to KD logic.
        
        num_chans = input_chop.numChans
        dims = 3 if num_chans % 3 == 0 else (2 if num_chans % 2 == 0 else 1)
        num_joints = num_chans // dims
        
        if num_joints == 0:
            return

        # Check weight list length against incoming joints to provide user feedback
        if isinstance(self.feature.weights, np.ndarray) and self.feature.weights.shape[0] != num_joints:
            scriptOp.addWarning(f"Weight list length ({self.feature.weights.shape[0]}) does not match number of incoming joints ({num_joints}).")
            return

        frame_data = np.zeros((num_joints, dims))
        for j in range(num_joints):
            for d in range(dims):
                idx = j * dims + d
                if idx < num_chans:
                    chan = input_chop.chans()[idx]
                    frame_data[j, d] = chan[0]

        try:
            results = self.feature.compute(frame_data)
        except ValueError as e:
            scriptOp.addWarning(str(e))
            return
            
        if getattr(results, 'is_valid', False):
            flat_results = results.to_flat_dict()
            for metric_name, value in flat_results.items():
                if value == value: # check nan
                    chan = scriptOp.appendChan(metric_name)
                    chan[0] = value
        return
