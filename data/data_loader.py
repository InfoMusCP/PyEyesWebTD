import os
import json

def onCook(scriptOp: scriptDAT):
	"""
	Called when the Script DAT needs to cook.
	"""
	scriptOp.clear()
	
	if not scriptOp.inputs:
	    return
	
	inpts = scriptOp.inputs[0]
	
	# 1. Dynamically find MARKER_NAMES row and data offset
	marker_row = None
	data_offset = 0
	
	for r in range(min(20, inpts.numRows)):
	    row = inpts.row(r)
	    if not row: continue
	    val0 = row[0].val.strip()
	    
	    if val0 == 'MARKER_NAMES':
	        marker_row = row
	    elif val0 == 'Frame':
	        data_offset = 1
	        if len(row) > 1 and row[1].val.strip() == 'Time':
	            data_offset = 2
	
	if not marker_row:
	    marker_row = inpts.row(9)  # Fallback to row 9 if not explicitly found

	if not marker_row: 
	    return
	
	# Load JSON
	json_path = os.path.join(project.folder, 'data', "markers_mappings.json")
	
	try:
	    with open(json_path, 'r') as f:
	        body_groups = json.load(f)
	except FileNotFoundError:
	    scriptOp.text = f"Error: JSON not found at {json_path}"
	    return
	
	# 2. Build lookups & mapping
	# Reverse lookup dictionary: {'ARIEL_01': 'Head', ...}
	marker_to_group = {m: g for g, markers in body_groups.items() for m in markers}
	
	# Store column indices as a tuple of lists: { 'Head': ([x_cols], [y_cols], [z_cols]) }
	group_cols = {g: ([], [], []) for g in body_groups}
	
	for col_idx, cell in enumerate(marker_row[1:]):
	    if cell.val in marker_to_group:
	        group = marker_to_group[cell.val]
	        base_idx = data_offset + (col_idx * 3)
	        
	        group_cols[group][0].append(base_idx)     # X columns
	        group_cols[group][1].append(base_idx + 1) # Y columns
	        group_cols[group][2].append(base_idx + 2) # Z columns
	
	# 3. Create Header
	ordered_groups = list(body_groups.keys())
	new_header = [f"{g}_{axis}" for g in ordered_groups for axis in ('x', 'y', 'z')]
	scriptOp.appendRow(new_header)
	
	# Helper function to safely extract floats and average them
	def get_avg(row, indices):
	    vals = []
	    for i in indices:
	        if i < inpts.numCols:
	            try: vals.append(float(row[i].val))
	            except ValueError: pass # Skip empty cells or NaN
	    return round(sum(vals) / len(vals), 3) if vals else float('nan')
	
	# 4. Process Data Rows
	for row_idx in range(1, inpts.numRows):
		source_row = inpts.row(row_idx)
		if not source_row:
			continue
			
		# Skip non-data header rows like 'TRAJECTORY_TYPES' or 'Frame'
		val0 = source_row[0].val.strip()
		if val0 in ('TRAJECTORY_TYPES', 'TRAJECTORY TYPE', 'Frame', 'MARKER_NAMES'):
			continue
			
		# Explicitly skip line 10 (index 9) as it might contain numeric trajectory types 
		# instead of actual numerical frame data
		if row_idx == 9:
			continue

		# Numeric data rows have digits in the first column (Frame number)
		if not val0.lstrip("-").isdigit():
			continue
			
		new_row = []
		
		for group in ordered_groups:
			new_row.extend([
				get_avg(source_row, group_cols[group][0]), # X
				get_avg(source_row, group_cols[group][1]), # Y
				get_avg(source_row, group_cols[group][2])  # Z
			])
		
		scriptOp.appendRow(new_row)
	root.time.end = (inpts.numRows - 1) * 3
	root.time.rangeEnd = (inpts.numRows - 1) * 3
	return
