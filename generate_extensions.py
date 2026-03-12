import os
import sys
import inspect
import json
import importlib

# Ensure PyEyesWeb is in the path so we can parse it
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "PyEyesWeb")))

DATA_ROUTER = {
    # == Analysis Primitives ==
    "Clusterability": {
        "module": "pyeyesweb.analysis_primitives.clusterability",
        "inputs": [{"name": "Features", "type": "CHOP"}],
        "shape": "2D_features", "requires_window": True, "default_window_size": 100
    },
    "MultiScaleEntropyDominance": {
        "module": "pyeyesweb.analysis_primitives.mse_dominance",
        "inputs": [{"name": "Signals", "type": "CHOP"}],
        "shape": "2D_features", "requires_window": True, "default_window_size": 500
    },
    "Rarity": {
        "module": "pyeyesweb.analysis_primitives.rarity",
        "inputs": [{"name": "Speed", "type": "CHOP"}],
        "shape": "1D", "requires_window": True, "default_window_size": 100
    },
    "StatisticalMoment": {
        "module": "pyeyesweb.analysis_primitives.statistical_moment",
        "inputs": [{"name": "Features", "type": "CHOP"}],
        "shape": "2D_features", "requires_window": True, "default_window_size": 100
    },
    "Synchronization": {
        "module": "pyeyesweb.analysis_primitives.synchronization",
        "inputs": [{"name": "Signals", "type": "CHOP"}],
        "shape": "2D_features", "requires_window": True, "default_window_size": 100
    },

    # == Low Level ==
    "Smoothness": {
        "module": "pyeyesweb.low_level.smoothness",
        "inputs": [{"name": "Speed", "type": "CHOP"}],
        "shape": "1D", "requires_window": True, "default_window_size": 100
    },
    "Equilibrium": {
        "module": "pyeyesweb.low_level.equilibrium",
        "inputs": [
            {"name": "Left Foot", "type": "CHOP"},
            {"name": "Right Foot", "type": "CHOP"},
            {"name": "Barycenter", "type": "CHOP"}
        ],
        "shape": "2D_joints", "requires_window": False
    },
    "BoundingBoxFilledArea": {
        "module": "pyeyesweb.low_level.contraction_expansion",
        "inputs": [{"name": "Joints", "type": "CHOP"}],
        "shape": "2D_joints", "requires_window": False
    },
    "EllipsoidSphericity": {
        "module": "pyeyesweb.low_level.contraction_expansion",
        "inputs": [{"name": "Joints", "type": "CHOP"}],
        "shape": "2D_joints", "requires_window": False
    },
    "PointsDensity": {
        "module": "pyeyesweb.low_level.contraction_expansion",
        "inputs": [{"name": "Joints", "type": "CHOP"}],
        "shape": "2D_joints", "requires_window": False
    },
    "DirectionChange": {
        "module": "pyeyesweb.low_level.direction_change",
        "inputs": [{"name": "Trajectory", "type": "CHOP"}],
        "shape": "2D_features", "requires_window": True, "default_window_size": 100
    },
    "GeometricSymmetry": {
        "module": "pyeyesweb.low_level.geometric_symmetry",
        "inputs": [{"name": "Joints", "type": "CHOP"}],
        "shape": "2D_joints", "requires_window": False
    },
    "KineticEnergy": {
        "module": "pyeyesweb.low_level.kinetic_energy",
        "inputs": [{"name": "Velocities", "type": "CHOP"}],
        "shape": "2D_joints", "requires_window": False
    },

    # == Mid Level ==
    "Impulsivity": {
        "module": "pyeyesweb.mid_level.impulsivity",
        "inputs": [{"name": "Trajectory", "type": "CHOP"}],
        "shape": "3D_window", "requires_window": True, "default_window_size": 100
    },
    "Lightness": {
        "module": "pyeyesweb.mid_level.lightness",
        "inputs": [{"name": "Velocities", "type": "CHOP"}],
        "shape": "3D_window", "requires_window": True, "default_window_size": 100
    },
    "Suddenness": {
        "module": "pyeyesweb.mid_level.suddenness",
        "inputs": [{"name": "Trajectory", "type": "CHOP"}],
        "shape": "3D_window", "requires_window": True, "default_window_size": 100
    }
}

