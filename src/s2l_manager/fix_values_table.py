"""Fix the values table format - it should have 3 columns, not 1."""

print("=" * 60)
print("FIXING values TABLE FORMAT")
print("=" * 60)

values = op('/project1/src/s2l_manager/values')

if not values:
    print("❌ ERROR: values table not found")
else:
    print(f"Current: {values.numRows} rows, {values.numCols} cols")

    # Check if it's the wrong format
    if values.numCols == 1 or (values.numRows > 1 and '\\t' in str(values[1, 0].val)):
        print("⚠️  Detected single-column format with \\t - fixing...")

        # Save the data
        old_data = []
        for r in range(values.numRows):
            old_data.append(values[r, 0].val)

        # Clear and set proper column structure
        values.clear()
        values.setSize(1, 3)  # Start with 1 row, 3 columns
        values[0, 0] = 'instance'
        values[0, 1] = 'parameter'
        values[0, 2] = 'value'

        print(f"✅ Set to 3 columns")
        print(f"   Now: {values.numRows} rows, {values.numCols} cols")

    elif values.numCols >= 3:
        print("✅ Already has 3+ columns")

        # Show first few rows
        print("\nFirst 5 data rows:")
        for r in range(1, min(6, values.numRows)):
            inst = values[r, 0].val
            param = values[r, 1].val
            val = values[r, 2].val
            print(f"  {inst} | {param} | {val}")

    print()
    print("Now trigger the dispatcher to populate:")
    print("exec(open('C:/_DEV/TOUCHDESIGNER/src/s2l_manager/test_direct_handle_universe.py').read())")

print("=" * 60)
