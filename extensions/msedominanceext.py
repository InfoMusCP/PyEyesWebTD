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

from pyeyesweb.analysis_primitives import MultiScaleEntropyDominance
from pyeyesweb.data_models import SlidingWindow


class MSEDominanceExt:
    """
    MultiScaleEntropyDominance PyEyesWeb Extension
    """

    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp

        # Define storage for persistence
        storedItems = [
            {'name': 'Computecomplexityindex', 'default': True, 'target': ownerComp.par.Computecomplexityindex if hasattr(ownerComp.par, 'Computecomplexityindex') else None},
            {'name': 'Computedominancescore', 'default': False, 'target': ownerComp.par.Computedominancescore if hasattr(ownerComp.par, 'Computedominancescore') else None},
            {'name': 'Computeleaderidentification', 'default': False, 'target': ownerComp.par.Computeleaderidentification if hasattr(ownerComp.par, 'Computeleaderidentification') else None},
            {'name': 'Slidingwindowmaxlength', 'default': 500, 'target': ownerComp.par.Slidingwindowmaxlength if hasattr(ownerComp.par, 'Slidingwindowmaxlength') else None},
            {'name': 'M', 'default': 2, 'target': ownerComp.par.M if hasattr(ownerComp.par, 'M') else None},
            {'name': 'R', 'default': 0.15, 'target': ownerComp.par.R if hasattr(ownerComp.par, 'R') else None},
            {'name': 'Maxscale', 'default': 6, 'target': ownerComp.par.Maxscale if hasattr(ownerComp.par, 'Maxscale') else None},
            {'name': 'Minpoints', 'default': 500, 'target': ownerComp.par.Minpoints if hasattr(ownerComp.par, 'Minpoints') else None},
        ]
        
        # Initialize StorageManager
        self.stored = StorageManager(self, ownerComp, storedItems)

        # Map internal flags to stored values
        self.sliding_window_max_length = int(self.stored['Slidingwindowmaxlength'])
        self.compute_complexity_index = bool(self.stored['Computecomplexityindex'])
        self.compute_dominance_score = bool(self.stored['Computedominancescore'])
        self.compute_leader_identification = bool(self.stored['Computeleaderidentification'])

        initial_metrics = []
        if self.compute_complexity_index:
            initial_metrics.append("complexity_index")
        if self.compute_dominance_score:
            initial_metrics.append("dominance_score")
        if self.compute_leader_identification:
            initial_metrics.append("leader_identification")
            
        # Ensure at least one output if uninitialized
        if not initial_metrics:
            initial_metrics = ["complexity_index"]

        # Map initialization parameters
        m = int(self.stored['M'])
        r = float(self.stored['R'])
        max_scale = int(self.stored['Maxscale'])
        min_points = int(self.stored['Minpoints'])

        self.feature = MultiScaleEntropyDominance(
            m=m, r=r, max_scale=max_scale, min_points=min_points, methods=initial_metrics
        )
        # Assuming multi-signal use case for dominance, let's start with 2 signals
        self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=2)

    def _update_metrics(self):
        metrics = []
        if getattr(self, 'compute_complexity_index', False):
            metrics.append("complexity_index")
        if getattr(self, 'compute_dominance_score', False):
            metrics.append("dominance_score")
        if getattr(self, 'compute_leader_identification', False):
            metrics.append("leader_identification")
        self.feature.methods = metrics

    def _build_parameters(self):
        """Builds the custom parameter page with a structured layout."""
        page_name = "MSEDominance"
        
        for page in self.ownerComp.customPages:
            if page.name == page_name:
                page.destroy()
                
        page = self.ownerComp.appendCustomPage(page_name)
        
        # --- Output Selection ---
        p = page.appendToggle("Computecomplexityindex", label="Output Complexity Index")[0]
        p.default = True
        p.val = True
        
        p = page.appendToggle("Computedominancescore", label="Output Dominance Score")[0]
        p.default = False
        p.val = False

        p = page.appendToggle("Computeleaderidentification", label="Output Leader Identification")[0]
        p.default = False
        p.val = False
        
        # --- Sensor/Stream Config ---
        p = page.appendInt("Slidingwindowmaxlength", label="Window Size (samples)")[0]
        p.default = 500
        p.val = 500
        p.min = 100
        p.normMax = 2000
        
        # --- Algorithm Tuning ---
        p = page.appendInt("M", label="Pattern Length (m)")[0]
        p.default = 2
        p.val = 2
        p.min = 1
        p.normMax = 5
        
        p = page.appendFloat("R", label="Tolerance (r)")[0]
        p.default = 0.15
        p.val = 0.15
        p.min = 0.01
        p.normMax = 0.5
        
        p = page.appendInt("Maxscale", label="Max Scale")[0]
        p.default = 6
        p.val = 6
        p.min = 1
        p.normMax = 20
        
        p = page.appendInt("Minpoints", label="Min Points")[0]
        p.default = 500
        p.val = 500
        p.min = 100
        p.normMax = 2000
        
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

        def set_complexity(v):
            self.compute_complexity_index = bool(v)
            self._update_metrics()
            
        def set_dominance(v):
            self.compute_dominance_score = bool(v)
            self._update_metrics()
            
        def set_leader(v):
            self.compute_leader_identification = bool(v)
            self._update_metrics()

        param_handlers = {
            "Slidingwindowmaxlength": lambda v: (
                setattr(self, 'sliding_window_max_length', int(float(v))),
                setattr(self.sliding_window, 'max_length', int(float(v)))
            ),
            "Computecomplexityindex": set_complexity,
            "Computedominancescore": set_dominance,
            "Computeleaderidentification": set_leader,
            "M": lambda v: setattr(self.feature, 'm', int(float(v))),
            "R": lambda v: setattr(self.feature, 'r', float(v)),
            "Maxscale": lambda v: setattr(self.feature, 'max_scale', int(float(v))),
            "Minpoints": lambda v: setattr(self.feature, 'min_points', int(float(v)))
        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def ProcessCook(self, scriptOp):
        """Processes the incoming CHOP data and outputs the MultiScale Entropy metrics."""
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
        
        if getattr(self, 'compute_complexity_index', False):
            val = results.get('complexity_index', None)
            if isinstance(val, list):
                for i, v in enumerate(val):
                    chan = scriptOp.appendChan(f'complexity_index_{i}')
                    chan[0] = v if not isinstance(v, float) or v == v else 0.0 # handle nan safely
            else:
                chan = scriptOp.appendChan('complexity_index')
                chan[0] = val if val is not None and val == val else 0.0
                
        if getattr(self, 'compute_dominance_score', False):
            val = results.get('dominance_score', None)
            if isinstance(val, list):
                for i, v in enumerate(val):
                    chan = scriptOp.appendChan(f'dominance_score_{i}')
                    chan[0] = v if not isinstance(v, float) or v == v else 0.0
            else:
                chan = scriptOp.appendChan('dominance_score')
                chan[0] = val if val is not None and val == val else 0.0
                
        if getattr(self, 'compute_leader_identification', False):
            val = results.get('leader_complexity', None)
            # Leader complexity returns a tuple: (leader_idx, complexity_value)
            idx_chan = scriptOp.appendChan('leader_idx')
            val_chan = scriptOp.appendChan('leader_complexity')
            if val is not None:
                idx_chan[0] = val[0]
                val_chan[0] = val[1] if val[1] == val[1] else 0.0
            else:
                idx_chan[0] = 0.0
                val_chan[0] = 0.0

        return
