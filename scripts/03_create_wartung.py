"""
03_create_wartung.py
Create maintenance records for Ausstattung.
"""

import arcpy
import os
import random
from datetime import datetime, timedelta

aprx = arcpy.mp.ArcGISProject("CURRENT")

# Find Haltestelle layer to determine the GDB
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
ausstattung = os.path.join(gdb, "Ausstattung")
wartung = os.path.join(gdb, "Wartung")

if not arcpy.Exists(ausstattung):
    raise RuntimeError(f"Ausstattung nicht gefunden: {ausstattung}")
if not arcpy.Exists(wartung):
    raise RuntimeError(f"Wartung nicht gefunden: {wartung}")

with arcpy.da.SearchCursor(ausstattung, ["AusstattungID"]) as cursor:
    ausstattung_ids = [row[0] for row in cursor]

wartungstypen = [
    "Inspektion",
    "Reparatur",
    "Wartung",
    "Austausch",
    "Sicherheitspruefung",
]

techniker = [
    "Thomas Mueller",
    "Michael Schneider",
    "Stefan Weber",
    "Andreas Fischer",
    "Daniel Klein",
]

heute = datetime.today()


def zufalls_datum():
    tage = random.randint(30, 3650)
    return heute - timedelta(days=tage)


nummer = 1

with arcpy.da.InsertCursor(
    wartung,
    [
        "WartungID",
        "AusstattungID",
        "Wartungsdatum",
        "Wartungstyp",
        "Techniker",
        "Kosten",
        "Naechste_Wartung",
    ],
) as cursor:

    for ausstattung_id in ausstattung_ids:
        anzahl = random.randint(0, 3)

        for _ in range(anzahl):
            wartung_id = f"W{nummer:05d}"
            wartungsdatum = zufalls_datum()
            naechste_wartung = wartungsdatum + timedelta(
                days=random.randint(180, 730)
            )
            typ = random.choice(wartungstypen)
            techniker_name = random.choice(techniker)
            kosten = round(random.uniform(50, 2500), 2)

            cursor.insertRow([
                wartung_id,
                ausstattung_id,
                wartungsdatum,
                typ,
                techniker_name,
                kosten,
                naechste_wartung,
            ])

            nummer += 1

print("Wartung erstellt.")
print(f"Anzahl: {nummer - 1}")
