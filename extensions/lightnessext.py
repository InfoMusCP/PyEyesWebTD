"""
Extension classes enhance TouchDesigner components with python.
"""
import os
import sys

from TDStoreTools import StorageManager
import TDFunctions as TDF

parent_dir = os.path.dirname(project.folder)
lib_dir = os.path.join(project.folder, "pyeyesweb_env", "Lib", "site-packages")

if lib_dir not in sys.path:
    sys.path.insert(0, os.path.normpath(lib_dir))

from pyeyesweb.mid_level import Lightness
from pyeyesweb.data_models import SlidingWindow


class LightnessExt:
    """
    Lightness PyEyesWeb Extension
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

        self.sliding_window_max_length = _safe_eval('Slidingwindowmaxlength', 60, int)

        # Get metrics based on toggles
        self.compute_lightness = _safe_eval('Computelightness', True, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))
        self.compute_index = _safe_eval('Computeindex', False, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))

        # Map initialization parameters
        alpha = _safe_eval('Alpha', 0.5, float)

        self.feature = Lightness(alpha=alpha)
        # Needs velocity data
        self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=3)

    def _build_parameters(self):
        page_name = "Lightness"
        
        for page in self.ownerComp.customPages:
            if page.name == page_name:
                page.destroy()
                
        page = self.ownerComp.appendCustomPage(page_name)
        
        # --- Output Selection ---
        p = page.appendToggle("Computelightness", label="Output Lightness")[0]
        p.default = True
        p.val = True
        
        p = page.appendToggle("Computeindex", label="Output Weight Index")[0]
        p.default = False
        p.val = False
        
        # --- Sensor/Stream Config ---
        p = page.appendInt("Slidingwindowmaxlength", label="Window Size (samples)")[0]
        p.default = 60
        p.val = 60
        p.min = 10
        p.normMax = 300
        
        # --- Algorithm Tuning ---
        p = page.appendFloat("Alpha", label="Rarity Alpha Weight")[0]
        p.default = 0.5
        p.val = 0.5
        p.min = 0.01
        p.normMax = 1.0
        
        print(f"[{self.ownerComp.name}] Custom Parameters Rebuilt Successfully.")

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        param_handlers = {
            "Slidingwindowmaxlength": lambda v: (
                setattr(self, 'sliding_window_max_length', int(float(v))),
                setattr(self.sliding_window, 'max_length', int(float(v)))
            ),
            "Computelightness": lambda v: setattr(self, 'compute_lightness', bool(v)),
            "Computeindex": lambda v: setattr(self, 'compute_index', bool(v)),
            "Alpha": lambda v: setattr(self.feature, 'alpha', float(v))
        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def ProcessCook(self, scriptOp):
        scriptOp.clear()
        
        signals = []
        for i_chop in scriptOp.inputs:
            for chan in i_chop.chans():
                signals.append(chan[0])

        if len(signals) < 3: # 3D Velocity usually expected
            return
            
        dims = 3 if len(signals) % 3 == 0 else (2 if len(signals) % 2 == 0 else 1)
        expected_signals = len(signals) // dims

        if expected_signals != self.sliding_window.n_signals or dims != self.sliding_window.n_dims:
            self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=expected_signals, n_dims=dims)

        self.sliding_window.append(signals)

        results = self.feature(self.sliding_window)
        
        if getattr(self, 'compute_lightness', False):
            val = results.lightness if hasattr(results, 'lightness') else None
            chan = scriptOp.appendChan('lightness')
            chan[0] = val if val is not None else 0.0
            
        if getattr(self, 'compute_index', False):
            val = results.latest_weight_index if hasattr(results, 'latest_weight_index') else None
            chan = scriptOp.appendChan('weight_index')
            chan[0] = val if val is not None else 0.0

        return
