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

from pyeyesweb.mid_level.lightness import Lightness
from pyeyesweb.data_models.sliding_window import SlidingWindow


class LightnessExt:
    """
    InfoMusExt description
    """

    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp

        self.params = op("parameter1")
        self.rate = int(self.params["Rate", 1].val)
        self.sliding_window_max_length = int(self.params["Slidingwindowmaxlength", 1].val)

        self.lightness = Lightness(
            sliding_window_max_length=self.sliding_window_max_length,
            rate_hz=self.rate
        )

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update parameters based on name (more efficient than multiple if-else)
        param_handlers = {
            "Slidingwindowmaxlength": lambda v: (
                setattr(self, 'sliding_window_max_length', int(v)),
                setattr(self.lightness, 'sliding_window_max_length', int(v)),
                setattr(self.lightness.sliding_window, 'max_length', int(v))
            ),
            "Rate": lambda v: (
                setattr(self, 'rate', int(v)),
                setattr(self.lightness, 'rate', int(v))
            ),
        }

        # Call the appropriate handler if it exists
        if param_name in param_handlers:
            param_handlers[param_name](param_value)
