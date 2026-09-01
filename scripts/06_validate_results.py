"""
06_validate_results.py
Basic validation of the generated tables.
"""

import arcpy
import os

aprx = arcpy.mp.ArcGISProject("CURRENT")

haltestelle = None
for m in aprx.listMaps():
    for layer in m.listLayers():
        if layer.name == "haltestelle":
            haltestelle = layer
            break
    if haltestelle:
        break

if haltestelle is None:
    raise RuntimeError("Layer 'haltestelle' wurde nicht gefunden.")

gdb = os.path.dirname(arcpy.Describe(haltestelle).path)

datasets = [
    "Ausstattung",
    "Vertragspartner",
    "Wartung",
    "Wartungsvertrag",
]

for name in datasets:
    path = os.path.join(gdb, name)
    if arcpy.Exists(path):
        count = int(arcpy.management.GetCount(path)[0])
        print(f"{name}: {count}")
    else:
        print(f"{name}: NICHT GEFUNDEN")
