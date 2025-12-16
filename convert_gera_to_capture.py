import csv

# Input und Output Dateipfade
input_file = r"c:\Users\Oliver\Desktop\CAPTURE_PROJECT´s\Gera 0.5\THEATER GERA GRUNDEINRICHTUNG 0.5.1 + JB P18 li.csv"
output_file = r"c:\Users\Oliver\Desktop\CAPTURE_PROJECT´s\Gera 0.5\THEATER_GERA_converted.csv"

# Capture SE Export Header
output_header = [
    'Fixture', 'Optics', 'Wattage', 'Unit', 'Circuit', 'Channel', 'Groups', 'Patch',
    'DMX Mode', 'DMX Channels', 'Layer', 'Focus', 'Filters', 'Gobos', 'Accessories',
    'Purpose', 'Note', 'Weight', 'Location', 'Position X', 'Position Y', 'Position Z',
    'Rotation X', 'Rotation Y', 'Rotation Z', 'Focus Pan', 'Focus Tilt', 'Invert Pan',
    'Pan Start Limit', 'Pan End Limit', 'Invert Tilt', 'Tilt Start Limit', 'Tilt End Limit',
    'Identifier', 'External Identifier'
]

def convert_position(value):
    """Konvertiert Position von Metern zu Metern mit Komma-Format"""
    if not value:
        return ''
    try:
        # Wert ist bereits in Metern, nur Formatierung anpassen mit Komma
        meters = float(value)
        return f"{meters:.3f}m".replace('.', ',')
    except:
        return ''

def convert_rotation(value):
    """Konvertiert Rotation zu Grad-Format"""
    if not value:
        return '0°'
    try:
        degrees = float(value)
        return f"{degrees:.1f}°".replace('.', ',')
    except:
        return '0°'

# CSV einlesen und konvertieren
converted_rows = []

with open(input_file, 'r', encoding='utf-8-sig') as f:
    # Erste Zeile überspringen (START_CHANNELS)
    f.readline()

    # Jetzt die echten Header lesen
    reader = csv.DictReader(f)

    for row in reader:
        # Überspringe Zeilen ohne Channel-Nummer
        if not row.get('CHANNEL', '').strip():
            continue

        # Neue Zeile für Capture SE Format erstellen
        new_row = {
            'Fixture': 'Generic Dimmer',
            'Optics': '',
            'Wattage': '0W',
            'Unit': '',
            'Circuit': '',
            'Channel': row.get('CHANNEL', ''),
            'Groups': '',
            'Patch': (row.get('ADDRESS') or '').strip(),
            'DMX Mode': 'Dimmer',
            'DMX Channels': '1',
            'Layer': row.get('TEXT1', ''),
            'Focus': row.get('LABEL', ''),
            'Filters': '',
            'Gobos': '',
            'Accessories': '',
            'Purpose': '',
            'Note': '',
            'Weight': '0kg',
            'Location': '',
            'Position X': convert_position(row.get('LOCATION_X', '')),
            'Position Y': convert_position(row.get('LOCATION_Y', '')),
            'Position Z': convert_position(row.get('LOCATION_Z', '')),
            'Rotation X': convert_rotation(row.get('ORIENTATION_X', '0.0')),
            'Rotation Y': convert_rotation(row.get('ORIENTATION_Y', '0.0')),
            'Rotation Z': convert_rotation(row.get('ORIENTATION_Z', '0.0')),
            'Focus Pan': '0°',
            'Focus Tilt': '0°',
            'Invert Pan': 'No',
            'Pan Start Limit': '',
            'Pan End Limit': '',
            'Invert Tilt': 'No',
            'Tilt Start Limit': '',
            'Tilt End Limit': '',
            'Identifier': row.get('PATCH_DCID', ''),
            'External Identifier': ''
        }

        converted_rows.append(new_row)

# Output CSV schreiben
with open(output_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=output_header)
    writer.writeheader()
    writer.writerows(converted_rows)

print(f"Konvertierung abgeschlossen!")
print(f"Input: {input_file}")
print(f"Output: {output_file}")
print(f"Anzahl konvertierter Fixtures: {len(converted_rows)}")
