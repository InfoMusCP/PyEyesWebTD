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

from pyeyesweb.analysis_primitives import Clusterability
from pyeyesweb.data_models import SlidingWindow


class ClusterabilityExt:
    """
    Clusterability PyEyesWeb Extension
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

        # Map initialization parameters
        n_neighbors = _safe_eval('Nneighbors', 5, int)

        self.feature = Clusterability(n_neighbors=n_neighbors)
        self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=1)

    def _build_parameters(self):
        """Builds the custom parameter page with a structured layout."""
        page_name = "Clusterability"
        
        # Destroy existing page if it exists to ensure clean rebuild
        for page in self.ownerComp.customPages:
            if page.name == page_name:
                page.destroy()
                
        # Create new page
        page = self.ownerComp.appendCustomPage(page_name)
        
        # --- Sensor/Stream Config ---
        p = page.appendInt("Slidingwindowmaxlength", label="Window Size (samples)")[0]
        p.default = 60
        p.val = 60
        p.min = 10
        p.normMax = 300
        
        # --- Algorithm Tuning ---
        p = page.appendInt("Nneighbors", label="Number of Neighbors (k)")[0]
        p.default = 5
        p.val = 5
        p.min = 1
        p.normMax = 15
        
        print(f"[{self.ownerComp.name}] Custom Parameters Rebuilt Successfully.")

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update parameters based on name
        param_handlers = {
            "Slidingwindowmaxlength": lambda v: (
                setattr(self, 'sliding_window_max_length', int(float(v))),
                setattr(self.sliding_window, 'max_length', int(float(v)))
            ),
            "Nneighbors": lambda v: setattr(self.feature, 'n_neighbors', int(float(v)))
        }

        # Call the appropriate handler if it exists
        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def ProcessCook(self, scriptOp):
        """Processes the incoming CHOP data and outputs the clusterability metrics."""
        scriptOp.clear()
        inputs = scriptOp.inputs[0]
        series1 = inputs[0]

        self.sliding_window.append([series1])

        results = self.feature(self.sliding_window)
        
        clusterability_chan = scriptOp.appendChan('clusterability')
        val = results.clusterability if hasattr(results, 'clusterability') else None
        clusterability_chan[0] = val if val is not None else 0.0

        return
