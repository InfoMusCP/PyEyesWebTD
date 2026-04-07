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

from pyeyesweb.mid_level import Suddenness
from pyeyesweb.data_models import SlidingWindow


class SuddennessExt:
    """
    Suddenness PyEyesWeb Extension
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
        self.compute_is_sudden = _safe_eval('Computeissudden', True, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))
        self.compute_alpha = _safe_eval('Computealpha', False, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))
        self.compute_beta = _safe_eval('Computebeta', False, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))
        self.compute_gamma = _safe_eval('Computegamma', False, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))

        # Map initialization parameters
        algos = ["new", "old"]
        algo_idx = _safe_eval('Algo', 0, int)
        algo = algos[max(0, min(algo_idx, len(algos)-1))]

        self.feature = Suddenness(algo=algo)
        # Assuming typical 3D incoming movement tracking (tx,ty,tz)
        self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=3)

    def _build_parameters(self):
        page_name = "Suddenness"
        
        for page in self.ownerComp.customPages:
            if page.name == page_name:
                page.destroy()
                
        page = self.ownerComp.appendCustomPage(page_name)
        
        # --- Output Selection ---
        p = page.appendToggle("Computeissudden", label="Output Is Sudden")[0]
        p.default = True
        p.val = True
        
        p = page.appendToggle("Computealpha", label="Output Alpha Value")[0]
        p.default = False
        p.val = False

        p = page.appendToggle("Computebeta", label="Output Beta Value")[0]
        p.default = False
        p.val = False

        p = page.appendToggle("Computegamma", label="Output Gamma Value")[0]
        p.default = False
        p.val = False
        
        # --- Sensor/Stream Config ---
        p = page.appendInt("Slidingwindowmaxlength", label="Window Size (samples)")[0]
        p.default = 60
        p.val = 60
        p.min = 10
        p.normMax = 300
        
        # --- Algorithm Tuning ---
        p = page.appendMenu("Algo", label="Stable Distribution Algorithm")[0]
        p.menuNames = ["new", "old"]
        p.menuLabels = ["New Method (Constrained)", "Old Method"]
        p.default = 0
        p.val = 0
        
        print(f"[{self.ownerComp.name}] Custom Parameters Rebuilt Successfully.")

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        param_handlers = {
            "Slidingwindowmaxlength": lambda v: (
                setattr(self, 'sliding_window_max_length', int(float(v))),
                setattr(self.sliding_window, 'max_length', int(float(v)))
            ),
            "Computeissudden": lambda v: setattr(self, 'compute_is_sudden', bool(v)),
            "Computealpha": lambda v: setattr(self, 'compute_alpha', bool(v)),
            "Computebeta": lambda v: setattr(self, 'compute_beta', bool(v)),
            "Computegamma": lambda v: setattr(self, 'compute_gamma', bool(v)),
            "Algo": lambda v: setattr(self.feature, 'algo', ["new", "old"][int(float(v))])
        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def ProcessCook(self, scriptOp):
        scriptOp.clear()
        
        signals = []
        for i_chop in scriptOp.inputs:
            for chan in i_chop.chans():
                signals.append(chan[0])

        if len(signals) == 0:
            return
            
        dims = 3 if len(signals) % 3 == 0 else (2 if len(signals) % 2 == 0 else 1)
        expected_signals = len(signals) // dims

        if expected_signals != self.sliding_window.n_signals or dims != self.sliding_window.n_dims:
            self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=expected_signals, n_dims=dims)

        self.sliding_window.append(signals)

        results = self.feature(self.sliding_window)
        
        if getattr(self, 'compute_is_sudden', False):
            val = results.is_sudden if hasattr(results, 'is_sudden') else False
            chan = scriptOp.appendChan('is_sudden')
            chan[0] = 1.0 if val else 0.0
            
        if getattr(self, 'compute_alpha', False):
            val = results.alpha if hasattr(results, 'alpha') else None
            chan = scriptOp.appendChan('alpha')
            chan[0] = val if val is not None else 0.0

        if getattr(self, 'compute_beta', False):
            val = results.beta if hasattr(results, 'beta') else None
            chan = scriptOp.appendChan('beta')
            chan[0] = val if val is not None else 0.0

        if getattr(self, 'compute_gamma', False):
            val = results.gamma if hasattr(results, 'gamma') else None
            chan = scriptOp.appendChan('gamma')
            chan[0] = val if val is not None else 0.0

        return
