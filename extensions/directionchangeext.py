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

from pyeyesweb.low_level import DirectionChange
from pyeyesweb.data_models import SlidingWindow


class DirectionChangeExt:
    """
    DirectionChange PyEyesWeb Extension
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
        self.compute_cosine = _safe_eval('Computecosine', True, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))
        self.compute_polygon = _safe_eval('Computepolygon', True, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))

        initial_metrics = []
        if self.compute_cosine:
            initial_metrics.append("cosine")
        if self.compute_polygon:
            initial_metrics.append("polygon")

        if not initial_metrics:
            initial_metrics = ["cosine"]

        # Map initialization parameters
        epsilon = _safe_eval('Epsilon', 0.5, float)
        num_subsamples = _safe_eval('Numsubsamples', 20, int)
        saturation_area = _safe_eval('Saturationarea', 0.3, float)
        saturation_slope = _safe_eval('Saturationslope', 0.09, float)

        self.feature = DirectionChange(
            epsilon=epsilon,
            num_subsamples=num_subsamples,
            saturation_area=saturation_area,
            saturation_slope=saturation_slope,
            metrics=initial_metrics
        )
        # We need trajectory coordinate points over time, typically requires 3 signals (x, y, z)
        # but the module technically handles any dimensionality D>=2 
        # We will dynamically resize if needed in ProcessCook. Start with 3.
        self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=3)

    def _update_metrics(self):
        metrics = []
        if getattr(self, 'compute_cosine', False):
            metrics.append("cosine")
        if getattr(self, 'compute_polygon', False):
            metrics.append("polygon")
        self.feature.metrics = metrics

    def _build_parameters(self):
        page_name = "DirectionChange"
        
        for page in self.ownerComp.customPages:
            if page.name == page_name:
                page.destroy()
                
        page = self.ownerComp.appendCustomPage(page_name)
        
        # --- Output Selection ---
        p = page.appendToggle("Computecosine", label="Compute Cosine Similarity")[0]
        p.default = True
        p.val = True
        
        p = page.appendToggle("Computepolygon", label="Compute Polygon Area")[0]
        p.default = True
        p.val = True
        
        # --- Sensor/Stream Config ---
        p = page.appendInt("Slidingwindowmaxlength", label="Window Size (samples)")[0]
        p.default = 60
        p.val = 60
        p.min = 10
        p.normMax = 300
        
        # --- Algorithm Tuning ---
        p = page.appendFloat("Epsilon", label="Cosine Epsilon")[0]
        p.default = 0.5
        p.val = 0.5
        p.min = 0.01
        p.normMax = 2.0
        
        p = page.appendInt("Numsubsamples", label="Polygon Subsamples")[0]
        p.default = 20
        p.val = 20
        p.min = 3
        p.normMax = 50
        
        p = page.appendFloat("Saturationarea", label="Saturation Area")[0]
        p.default = 0.3
        p.val = 0.3
        p.min = 0.01
        p.normMax = 1.0
        
        p = page.appendFloat("Saturationslope", label="Saturation Slope")[0]
        p.default = 0.09
        p.val = 0.09
        p.min = 0.01
        p.normMax = 0.5
        
        print(f"[{self.ownerComp.name}] Custom Parameters Rebuilt Successfully.")

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        def set_cosine(v):
            self.compute_cosine = bool(v)
            self._update_metrics()
            
        def set_polygon(v):
            self.compute_polygon = bool(v)
            self._update_metrics()

        param_handlers = {
            "Slidingwindowmaxlength": lambda v: (
                setattr(self, 'sliding_window_max_length', int(float(v))),
                setattr(self.sliding_window, 'max_length', int(float(v)))
            ),
            "Computecosine": set_cosine,
            "Computepolygon": set_polygon,
            "Epsilon": lambda v: setattr(self.feature, 'epsilon', float(v)),
            "Numsubsamples": lambda v: setattr(self.feature, 'num_subsamples', int(float(v))),
            "Saturationarea": lambda v: setattr(self.feature, 'saturation_area', float(v)),
            "Saturationslope": lambda v: setattr(self.feature, 'saturation_slope', float(v))
        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def ProcessCook(self, scriptOp):
        scriptOp.clear()
        
        # Gather dynamic positional signals
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
        
        if getattr(self, 'compute_cosine', False):
            val = results.cosine if hasattr(results, 'cosine') else None
            chan = scriptOp.appendChan('cosine_similarity')
            chan[0] = val if val is not None else 0.0
            
        if getattr(self, 'compute_polygon', False):
            val = results.polygon if hasattr(results, 'polygon') else None
            chan = scriptOp.appendChan('polygon_area')
            chan[0] = val if val is not None else 0.0

        return
