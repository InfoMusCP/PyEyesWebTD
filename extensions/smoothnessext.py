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

        # Define storage for persistence
        storedItems = [
            {'name': 'Computesparc', 'default': True, 'target': ownerComp.par.Computesparc if hasattr(ownerComp.par, 'Computesparc') else None},
            {'name': 'Computejerk', 'default': True, 'target': ownerComp.par.Computejerk if hasattr(ownerComp.par, 'Computejerk') else None},
            {'name': 'Slidingwindowmaxlength', 'default': 60, 'target': ownerComp.par.Slidingwindowmaxlength if hasattr(ownerComp.par, 'Slidingwindowmaxlength') else None},
            {'name': 'Ratehz', 'default': 60.0, 'target': ownerComp.par.Ratehz if hasattr(ownerComp.par, 'Ratehz') else None},
            {'name': 'Usefilter', 'default': True, 'target': ownerComp.par.Usefilter if hasattr(ownerComp.par, 'Usefilter') else None},
            {'name': 'Sparcamplitudethreshold', 'default': 0.05, 'target': ownerComp.par.Sparcamplitudethreshold if hasattr(ownerComp.par, 'Sparcamplitudethreshold') else None},
            {'name': 'Sparcminfc', 'default': 2.0, 'target': ownerComp.par.Sparcminfc if hasattr(ownerComp.par, 'Sparcminfc') else None},
            {'name': 'Sparcmaxfc', 'default': 20.0, 'target': ownerComp.par.Sparcmaxfc if hasattr(ownerComp.par, 'Sparcmaxfc') else None},
        ]
        
        # Initialize StorageManager
        self.stored = StorageManager(self, ownerComp, storedItems)

        # Map internal flags to stored values
        self.sliding_window_max_length = int(self.stored['Slidingwindowmaxlength'])
        self.compute_sparc = bool(self.stored['Computesparc'])
        self.compute_jerk = bool(self.stored['Computejerk'])

        initial_metrics = []
        if self.compute_sparc:
            initial_metrics.append("sparc")
        if self.compute_jerk:
            initial_metrics.append("jerk_rms")

        self.smoothness = Smoothness(metrics=initial_metrics)

        # Map initialization parameters from storage
        self.smoothness.rate_hz = float(self.stored['Ratehz'])
        self.smoothness.use_filter = bool(self.stored['Usefilter'])
        self.smoothness.sparc_threshold = float(self.stored['Sparcamplitudethreshold'])
        self.smoothness.sparc_min_fc = float(self.stored['Sparcminfc'])
        self.smoothness.sparc_max_fc = float(self.stored['Sparcmaxfc'])

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
        
        # Refresh parameters from storage after they are rebuilt
        for item in self.stored.items():
            if hasattr(self.ownerComp.par, item.name):
                setattr(self.ownerComp.par, item.name, item.val)
        
        print(f"[{self.ownerComp.name}] Custom Parameters Rebuilt Successfully.")

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        if param_name in self.stored:
            self.stored[param_name] = param_value

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
