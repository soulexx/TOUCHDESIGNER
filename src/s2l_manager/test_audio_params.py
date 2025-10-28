"""Test if audio_params_table is being updated from values table."""

# Force rebuild of audio_params_table
print("=" * 60)
print("REBUILDING audio_params_table...")
print("=" * 60)

import sys
manager_path = 'C:/_DEV/TOUCHDESIGNER/src/s2l_manager'
if manager_path not in sys.path:
    sys.path.insert(0, manager_path)

# Check if audio_params_exec has the build_table function
audio_params_exec = op('/project1/src/s2l_manager/audio_params_exec')
if audio_params_exec:
    print(f"Found audio_params_exec: {audio_params_exec}")

    # Execute the module to load build_table function
    exec(audio_params_exec.text)

    # Call build_table if it exists
    if 'build_table' in dir():
        print("Calling build_table()...")
        build_table()
    else:
        print("ERROR: build_table() not found in current scope")
else:
    print("ERROR: Cannot find /project1/src/s2l_manager/audio_params_exec")

print()

# Check the audio_params_table
audio_params = op('/project1/src/s2l_manager/audio_params_table')
if audio_params:
    print("=" * 60)
    print("audio_params_table content:")
    print("=" * 60)
    print(f"Rows: {audio_params.numRows}, Cols: {audio_params.numCols}")

    # Show all rows
    for i in range(audio_params.numRows):
        row_data = []
        for j in range(audio_params.numCols):
            row_data.append(audio_params[i, j].val)
        print(f"  Row {i}: {' | '.join(row_data)}")
    print("=" * 60)
else:
    print("ERROR: Cannot find /project1/src/s2l_manager/audio_params_table")
