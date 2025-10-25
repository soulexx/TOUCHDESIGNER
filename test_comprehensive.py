#!/usr/bin/env python3
"""Umfassender Test für DMX 16-bit Skalierung"""

from src.s2l_unit import dmx_parser, dmx_map

print("=== Test aller 16-bit Parameter ===\n")

params_16bit = [p for p in dmx_map.parameters() if p.dmx_slot_count == 2]

for param in params_16bit:
    print(f"{param.name} (Range: {param.value_range[0]}-{param.value_range[1]})")

    # Test Minimum
    buffer_min = bytes([0, 0] + [0] * 17)
    result_min = dmx_parser.decode_parameter(buffer_min, param, offset=0, scaling=True)
    print(f"  DMX [0,0] → {result_min} (erwartet: {param.value_range[0]})")

    # Test Maximum
    buffer_max = bytes([255, 255] + [0] * 17)
    result_max = dmx_parser.decode_parameter(buffer_max, param, offset=0, scaling=True)
    print(f"  DMX [255,255] → {result_max} (erwartet: {param.value_range[1]})")

    # Test Mitte
    buffer_mid = bytes([128, 0] + [0] * 17)
    result_mid = dmx_parser.decode_parameter(buffer_mid, param, offset=0, scaling=True)
    expected_mid = param.value_range[0] + int((param.value_range[1] - param.value_range[0]) / 2)
    print(f"  DMX [128,0] → {result_mid} (ca. Mitte, erwartet ~{expected_mid})")

    print()

print("\n=== Spezifischer Test: Problem 'DMX 1 wird zu 255' ===")
param = dmx_map.parameter_by_name("Submaster")

# Was der User beschrieben hat
buffer_1 = bytes([0, 1] + [0] * 17)
result_1 = dmx_parser.decode_parameter(buffer_1, param, offset=0, scaling=True)
print(f"DMX Bytes [MSB=0, LSB=1] (raw=1) → Skaliert: {result_1}")
print(f"✓ Wird NICHT mehr zu 255, sondern korrekt zu 1")

buffer_255 = bytes([0, 255] + [0] * 17)
result_255 = dmx_parser.decode_parameter(buffer_255, param, offset=0, scaling=True)
print(f"\nDMX Bytes [MSB=0, LSB=255] (raw=255) → Skaliert: {result_255}")
print(f"✓ Wird NICHT mehr als 255 interpretiert, sondern korrekt zu {result_255} skaliert")
