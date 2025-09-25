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

from pyeyesweb.sync import Synchronization
from pyeyesweb.data_models.sliding_window import SlidingWindow


class SynchronizationExt:
    """
    InfoMusExt description
    """

    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp

        self.params = op("parameter1")
        self.sliding_window_max_length = int(self.params["Slidingwindowmaxlength", 1].val)


        self.synchronization = Synchronization()
        self.sliding_window = SlidingWindow(max_length=self.sliding_window_max_length, n_columns=2)


    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update parameters based on name (more efficient than multiple if-else)
        param_handlers = {
            "Slidingwindowmaxlength": lambda v: setattr(self, 'sliding_window_max_length', int(v)),
        }

        # Call the appropriate handler if it exists
        if param_name in param_handlers:
            param_handlers[param_name](param_value)

