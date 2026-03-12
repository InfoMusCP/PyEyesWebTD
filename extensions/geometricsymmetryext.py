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
        # TD UI doesn't natively do lists of tuples well without DATs, so we expose up to 4 pairs 
        # as a pragmatic UI choice for a basic character skeleton
        
        self.pairs_enabled = []
        for i in range(1, 5):
            en = _safe_eval(f'Enablepair{i}', False, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))
            l_idx = _safe_eval(f'Leftidx{i}', 0, int)
            r_idx = _safe_eval(f'Rightidx{i}', 1, int)
            if en:
                self.pairs_enabled.append((l_idx, r_idx))
                
        # Fallback to a single pair [0, 1] if none are enabled to satisfy validation
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
        for i in range(1, 5):
            par_en = getattr(self.ownerComp.par, f'Enablepair{i}')
            par_l = getattr(self.ownerComp.par, f'Leftidx{i}')
            par_r = getattr(self.ownerComp.par, f'Rightidx{i}')
            
            if par_en is not None and par_en.eval():
                pairs.append((int(par_l.eval()), int(par_r.eval())))
                
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
        
        # Build 4 pairs
        for i in range(1, 5):
            p_en = page.appendToggle(f"Enablepair{i}", label=f"Enable Pair {i}")[0]
            p_en.default = (i == 1)
            p_en.val = (i == 1)
            
            p_l = page.appendInt(f"Leftidx{i}", label=f"Left Index {i}")[0]
            p_l.default = 0
            p_l.val = 0
            p_l.min = 0
            p_l.normMax = 32
            
            p_r = page.appendInt(f"Rightidx{i}", label=f"Right Index {i}")[0]
            p_r.default = 1
            p_r.val = 1
            p_r.min = 0
            p_r.normMax = 32

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
        if "pair" in param_name.lower() or "idx" in param_name.lower():
            if param_name == "Usecenter":
                set_use_center(param_value)
            elif param_name == "Centeridx":
                set_center(param_value)
            else:
                self._update_feature()

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

        try:
            results = self.feature.compute(frame_data)
        except Exception:
            return
        
        if getattr(results, 'is_valid', False):
            flat_results = results.to_flat_dict()
            for metric_name, value in flat_results.items():
                if value == value: # check nan
                    chan = scriptOp.appendChan(metric_name)
                    chan[0] = value
        return
