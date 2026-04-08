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

from pyeyesweb.analysis_primitives import Synchronization
from pyeyesweb.data_models import SlidingWindow


class SynchronizationExt:
    """
    Synchronization PyEyesWeb Extension
    """

    def __init__(self, ownerComp):
        self.ownerComp = ownerComp

        # Define storage for persistence
        storedItems = [
            {'name': 'Applyfilter', 'default': False, 'target': ownerComp.par.Applyfilter if hasattr(ownerComp.par, 'Applyfilter') else None},
            {'name': 'Lowcut', 'default': 0.5, 'target': ownerComp.par.Lowcut if hasattr(ownerComp.par, 'Lowcut') else None},
            {'name': 'Highcut', 'default': 5.0, 'target': ownerComp.par.Highcut if hasattr(ownerComp.par, 'Highcut') else None},
            {'name': 'Fs', 'default': 60.0, 'target': ownerComp.par.Fs if hasattr(ownerComp.par, 'Fs') else None},
            {'name': 'Slidingwindowmaxlength', 'default': 60, 'target': ownerComp.par.Slidingwindowmaxlength if hasattr(ownerComp.par, 'Slidingwindowmaxlength') else None},
        ]
        
        # Initialize StorageManager
        self.stored = StorageManager(self, ownerComp, storedItems)

        # Map internal flags to stored values
        self.sliding_window_max_length = int(self.stored['Slidingwindowmaxlength'])
        self.apply_filter = bool(self.stored['Applyfilter'])
        self.lowcut = float(self.stored['Lowcut'])
        self.highcut = float(self.stored['Highcut'])
        self.fs = float(self.stored['Fs'])

        filter_params = None
        if self.apply_filter:
            filter_params = (self.lowcut, self.highcut, self.fs)

        self.feature = Synchronization(filter_params=filter_params)
        self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=2)  # Plv needs 2 inputs

    def _update_filter(self):
        if getattr(self, 'apply_filter', False):
            self.feature.filter_params = (self.lowcut, self.highcut, self.fs)
        else:
            self.feature.filter_params = None

    def _build_parameters(self):
        page_name = "Synchronization"
        
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
        p = page.appendToggle("Applyfilter", label="Apply Bandpass Filter")[0]
        p.default = False
        p.val = True
        
        p = page.appendFloat("Lowcut", label="Lowcut Freq (Hz)")[0]
        p.default = 0.5
        p.val = 0.5
        p.min = 0.1
        p.normMax = 10.0
        
        p = page.appendFloat("Highcut", label="Highcut Freq (Hz)")[0]
        p.default = 5.0
        p.val = 5.0
        p.min = 1.0
        p.normMax = 30.0
        
        p = page.appendFloat("Fs", label="Sampling Rate (Hz)")[0]
        p.default = 60.0
        p.val = 60.0
        p.min = 1.0
        p.normMax = 120.0
        
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

        def set_apply_filter(v):
            self.apply_filter = bool(v)
            self._update_filter()
            
        def set_lowcut(v):
            self.lowcut = float(v)
            self._update_filter()
            
        def set_highcut(v):
            self.highcut = float(v)
            self._update_filter()
            
        def set_fs(v):
            self.fs = float(v)
            self._update_filter()

        param_handlers = {
            "Slidingwindowmaxlength": lambda v: (
                setattr(self, 'sliding_window_max_length', int(float(v))),
                setattr(self.sliding_window, 'max_length', int(float(v)))
            ),
            "Applyfilter": set_apply_filter,
            "Lowcut": set_lowcut,
            "Highcut": set_highcut,
            "Fs": set_fs
        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def ProcessCook(self, scriptOp):
        scriptOp.clear()
        
        # Gathering multiple inputs since Phase Synch needs minimum 2.
        signals = []
        for i_chop in scriptOp.inputs:
            for chan in i_chop.chans():
                signals.append(chan[0])

        if not signals:
            return
            
        if len(signals) != self.sliding_window.n_signals:
            self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_signals=len(signals))

        self.sliding_window.append(signals)

        if not self.sliding_window.is_full:
            return

        results = self.feature(self.sliding_window)
        
        chan = scriptOp.appendChan('plv')
        val = results.plv if hasattr(results, 'plv') else None
        chan[0] = val if val is not None else 0.0
        return
