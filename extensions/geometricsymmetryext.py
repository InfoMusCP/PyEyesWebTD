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

from pyeyesweb.low_level import GeometricSymmetry


class GeometricSymmetryExt:
    """
    GeometricSymmetry PyEyesWeb Extension
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
        # We read from the sequence parameter 'Jointpairs'
        self.pairs_enabled = []
        
        # Safely try to access the sequence
        seq_par = getattr(self.ownerComp.seq, 'Jointpairs', None)
        if seq_par is not None:
            for block in seq_par.blocks:
                left_par = getattr(block.par, 'Leftidx', None)
                right_par = getattr(block.par, 'Rightidx', None)
                if left_par is not None and right_par is not None:
                    try:
                        l_idx = int(float(left_par.eval()))
                        r_idx = int(float(right_par.eval()))
                        self.pairs_enabled.append((l_idx, r_idx))
                    except (ValueError, TypeError):
                        continue
        
        # Fallback to a single pair [0, 1] if none are configured
        if not self.pairs_enabled:
            self.pairs_enabled = [(0, 1)]

        self.center_idx = _safe_eval('Centeridx', 0, int)
        self.use_center = _safe_eval('Usecenter', True, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))

        center_param = self.center_idx if self.use_center else None

        self.feature = GeometricSymmetry(
            joint_pairs=self.pairs_enabled,
            center_of_symmetry=center_param
        )

    def _update_feature(self):
        pairs = []
        seq_par = getattr(self.ownerComp.seq, 'Jointpairs', None)
        
        if seq_par is not None:
            for block in seq_par.blocks:
                left_par = getattr(block.par, 'Leftidx', None)
                right_par = getattr(block.par, 'Rightidx', None)
                if left_par is not None and right_par is not None:
                    try:
                        pairs.append((int(float(left_par.eval())), int(float(right_par.eval()))))
                    except (ValueError, TypeError):
                        continue
                
        if not pairs:
            pairs = [(0, 1)]
            
        center = getattr(self, 'center_idx', 0) if getattr(self, 'use_center', True) else None
        
        # We must instantiate a new object if pairs change because validation occurs in __init__
        self.feature = GeometricSymmetry(joint_pairs=pairs, center_of_symmetry=center)

    def _build_parameters(self):
        page_name = "GeometricSymmetry"
        
        for page in self.ownerComp.customPages:
            if page.name == page_name:
                page.destroy()
                
        page = self.ownerComp.appendCustomPage(page_name)
        
        # --- Algorithm Tuning ---
        p = page.appendToggle("Usecenter", label="Use Specific Center Index")[0]
        p.default = True
        p.val = True

        p = page.appendInt("Centeridx", label="Center Joint Index")[0]
        p.default = 0
        p.val = 0
        p.min = 0
        p.normMax = 32
        
        # Build the Sequence parameter
        seq = page.appendSequence('Jointpairs', label='Joint Pairs')
        
        # We need to create the parameter template for the sequence blocks
        # TouchDesigner handles sequence params slightly differently
        p_l = page.appendInt('Leftidx', label='Left Index')[0]
        p_l.default = 0
        p_l.min = 0
        p_l.normMax = 32
        
        p_r = page.appendInt('Rightidx', label='Right Index')[0]
        p_r.default = 1
        p_r.min = 0
        p_r.normMax = 32
        
        # Explicitly tell TouchDesigner that the last 2 parameters belong to this Sequence Block
        self.ownerComp.seq.Jointpairs.blockSize = 2
        
        # Initialize with at least 1 pair block for UI convenience
        self.ownerComp.par.Jointpairs = 1

        print(f"[{self.ownerComp.name}] Custom Parameters Rebuilt Successfully.")

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        def set_use_center(v):
            self.use_center = bool(v)
            self._update_feature()

        def set_center(v):
            self.center_idx = int(float(v))
            self._update_feature()

        # Check if the changed parameter relates to our pairs definition
        # Sequence parameters generate names like Leftidx0, Leftidx1, Jointpairs, etc.
        if "jointpairs" in param_name.lower() or "leftidx" in param_name.lower() or "rightidx" in param_name.lower():
            self._update_feature()
        elif param_name == "Usecenter":
            set_use_center(param_value)
        elif param_name == "Centeridx":
            set_center(param_value)

    def ProcessCook(self, scriptOp):
        scriptOp.clear()
        
        # Expects physical coordinates (N_joints x 3)
        if len(scriptOp.inputs) == 0:
            return
            
        input_chop = scriptOp.inputs[0]
        if input_chop.numChans < 3:
            return
            
        tx = input_chop.chan('tx') or input_chop.chans()[0]
        ty = input_chop.chan('ty') or input_chop.chans()[1]
        tz = input_chop.chan('tz') or input_chop.chans()[2]
        
        # Shape: (n_joints, 3) representing the current frame
        frame_data = np.column_stack([tx.vals, ty.vals, tz.vals])

        results = self.feature.compute(frame_data)
        print(results)
        if getattr(results, 'is_valid', False):
            flat_results = results.to_flat_dict()
            for metric_name, value in flat_results.items():
                if value == value: # check nan
                    chan = scriptOp.appendChan(metric_name)
                    chan[0] = value
        return
