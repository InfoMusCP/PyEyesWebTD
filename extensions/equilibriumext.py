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

from pyeyesweb.low_level.equilibrium import Equilibrium


class EquilibriumExt:
    """
    InfoMusExt description
    """

    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp

        self.params = op("parameter1")
        self.margin = float(self.params["Margin", 1].val)
        self.y_weight = float(self.params["Yweight", 1].val)


        self.equilibrium = Equilibrium(margin_mm=self.margin, y_weight=self.y_weight)

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Map parameter names to update functions
        param_handlers = {
            "Margin": lambda v: (
                setattr(self, "margin", v),
                setattr(self.equilibrium, "margin_mm", v),
            ),
            "Yweight": lambda v: (
                setattr(self, "y_weight", v),
                setattr(self.equilibrium, "y_weight", v),
            ),
        }

        # Call the appropriate handler if it exists
        if param_name in param_handlers:
            param_handlers[param_name](param_value)
