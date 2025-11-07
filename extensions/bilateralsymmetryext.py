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

from pyeyesweb.analysis_primitives.bilateral_symmetry import BilateralSymmetryAnalyzer


class BilateralSymmetryExt:
    """
    InfoMusExt description
    """

    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp

        self.params = op("parameter1")

        self.contraction = BilateralSymmetryAnalyzer()

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update parameters based on name (more efficient than multiple if-else)
        param_handlers = {}

        # Call the appropriate handler if it exists
        if param_name in param_handlers:
            param_handlers[param_name](param_value)

