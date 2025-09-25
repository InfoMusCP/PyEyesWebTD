"""
Extension classes enhance TouchDesigner components with python. An
extension is accessed via ext.ExtensionClassName from any operator
within the extended component. If the extension is promoted via its
Promote Extension parameter, all its attributes with capitalized names
can be accessed externally, e.g. op('yourComp').PromotedFunction().

Help: search "Extensions" in wiki
"""

from TDStoreTools import StorageManager
import TDFunctions as TDF

from pyeyesweb.mid_level import Smoothness
from pyeyesweb.sync import Synchronization
from pyeyesweb.data_models.sliding_window import SlidingWindow


class InfoMusExt:
    """
    InfoMusExt description
    """

    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp

        self.params = op("parameter1")
        self.compute_smoothness = bool(self.params["Computesmoothness", 1].val)
        self.compute_synchronization = bool(self.params["Computesynchronization", 1].val)

        self.synchronization_max_window = int(self.params["Slidingwindowmaxlenghtsynch", 1].val)

        self.smoothness_max_window = int(self.params["Slidingwindowmaxlenghtsmooth", 1].val)
        self.compute_sparc = bool(self.params["Computesparc", 1].val)
        self.compute_jerk = bool(self.params["Computejerk", 1].val)

        self.synch = Synchronization()
        self.synch_sliding_window = SlidingWindow(max_length=self.synchronization_max_window, n_columns=2)

        self.smoothness = Smoothness()
        self.smoothness_sliding_window = SlidingWindow(max_length=self.smoothness_max_window, n_columns=1)

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update parameters based on name (more efficient than multiple if-else)
        param_handlers = {
            "Computesmoothness": lambda v: setattr(self, 'compute_smoothness', bool(v)),
            "Computesynchronization": lambda v: setattr(self, 'compute_synchronization', bool(v)),
            "Slidingwindowmaxlenghtsmooth": lambda v: setattr(self, 'smoothness_max_window', int(v)),
            "Slidingwindowmaxlenghtsynch": lambda v: setattr(self, 'synchronization_max_window', int(v)),
            "Computesparc": lambda v: setattr(self, 'compute_sparc', bool(v)),
            "Computejerk": lambda v: setattr(self, 'compute_jerk', bool(v))
        }

        # Call the appropriate handler if it exists
        if param_name in param_handlers:
            param_handlers[param_name](param_value)

