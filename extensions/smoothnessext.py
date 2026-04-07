"""
Extension classes enhance TouchDesigner components with python. An
extension is accessed via ext.ExtensionClassName from any operator
within the extended component. If the extension is promoted via its
Promote Extension parameter, all its attributes with capitalized names
can be accessed externally, e.g. op('yourComp').PromotedFunction().

Help: search "Extensions" in wiki
"""
import os
import sys

from TDStoreTools import StorageManager
import TDFunctions as TDF

parent_dir = os.path.dirname(project.folder)
lib_dir = os.path.join(project.folder, "pyeyesweb_env", "Lib", "site-packages")

if lib_dir not in sys.path:
	sys.path.insert(0, os.path.normpath(lib_dir))

from pyeyesweb.low_level import Smoothness
from pyeyesweb.data_models import SlidingWindow


class SmoothnessExt:
    """
    InfoMusExt description
    """

    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp

        # Helper to safely evaluate parameter values during component init
        def _safe_eval(par_name, default_val, expected_type):
            par = getattr(self.ownerComp.par, par_name, None)
            if par is not None:
                val = par.eval()
                # Empty string from DAT or invalid eval mapping
                if val == '' or val is None:
                    par.val = default_val  # Sync UI parameter visually
                    return default_val
                try:
                    result = expected_type(val)
                    # TD often defaults uninitialized params to 0, which breaks models
                    if result == 0 and default_val != 0:
                        par.val = default_val  # Sync UI parameter visually
                        return default_val
                    return result
                except (ValueError, TypeError):
                    pass
            return default_val

        # Sliding window
        self.sliding_window_max_length = _safe_eval('Slidingwindowmaxlength', 60, int)

        # Get metrics based on toggles
        self.compute_sparc = _safe_eval('Computesparc', True, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))
        self.compute_jerk = _safe_eval('Computejerk', True, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))

        initial_metrics = []
        if self.compute_sparc:
            initial_metrics.append("sparc")
        if self.compute_jerk:
            initial_metrics.append("jerk_rms")

        self.smoothness = Smoothness(metrics=initial_metrics)

        # Map optional new parameters if they exist in the Custom Parameters
        self.smoothness.rate_hz = _safe_eval('Ratehz', 60.0, float)
        self.smoothness.use_filter = _safe_eval('Usefilter', True, lambda v: bool(int(v)) if str(v).isdigit() else bool(v))
        self.smoothness.sparc_threshold = _safe_eval('Sparcamplitudethreshold', 0.05, float)
        self.smoothness.sparc_min_fc = _safe_eval('Sparcminfc', 2.0, float)
        self.smoothness.sparc_max_fc = _safe_eval('Sparcmaxfc', 20.0, float)

        self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=1)

    def _update_metrics(self):
        metrics = []
        if getattr(self, 'compute_sparc', False):
            metrics.append("sparc")
        if getattr(self, 'compute_jerk', False):
            metrics.append("jerk_rms")
        self.smoothness.metrics = metrics
    
    def _build_parameters(self):
        """Builds the custom parameter page with a structured layout."""
        page_name = "Smoothness"
        
        # Destroy existing page if it exists to ensure clean rebuild
        for page in self.ownerComp.customPages:
            if page.name == page_name:
                page.destroy()
                
        # Create new page
        page = self.ownerComp.appendCustomPage(page_name)
        
        # --- Output Selection ---
        p = page.appendToggle("Computesparc", label="Compute SPARC")[0]
        p.default = True
        p.val = True
        
        p = page.appendToggle("Computejerk", label="Compute Jerk RMS")[0]
        p.default = True
        p.val = True
        
        # --- Pre-processing ---
        p = page.appendToggle("Usefilter", label="Apply SavGol Filter")[0]
        p.default = True
        p.val = True
        
        # --- Sensor/Stream Config ---
        p = page.appendFloat("Ratehz", label="Sampling Rate (Hz)")[0]
        p.default = 60.0
        p.val = 60.0
        p.min = 1.0
        p.normMax = 120.0
        
        p = page.appendInt("Slidingwindowmaxlength", label="Window Size (samples)")[0]
        p.default = 60
        p.val = 60
        p.min = 10
        p.normMax = 300
        
        # --- Algorithm Tuning (SPARC specific) ---
        p = page.appendFloat("Sparcamplitudethreshold", label="SPARC Amp Threshold")[0]
        p.default = 0.05
        p.val = 0.05
        p.min = 0.0
        p.normMax = 0.5
        
        p = page.appendFloat("Sparcminfc", label="SPARC Min Freq (Hz)")[0]
        p.default = 2.0
        p.val = 2.0
        p.min = 0.1
        p.normMax = 10.0
        
        p = page.appendFloat("Sparcmaxfc", label="SPARC Max Freq (Hz)")[0]
        p.default = 20.0
        p.val = 20.0
        p.min = 2.0
        p.normMax = 40.0
        
        print(f"[{self.ownerComp.name}] Custom Parameters Rebuilt Successfully.")

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        def set_sparc(v):
            self.compute_sparc = bool(v)
            self._update_metrics()

        def set_jerk(v):
            self.compute_jerk = bool(v)
            self._update_metrics()

        # Update parameters based on name (more efficient than multiple if-else)
        param_handlers = {
            "Slidingwindowmaxlength": lambda v: (
                setattr(self, 'sliding_window_max_length', int(float(v))),
                setattr(self, 'smoothness_max_window', int(float(v))),
                setattr(self.sliding_window, 'max_length', int(float(v)))
            ),
            "Computesparc": set_sparc,
            "Computejerk": set_jerk,
            "Ratehz": lambda v: setattr(self.smoothness, 'rate_hz', float(v)),
            "Usefilter": lambda v: setattr(self.smoothness, 'use_filter', bool(v)),
            "Sparcamplitudethreshold": lambda v: setattr(self.smoothness, 'sparc_threshold', float(v)),
            "Sparcminfc": lambda v: setattr(self.smoothness, 'sparc_min_fc', float(v)),
            "Sparcmaxfc": lambda v: setattr(self.smoothness, 'sparc_max_fc', float(v))
        }

        # Call the appropriate handler if it exists
        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def ProcessCook(self, scriptOp):
        """Processes the incoming CHOP data and outputs the smoothness metrics."""
        scriptOp.clear()
        inputs = scriptOp.inputs[0]
        series1 = inputs[0]

        self.sliding_window.append([series1])

        results = self.smoothness(self.sliding_window)
        
        if getattr(self, 'compute_sparc', False):
            sparc_chan = scriptOp.appendChan('sparc')
            val = results.sparc if hasattr(results, 'sparc') else None
            sparc_chan[0] = val if val is not None else 0.0
            
        if getattr(self, 'compute_jerk', False):	
            jerk_chan = scriptOp.appendChan('jerk')	
            val = results.jerk_rms if hasattr(results, 'jerk_rms') else None
            jerk_chan[0] = val if val is not None else 0.0
        return
