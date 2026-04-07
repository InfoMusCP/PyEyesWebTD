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

from pyeyesweb.mid_level import Impulsivity
from pyeyesweb.data_models import SlidingWindow


class ImpulsivityExt:
    """
    Impulsivity PyEyesWeb Extension
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
        self.compute_impulsivity = _safe_eval('Computeimpulsivity', True, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))
        self.compute_direction_change = _safe_eval('Computedirectionchange', False, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))
        self.compute_suddenness = _safe_eval('Computesuddenness', False, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))

        # Map initialization parameters
        direction_change_epsilon = _safe_eval('Directionchangeepsilon', 0.5, float)
        
        algos = ["new", "old"]
        algo_idx = _safe_eval('Suddennessalgo', 0, int)
        suddenness_algo = algos[max(0, min(algo_idx, len(algos)-1))]

        self.feature = Impulsivity(
            direction_change_epsilon=direction_change_epsilon,
            suddenness_algo=suddenness_algo
        )
        # Needs spatial coordinates since it computes DirectionChange
        self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=3)

    def _build_parameters(self):
        page_name = "Impulsivity"
        
        for page in self.ownerComp.customPages:
            if page.name == page_name:
                page.destroy()
                
        page = self.ownerComp.appendCustomPage(page_name)
        
        # --- Output Selection ---
        p = page.appendToggle("Computeimpulsivity", label="Output Impulsivity")[0]
        p.default = True
        p.val = True
        
        p = page.appendToggle("Computedirectionchange", label="Output Direction Change Var")[0]
        p.default = False
        p.val = False

        p = page.appendToggle("Computesuddenness", label="Output Suddenness Bool")[0]
        p.default = False
        p.val = False
        
        # --- Sensor/Stream Config ---
        p = page.appendInt("Slidingwindowmaxlength", label="Window Size (samples)")[0]
        p.default = 60
        p.val = 60
        p.min = 10
        p.normMax = 300
        
        # --- Algorithm Tuning ---
        p = page.appendFloat("Directionchangeepsilon", label="Direction Change Epsilon")[0]
        p.default = 0.5
        p.val = 0.5
        p.min = 0.01
        p.normMax = 2.0
        
        p = page.appendMenu("Suddennessalgo", label="Suddenness Algorithm")[0]
        p.menuNames = ["new", "old"]
        p.menuLabels = ["New Method", "Old Method"]
        p.default = 0
        p.val = 0
        
        print(f"[{self.ownerComp.name}] Custom Parameters Rebuilt Successfully.")

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update properties
        param_handlers = {
            "Slidingwindowmaxlength": lambda v: (
                setattr(self, 'sliding_window_max_length', int(float(v))),
                setattr(self.sliding_window, 'max_length', int(float(v)))
            ),
            "Computeimpulsivity": lambda v: setattr(self, 'compute_impulsivity', bool(v)),
            "Computedirectionchange": lambda v: setattr(self, 'compute_direction_change', bool(v)),
            "Computesuddenness": lambda v: setattr(self, 'compute_suddenness', bool(v)),
            "Directionchangeepsilon": lambda v: setattr(self.feature, 'direction_change_epsilon', float(v)),
            "Suddennessalgo": lambda v: setattr(self.feature, 'suddenness_algo', ["new", "old"][int(float(v))])
        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def ProcessCook(self, scriptOp):
        scriptOp.clear()
        
        signals = []
        for i_chop in scriptOp.inputs:
            for chan in i_chop.chans():
                signals.append(chan[0])

        if len(signals) < 2:
            return
            
        dims = 3 if len(signals) % 3 == 0 else (2 if len(signals) % 2 == 0 else 1)
        expected_signals = len(signals) // dims

        if expected_signals != self.sliding_window.n_signals or dims != self.sliding_window.n_dims:
            self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=expected_signals, n_dims=dims)

        self.sliding_window.append(signals)

        results = self.feature(self.sliding_window)
        
        if getattr(self, 'compute_impulsivity', False):
            val = results.impulsivity_index if hasattr(results, 'impulsivity_index') else None
            chan = scriptOp.appendChan('impulsivity_index')
            chan[0] = val if val is not None else 0.0
            
        if getattr(self, 'compute_direction_change', False):
            val = results.direction_change_val if hasattr(results, 'direction_change_val') else None
            chan = scriptOp.appendChan('direction_change_val')
            chan[0] = val if val is not None else 0.0

        if getattr(self, 'compute_suddenness', False):
            val = results.is_sudden if hasattr(results, 'is_sudden') else False
            chan = scriptOp.appendChan('is_sudden')
            chan[0] = 1.0 if val else 0.0

        return
