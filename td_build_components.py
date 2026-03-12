# td_build_components.py
# Run this script INSIDE TouchDesigner (e.g. from a Text DAT)
# It reads td_node_config.json and generates the Base COMPs.

import json
import os

def build_nodes():
    # Attempt to load the config from the project directory
    config_path = "td_node_config.json"
    if not os.path.exists(config_path):
        config_path = project.folder + "/td_node_config.json"
        
    if not os.path.exists(config_path):
        print("ERROR: Cannot find td_node_config.json. Run generate_extensions.py first.")
        return

    with open(config_path, 'r') as f:
        config = json.load(f)

    # We will build these inside the current parent component usually
    parent_comp = parent()
    
    # Layout offset
    x_offset = 0

    for node_def in config:
        name = node_def["name"]
        print(f"Building {name}...")

        # 1. Create Base COMP
        comp = parent_comp.create(baseCOMP, name.lower() + "_node")
        comp.nodeX = x_offset
        comp.nodeY = -200
        x_offset += 200

        # 2. Add Custom Parameters
        page = comp.appendCustomPage('PyEyesWeb')
        
        for p in node_def["parameters"]:
            p_type = p["type"]
            p_name = p["name"]
            p_label = p["label"]
            p_default = p["default"]

            print(p_name)
            
            # Map type string to TD tuple method
            if p_type == "Int":
                new_p = page.appendInt(p_name, label=p_label)[0]
                try:
                    new_p.default = int(p_default)
                    new_p.val = int(p_default)
                except:
                    pass
            elif p_type == "Float":
                new_p = page.appendFloat(p_name, label=p_label)[0]
                try:
                    new_p.default = float(p_default)
                    new_p.val = float(p_default)
                except:
                    pass
            elif p_type == "Toggle":
                new_p = page.appendToggle(p_name, label=p_label)[0]
                new_p.default = bool(p_default)
                new_p.val = bool(p_default)
            elif p_type == "Str":
                new_p = page.appendStr(p_name, label=p_label)[0]
                new_p.default = str(p_default)
                new_p.val = str(p_default)
                
        # 3. Add Inputs
        in_offset = 100
        for i, in_def in enumerate(node_def["inputs"]):
            in_node = comp.create(inCHOP, f"in_{i+1}")
            in_node.nodeX = 300
            in_node.nodeY = in_offset
            in_offset += 150
            # Optional: Add a text DAT to label the input?
            
        # Add a Script CHOP for the output (instead of a plain Out CHOP, allow Python to write to it)
        out_node = comp.create(scriptCHOP, "out1")
        out_node.nodeX = 500
        out_node.nodeY = -100
        
        # We need a Script CHOP callback DAT to drive the data processing
        script_callbacks_dat = comp.create(textDAT, "out1_callbacks")
        script_callbacks_dat.nodeX = 500
        script_callbacks_dat.nodeY = -200
        
        # Write the callback code for the Script CHOP
        callbacks_code = "def onSetupParameters(scriptOp):\n"
        callbacks_code += "    pass\n\n"
        callbacks_code += "def onPulse(par):\n"
        callbacks_code += "    return\n\n"
        callbacks_code += "def onCook(scriptOp):\n"
        callbacks_code += f"    if hasattr(parent().ext, '{name}Ext'):\n"
        callbacks_code += f"        result = parent().ext.{name}Ext.process_data()\n"
        callbacks_code += f"        if result is not None:\n"
        callbacks_code += f"            # Assuming result is an object with properties or a dict. Needs adaptation based on PyEyesWeb return types.\n"
        callbacks_code += f"            # For now, if it has a .to_flat_dict() we use that, otherwise if it's a numeric value we map it.\n"
        callbacks_code += f"            scriptOp.clear()\n"
        callbacks_code += f"            if hasattr(result, 'to_flat_dict'):\n"
        callbacks_code += f"                flat_dict = result.to_flat_dict()\n"
        callbacks_code += f"                scriptOp.numSamples = 1\n"
        callbacks_code += f"                for key, val in flat_dict.items():\n"
        callbacks_code += f"                    c = scriptOp.appendChan(key)\n"
        callbacks_code += f"                    c[0] = float(val)\n"
        callbacks_code += f"            elif hasattr(result, '__dict__'):\n"
        callbacks_code += f"                scriptOp.numSamples = 1\n"
        callbacks_code += f"                for key, val in result.__dict__.items():\n"
        callbacks_code += f"                    if isinstance(val, (int, float, bool)):\n"
        callbacks_code += f"                        c = scriptOp.appendChan(key)\n"
        callbacks_code += f"                        c[0] = float(val)\n"
        callbacks_code += "    return\n"
        
        script_callbacks_dat.text = callbacks_code
        out_node.par.callbacks = script_callbacks_dat.name
        
        # Add a standard Out CHOP and wire the Script CHOP to it for easy external connection
        final_out = comp.create(outCHOP, "out_final")
        final_out.nodeX = 700
        final_out.nodeY = -100
        final_out.inputConnectors[0].connect(out_node)
        
        # 4. Inject Python Extension
        ext_file_path = node_def["extension_file"]
        
        # We need to construct absolute path if running inside TD
        abs_ext_file_path = project.folder + "/" + ext_file_path
        
        if os.path.exists(abs_ext_file_path):
            with open(abs_ext_file_path, "r") as f:
                ext_code = f.read()
                
            ext_dat = comp.create(textDAT, f"{name.lower()}ext")
            ext_dat.text = ext_code
            ext_dat.par.language = 3
            ext_dat.nodeX = -200
            ext_dat.nodeY = 0
            
            # Setup Extension on the COMP (Defer by 1 frame to ensure DAT is compiled into a module)
            ext_assign_cmd = f"args[0].par.extension1 = \\\"op('{{args[1]}}').module.{{args[2]}}Ext(me)\\\"; args[0].par.promoteextension1 = True"
            run(ext_assign_cmd, comp, ext_dat.name, name, delayFrames=1)
            
            # Create a Parameter Execute DAT to call the extension's execution method
            parexec_dat = comp.create(parameterexecuteDAT, "parexec1")
            parexec_dat.nodeX = -200
            parexec_dat.nodeY = -150
            parexec_dat.par.custom = True  # Only listen to custom parameters
            parexec_dat.par.builtin = False
            
            # Write the callback code for the Parameter Execute DAT
            parexec_code = "def onValueChange(par, prev):\n"
            parexec_code += f"    if hasattr(parent().ext, '{name}Ext'):\n"
            parexec_code += "        parent().ext." + name + "Ext.par_exec_onValueChange(par)\n"
            parexec_code += "    return\n"
            
            parexec_dat.text = parexec_code
            
        print(f"Successfully built {name}")

    print("PyEyesWeb integration nodes generated!")

# To run: build_nodes()
def onCook(par):
    build_nodes()