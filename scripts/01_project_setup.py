"""
01_project_setup.py
Inspect the current ArcGIS Pro project and locate the Haltestelle layer.
Run this inside ArcGIS Pro's Python environment / Notebook.
"""

import arcpy

aprx = arcpy.mp.ArcGISProject("CURRENT")

print(f"ArcGIS Pro project: {aprx.filePath}")

maps = aprx.listMaps()
for m in maps:
    print(f"MAP: {m.name}")
    for layer in m.listLayers():
        print(f"    {layer.name}")

haltestelle = None
for m in maps:
    for layer in m.listLayers():
        if layer.name == "haltestelle":
            haltestelle = layer
            break
    if haltestelle:
        break

if haltestelle is None:
    raise RuntimeError("Layer 'haltestelle' wurde nicht gefunden.")

print(f"Haltestelle datasource: {haltestelle.dataSource}")

print("\nFields:")
for field in arcpy.ListFields(haltestelle):
    print(f"{field.name} → {field.type}")

with arcpy.da.SearchCursor(haltestelle, ["stop_id"]) as cursor:
    stop_ids = [row[0] for row in cursor]

print(f"\nAnzahl Haltestellen: {len(stop_ids)}")
print("Erste 10 stop_id:")
print(stop_ids[:10])
