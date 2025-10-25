#!/usr/bin/env python3
"""Test für Skalierungs-Bug in dmx_parser._scale_if_needed"""

from src.s2l_unit import dmx_parser, dmx_map

param = dmx_map.parameter_by_name("Submaster")
print(f"Parameter: {param.name}")
print(f"Value Range: {param.value_range} (min={param.value_range[0]}, max={param.value_range[1]})")
print(f"DMX Slots: {param.dmx_slot_count} (16-bit)\n")

print("=== Test: Skalierung mit scaling=True ===")

# Test verschiedene DMX raw values
test_values = [
    (0, 0, "Minimum DMX"),
    (0, 1, "DMX = 1"),
    (0, 255, "DMX LSB = 255"),
    (1, 0, "DMX MSB = 1"),
    (255, 255, "Maximum DMX"),
]

for msb, lsb, desc in test_values:
    buffer = bytes([msb, lsb] + [0] * 17)
    raw = dmx_parser.decode_parameter(buffer, param, offset=0, scaling=False)
    scaled = dmx_parser.decode_parameter(buffer, param, offset=0, scaling=True)

    # Was sollte es sein?
    expected = 1 + int((raw / 65535.0) * (999 - 1))

    print(f"{desc}:")
    print(f"  DMX [MSB={msb}, LSB={lsb}] → raw={raw}")
    print(f"  Mit scaling=True: {scaled}")
    print(f"  Erwartet: {expected}")

    # BUG CHECK: Wird raw direkt zurückgegeben statt skaliert?
    if raw == scaled and raw != expected:
        print(f"  ❌ BUG: Raw-Wert wurde NICHT skaliert! (raw={raw} ist im Range {param.value_range})")
    elif scaled != expected:
        print(f"  ⚠️  Skalierung anders als erwartet")
    else:
        print(f"  ✓ Korrekt")
    print()