EXTENSION_TEMPLATE = """\"\"\"
Generated TouchDesigner Extension for {class_name}
\"\"\"
import os
import sys
import numpy as np

# Ensure pyeyesweb is accessible
conda_lib_dir = "C:/Users/Nicola/miniconda3/envs/pwb/Lib/site-packages"
if conda_lib_dir not in sys.path:
    sys.path.insert(0, conda_lib_dir)

from {module_name} import {class_name}
{import_window}

class {class_name}Ext:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        
{init_params}

        # Initialize PyEyesWeb Feature
        self.analyzer = {class_name}({constructor_args})
{init_window}

    def par_exec_onValueChange(self, par):
        param_name = par.name
        param_value = par.eval()

        # Update parameters based on name
        param_handlers = {{
{param_handlers}
        }}

        if param_name in param_handlers:
            param_handlers[param_name](param_value)
            
    def process_data(self):
        \"\"\"
        Reads inputs, formats data for {class_name}, and computes the result.
        \"\"\"
        {process_logic}
"""


def get_td_param_type(param_annotation):
    """Maps Python type hints to TouchDesigner Custom Parameter types."""
    if param_annotation == inspect.Parameter.empty:
        return "Float" # Default fallback
    
    type_str = str(param_annotation).lower()
    
    if "int" in type_str:
        return "Int"
    elif "float" in type_str:
        return "Float"
    elif "bool" in type_str:
        return "Toggle"
    elif "str" in type_str:
        return "Str"
    elif "list" in type_str or "literal" in type_str or "tuple" in type_str or "dict" in type_str:
        return "Str" # Fallback for complex types
        
    return "Float"


def infer_process_logic(signature_data):
    shape = signature_data.get("shape", "Unknown")
    requires_window = signature_data.get("requires_window", False)
    
    logic = ""
    logic += "chop_in = self.ownerComp.op('in_1')\n"
    logic += "        if not chop_in or chop_in.numChans == 0:\n"
    logic += "            return None\n\n"
    
    if shape == "1D":
         logic += "        # 1D Array (Single channel speed/value)\n"
         logic += "        vals = [c.eval() for c in chop_in.chans()]\n"
    elif shape == "2D_joints":
         logic += "        # 2D Array formatting: grouping channels by 3 (X,Y,Z)\n"
         logic += "        vals = [c.eval() for c in chop_in.chans()]\n"
         logic += "        # Assuming 3 CHOP channels per joint (tx, ty, tz)\n"
         logic += "        num_joints = len(vals) // 3\n"
         logic += "        vals = np.array(vals).reshape(num_joints, 3) if num_joints > 0 else np.array(vals)\n"
    elif shape == "2D_features":
         logic += "        # 2D Array of Features. Each CHOP channel is a feature.\n"
         logic += "        vals = [c.eval() for c in chop_in.chans()]\n"
    elif shape == "3D_window":
         logic += "        # 3D Array of (Time, Signals, Dims). We assume incoming CHOP is (Signals * Dims).\n"
         logic += "        vals = [c.eval() for c in chop_in.chans()]\n"
         logic += "        num_joints = len(vals) // 3\n"
         logic += "        # Reshape to (N_joints, 3) for the current frame\n"
         logic += "        vals = np.array(vals).reshape(num_joints, 3) if num_joints > 0 else np.array(vals)\n"

    if requires_window:
         logic += "        self.sliding_window.append([vals])\n"
         logic += "        if self.sliding_window.is_full():\n"
         logic += "            # Some features expect pure numpy array, some expect SlidingWindow object.\n"
         logic += "            # PyEyesweb typically accepts numpy array through compute(), or SlidingWindow through __call__().\n"
         logic += "            try:\n"
         logic += "                return self.analyzer.compute(self.sliding_window.to_array()[0])\n"
         logic += "            except:\n"
         logic += "                return self.analyzer(self.sliding_window)\n"
    else:
         logic += "        return self.analyzer.compute(vals)\n"
         
    logic += "        return None"
    return logic


