"""
Extension classes enhance TouchDesigner components with python.
"""
import os
import sys
import numpy as np

from TDStoreTools import StorageManager
import TDFunctions as TDF

parent_dir = os.path.dirname(project.folder)
lib_dir = os.path.join(project.folder, "pyeyesweb_env", "Lib", "site-packages")

if lib_dir not in sys.path:
    sys.path.insert(0, os.path.normpath(lib_dir))

from pyeyesweb.low_level.contraction_expansion import BoundingBoxFilledArea, EllipsoidSphericity, PointsDensity


class ContractionExpansionExt:
    """
    ContractionExpansion PyEyesWeb Extension
    Coordinates multiple static spatial features natively.
    """

    def __init__(self, ownerComp):
        self.ownerComp = ownerComp

        # Define storage for persistence
        storedItems = [
            {'name': 'Computefilledarea', 'default': True, 'target': ownerComp.par.Computefilledarea if hasattr(ownerComp.par, 'Computefilledarea') else None},
            {'name': 'Computesphericity', 'default': True, 'target': ownerComp.par.Computesphericity if hasattr(ownerComp.par, 'Computesphericity') else None},
            {'name': 'Computedensity', 'default': True, 'target': ownerComp.par.Computedensity if hasattr(ownerComp.par, 'Computedensity') else None},
        ]
        
        # Initialize StorageManager
        self.stored = StorageManager(self, ownerComp, storedItems)

        # Map internal flags to stored values
        self.compute_filled_area = self.stored['Computefilledarea']
        self.compute_sphericity = self.stored['Computesphericity']
        self.compute_density = self.stored['Computedensity']

        # Unlike dynamic features, these are static spatial calculations applied per-frame
        self.feature_area = BoundingBoxFilledArea()
        self.feature_sphericity = EllipsoidSphericity()
        self.feature_density = PointsDensity()

    def _build_parameters(self):
        page_name = "ContractionExpansion"
        
        for page in self.ownerComp.customPages:
            if page.name == page_name:
                page.destroy()
                
        page = self.ownerComp.appendCustomPage(page_name)
        
        # --- Output Selection ---
        p = page.appendToggle("Computefilledarea", label="Compute BBox Area")[0]
        p.default = True
        p.val = True
        
        p = page.appendToggle("Computesphericity", label="Compute Sphericity")[0]
        p.default = True
        p.val = True

        p = page.appendToggle("Computedensity", label="Compute Point Density")[0]
        p.default = True
        p.val = True
        
        # Because these expect spatial points (e.g. 3D Body Joints) internally, 
        # there is no SlidingWindowmaxlength parameter. Computation is per-frame.
        
        # Refresh parameters from storage after they are rebuilt
        for item in self.stored.items():
            if hasattr(self.ownerComp.par, item.name):
                setattr(self.ownerComp.par, item.name, item.val)
        
        print(f"[{self.ownerComp.name}] Custom Parameters Rebuilt Successfully.")

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update storage (this will also update the parameter if it was a target, 
        # though here the parameter change triggered this, so it's a loop-safe sync)
        if param_name in self.stored:
            self.stored[param_name] = param_value

        # Update toggles internally for fast access in ProcessCook
        param_handlers = {
            "Computefilledarea": lambda v: setattr(self, 'compute_filled_area', bool(v)),
            "Computesphericity": lambda v: setattr(self, 'compute_sphericity', bool(v)),
            "Computedensity": lambda v: setattr(self, 'compute_density', bool(v))
        }

        if param_name in param_handlers:
            param_handlers[param_name](param_value)

    def ProcessCook(self, scriptOp):
        scriptOp.clear()
        
        if len(scriptOp.inputs) == 0:
            return
            
        input_chop = scriptOp.inputs[0]
        n_chans = input_chop.numChans
        if n_chans < 2:
            return

        # Determine dimensionality: channels grouped by 3 (3D) or 2 (2D)
        if n_chans % 3 == 0:
            dims = 3
        elif n_chans % 2 == 0:
            dims = 2
        else:
            return

        # Fast extraction via numpyArray: shape (n_chans, n_samples)
        arr = input_chop.numpyArray()
        if arr.shape[1] == 0:
            return

        # Take first sample, reshape to (n_joints, dims)
        flat = arr[:, 0]
        frame_data = flat.reshape(-1, dims)

        # Library features expect 3D — pad 2D with zeros
        if dims == 2:
            frame_data = np.column_stack([frame_data, np.zeros(frame_data.shape[0])])

        if getattr(self, 'compute_filled_area', False):
            res_area = self.feature_area.compute(frame_data)
            chan = scriptOp.appendChan('contraction_index')
            val = res_area.contraction_index if hasattr(res_area, 'contraction_index') else None
            chan[0] = val if val is not None else 0.0
            
        if getattr(self, 'compute_sphericity', False):
            res_sph = self.feature_sphericity.compute(frame_data)
            chan = scriptOp.appendChan('sphericity')
            val = res_sph.sphericity if hasattr(res_sph, 'sphericity') else None
            chan[0] = val if val is not None else 0.0
            
        if getattr(self, 'compute_density', False):
            res_den = self.feature_density.compute(frame_data)
            chan = scriptOp.appendChan('points_density')
            val = res_den.points_density if hasattr(res_den, 'points_density') else None
            chan[0] = val if val is not None else 0.0

        return
