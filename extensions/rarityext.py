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

from pyeyesweb.analysis_primitives import Rarity
from pyeyesweb.data_models import SlidingWindow


class RarityExt:
    """
    Rarity PyEyesWeb Extension
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
        alpha = _safe_eval('Alpha', 0.5, float)

        self.feature = Rarity(alpha=alpha)
        self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=1)

    def _build_parameters(self):
        page_name = "Rarity"
        
        for page in self.ownerComp.customPages:
            if page.name == page_name:
                page.destroy()
                
        page = self.ownerComp.appendCustomPage(page_name)
        
        # --- Sensor/Stream Config ---
        p = page.appendInt("Slidingwindowmaxlength", label="Window Size (samples)")[0]
        p.default = 60
        p.val = 60
        p.min = 10
        p.normMax = 300
        
        # --- Algorithm Tuning ---
        p = page.appendFloat("Alpha", label="Alpha Weight")[0]
        p.default = 0.5
        p.val = 0.5
        p.min = 0.0
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
            "Alpha": lambda v: setattr(self.feature, 'alpha', float(v))
        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def ProcessCook(self, scriptOp):
        scriptOp.clear()
        inputs = scriptOp.inputs[0]
        series1 = inputs[0]

        self.sliding_window.append([series1])

        results = self.feature(self.sliding_window)
        
        chan = scriptOp.appendChan('rarity')
        val = results.rarity if hasattr(results, 'rarity') else None
        chan[0] = val if val is not None else 0.0
        return