def generate_node_config():
    config = []
    
    if not os.path.exists("dist_extensions"):
        os.makedirs("dist_extensions")

    for class_name, meta in DATA_ROUTER.items():
        module_name = meta["module"]
        
        try:
            module = importlib.import_module(module_name)
            target_class = getattr(module, class_name)
        except ImportError as e:
            print(f"Skipping {class_name}: Could not import - {e}")
            continue

        sig = inspect.signature(target_class.__init__)
        
        node_def = {
            "name": class_name,
            "inputs": meta["inputs"],
            "parameters": []
        }
        
        init_params = ""
        constructor_args_list = []
        param_handlers = ""
        
        # Add sliding window max length parameter if needed
        if meta.get("requires_window"):
            node_def["parameters"].append({
                "name": "Slidingwindowlength",
                "label": "Window Length",
                "type": "Int",
                "default": meta.get("default_window_size", 100)
            })
            init_params += f"        self.sliding_window_length = int(self.ownerComp.par.Slidingwindowlength.eval())\n"
            param_handlers += f"            'Slidingwindowlength': lambda v: setattr(self, 'sliding_window_length', int(v)),\n"
        
        for name, param in sig.parameters.items():
            if name == "self" or name == "args" or name == "kwargs":
                continue
                
            default_val = param.default if param.default != inspect.Parameter.empty else 0
            td_type = get_td_param_type(param.annotation)
            
            # Formatting TD param names strictly: First letter uppercase, rest lowercase and numbers only
            td_param_name = name.replace("_", "").replace(" ", "").lower()
            if td_param_name:
                td_param_name = td_param_name[0].upper() + td_param_name[1:]
            
            node_def["parameters"].append({
                "name": td_param_name,
                "label": name.replace("_", " ").title(),
                "type": td_type,
                "default": default_val
            })
            
            cast_func = "int" if td_type == "Int" else "float" if td_type == "Float" else "str"
            if td_type == "Toggle": cast_func = "bool"
            
            init_params += f"        self.{name} = {cast_func}(self.ownerComp.par.{td_param_name}.eval())\n"
            constructor_args_list.append(f"{name}=self.{name}")
            
            # The handler needs to update the local property AND the analyzer object if it exists
            handler_str = f"            '{td_param_name}': lambda v: (\n"
            handler_str += f"                setattr(self, '{name}', {cast_func}(v)),\n"
            handler_str += f"                setattr(self.analyzer, '{name}', {cast_func}(v))\n"
            handler_str += f"            ),\n"
            param_handlers += handler_str

        import_window_str = "from pyeyesweb.data_models.sliding_window import SlidingWindow" if meta.get("requires_window") else ""
        init_window_str = f"\n        self.sliding_window = SlidingWindow(max_length=self.sliding_window_length, n_columns=1) # TODO shape" if meta.get("requires_window") else ""
        
        # Generate the Python Extension string
        ext_code = EXTENSION_TEMPLATE.format(
            class_name=class_name,
            module_name=module_name,
            import_window=import_window_str,
            init_params=init_params,
            constructor_args=", ".join(constructor_args_list),
            init_window=init_window_str,
            param_handlers=param_handlers,
            process_logic=infer_process_logic(meta)
        )
        
        # Save extension to disk
        ext_filename = f"dist_extensions/{class_name.lower()}ext.py"
        with open(ext_filename, "w") as f:
            f.write(ext_code)
            
        node_def["extension_file"] = ext_filename
        config.append(node_def)
        
        print(f"Generated {ext_filename}")

    # Save the configuration dictionary
    with open("td_node_config.json", "w") as f:
        json.dump(config, f, indent=4)
        
    print("Generated td_node_config.json")


if __name__ == "__main__":
    # In practice, you might need to adjust sys.path here to import pyeyesweb 
    # if it's not installed in the system environment
    generate_node_config()
