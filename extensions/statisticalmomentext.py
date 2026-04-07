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

from pyeyesweb.analysis_primitives import StatisticalMoment
from pyeyesweb.data_models import SlidingWindow


class StatisticalMomentExt:
    """
    StatisticalMoment PyEyesWeb Extension
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
        self.compute_mean = _safe_eval('Computemean', True, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))
        self.compute_std_dev = _safe_eval('Computestddev', True, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))
        self.compute_skewness = _safe_eval('Computeskewness', False, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))
        self.compute_kurtosis = _safe_eval('Computekurtosis', False, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))

        initial_metrics = []
        if self.compute_mean:
            initial_metrics.append("mean")
        if self.compute_std_dev:
            initial_metrics.append("std_dev")
        if self.compute_skewness:
            initial_metrics.append("skewness")
        if self.compute_kurtosis:
            initial_metrics.append("kurtosis")

        if not initial_metrics:
            initial_metrics = ["mean"]

        self.feature = StatisticalMoment(metrics=initial_metrics)
        self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=1)

    def _update_metrics(self):
        metrics = []
        if getattr(self, 'compute_mean', False):
            metrics.append("mean")
        if getattr(self, 'compute_std_dev', False):
            metrics.append("std_dev")
        if getattr(self, 'compute_skewness', False):
            metrics.append("skewness")
        if getattr(self, 'compute_kurtosis', False):
            metrics.append("kurtosis")
        self.feature.metrics = metrics

    def _build_parameters(self):
        page_name = "StatisticalMoment"
        
        for page in self.ownerComp.customPages:
            if page.name == page_name:
                page.destroy()
                
        page = self.ownerComp.appendCustomPage(page_name)
        
        # --- Output Selection ---
        p = page.appendToggle("Computemean", label="Output Mean")[0]
        p.default = True
        p.val = True
        
        p = page.appendToggle("Computestddev", label="Output Std Dev")[0]
        p.default = True
        p.val = True

        p = page.appendToggle("Computeskewness", label="Output Skewness")[0]
        p.default = False
        p.val = False

        p = page.appendToggle("Computekurtosis", label="Output Kurtosis")[0]
        p.default = False
        p.val = False
        
        # --- Sensor/Stream Config ---
        p = page.appendInt("Slidingwindowmaxlength", label="Window Size (samples)")[0]
        p.default = 60
        p.val = 60
        p.min = 10
        p.normMax = 300
        
        print(f"[{self.ownerComp.name}] Custom Parameters Rebuilt Successfully.")

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        def set_mean(v):
            self.compute_mean = bool(v)
            self._update_metrics()
            
        def set_std_dev(v):
            self.compute_std_dev = bool(v)
            self._update_metrics()
            
        def set_skewness(v):
            self.compute_skewness = bool(v)
            self._update_metrics()

        def set_kurtosis(v):
            self.compute_kurtosis = bool(v)
            self._update_metrics()

        param_handlers = {
            "Slidingwindowmaxlength": lambda v: (
                setattr(self, 'sliding_window_max_length', int(float(v))),
                setattr(self.sliding_window, 'max_length', int(float(v)))
            ),
            "Computemean": set_mean,
            "Computestddev": set_std_dev,
            "Computeskewness": set_skewness,
            "Computekurtosis": set_kurtosis
        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def ProcessCook(self, scriptOp):
        scriptOp.clear()
        
        # Multi-signal gather
        signals = []
        for i_chop in scriptOp.inputs:
            for chan in i_chop.chans():
                signals.append(chan[0])

        if not signals:
            return
            
        # Dynamically resize signal columns if the CHOP structure changes
        if len(signals) != self.sliding_window.n_signals:
            self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=len(signals))

        self.sliding_window.append(signals)

        results = self.feature(self.sliding_window)
        
        # Use the built in flat dictionary string unpacking mapping directly
        flat_results = results.to_flat_dict()
        
        for metric_name, value in flat_results.items():
            chan = scriptOp.appendChan(metric_name)
            chan[0] = value if value == value else 0.0 # catch nans

        return
