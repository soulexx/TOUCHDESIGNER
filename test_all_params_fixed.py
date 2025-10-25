#!/usr/bin/env python3
"""Korrigierter Test für alle DMX 16-bit Parameter"""

from src.s2l_unit import dmx_parser, dmx_map

print("=== Test aller 16-bit Parameter (korrekt) ===\n")

params_16bit = [p for p in dmx_map.parameters() if p.dmx_slot_count == 2]

for param in params_16bit:
    print(f"{param.name} (Slots {param.dmx_slot_start}-{param.dmx_slot_start+1}, Range: {param.value_range[0]}-{param.value_range[1]})")

    # Buffer mit 19 Slots (genug für alle Parameter)
    # Test Minimum (0,0)
    buffer = bytearray([0] * 19)
    slot_idx = param.dmx_slot_start - 1
    buffer[slot_idx] = 0
    buffer[slot_idx + 1] = 0
    result_min = dmx_parser.decode_parameter(bytes(buffer), param, offset=0, scaling=True)
    print(f"  DMX [0,0] → {result_min} (erwartet: {param.value_range[0]})")

    # Test Maximum (255,255)
    buffer = bytearray([0] * 19)
    buffer[slot_idx] = 255
    buffer[slot_idx + 1] = 255
    result_max = dmx_parser.decode_parameter(bytes(buffer), param, offset=0, scaling=True)
    print(f"  DMX [255,255] → {result_max} (erwartet: {param.value_range[1]})")

    # Test Mitte (128,0)
    buffer = bytearray([0] * 19)
    buffer[slot_idx] = 128
    buffer[slot_idx + 1] = 0
    result_mid = dmx_parser.decode_parameter(bytes(buffer), param, offset=0, scaling=True)
    expected_mid = param.value_range[0] + int((param.value_range[1] - param.value_range[0]) / 2)
    print(f"  DMX [128,0] → {result_mid} (ca. Mitte, erwartet ~{expected_mid})")

    print()
