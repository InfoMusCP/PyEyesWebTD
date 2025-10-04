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

from pyeyesweb.mid_level.smoothness import Smoothness
from pyeyesweb.data_models.sliding_window import SlidingWindow


class SmoothnessExt:
    """
    InfoMusExt description
    """

    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp

        self.params = op("parameter1")

        self.sliding_window_max_length = int(self.params["Slidingwindowmaxlength", 1].val)
        self.compute_jerk = bool(self.params["Computejerk", 1].val)
        self.compute_sparc = bool(self.params["Computesparc", 1].val)

        self.smoothness = Smoothness()
        self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_columns=1)

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update parameters based on name (more efficient than multiple if-else)
        param_handlers = {
            "Slidingwindowmaxlength": lambda v: (
                setattr(self, 'smoothness_max_window', int(v)),
                setattr(self.sliding_window, 'max_length', int(v))
            ),
            "Computesparc": lambda v: setattr(self, 'compute_sparc', bool(v)),
            "Computejerk": lambda v: setattr(self, 'compute_jerk', bool(v))
        }

        # Call the appropriate handler if it exists
        if param_name in param_handlers:
            param_handlers[param_name](param_value)

