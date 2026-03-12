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

from pyeyesweb.low_level.geometric_symmetry import GeometricSymmetry
from pyeyesweb.data_models.sliding_window import SlidingWindow


class GeometricSymmetryExt:
    """
    InfoMusExt description
    """

    def __init__(self, ownerComp):
        # The component to which this extension is attached
        self.ownerComp = ownerComp

        self.params = op("parameter1")

        self.joint_pairs_sequence = self.ownerComp.seq.Jointpairs
        self.joint_pairs = [
            (self.joint_pairs_sequence[i].par.joint1.eval(),
             self.joint_pairs_sequence[i].par.joint2.eval()
             ) for i in range(len(self.joint_pairs_sequence))
        ]

        self.center_of_symmetry = int(self.params["Centerofsymmetry", 1].val)

        self.geometric_symmetry = GeometricSymmetry(joint_pairs=self.joint_pairs,
                                                    center_of_symmetry=self.center_of_symmetry)

    def _update_joint_pairs(self):
        self.joint_pairs_sequence = self.ownerComp.Jointpairs
        self.joint_pairs = [
            (self.joint_pairs_sequence[i].par.joint1.eval(),
             self.joint_pairs_sequence[i].par.joint2.eval()
             ) for i in range(len(self.joint_pairs_sequence))
        ]

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update parameters based on name (more efficient than multiple if-else)
        param_handlers = {
            "Centerofsymmetry": lambda v: (
                setattr(self, 'center_of_symmetry', int(v)),
                setattr(self.geometric_symmetry, 'center_of_symmetry', int(v))
            )
        }

        # Call the appropriate handler if it exists
        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def par_exec_onValuesChanged(self, par):
        self._update_joint_pairs()

    def onInitTD(self):
        """
        Called after the extension is fully initialized and attached to the
        component. Use this instead of __init__ for tasks that require other
        components' extensions to be available, or that use promoted members.
        """
        # self.joint_pairs_sequence = self.ownerComp.seq.Jointpairs
        # self.joint_pairs = [
        #     (self.joint_pairs_sequence[i].par.joint1.eval(),
        #      self.joint_pairs_sequence[i].par.joint2.eval()
        #      ) for i in range(len(self.joint_pairs_sequence))
        # ]
        #
        # self.center_of_symmetry = int(self.params["Centerofsymmetry", 1].val)
        #
        # self.geometric_symmetry = GeometricSymmetry(joint_pairs=self.joint_pairs,
        #                                             center_of_symmetry=self.center_of_symmetry)
