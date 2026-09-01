"""
02_create_ausstattung.py
Create and populate the Ausstattung table for all Haltestellen.

NOTE:
The source notebook uses randomly generated example data for
Ausstattungstyp, Zustand, Hersteller and Einbaudatum.
"""

import arcpy
import os
import random
from datetime import datetime, timedelta

aprx = arcpy.mp.ArcGISProject("CURRENT")

# Find Haltestelle layer
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

# GDB path
gdb = os.path.dirname(arcpy.Describe(haltestelle).path)
ausstattung = os.path.join(gdb, "Ausstattung")

if not arcpy.Exists(ausstattung):
    raise RuntimeError(f"Ausstattung nicht gefunden: {ausstattung}")

with arcpy.da.SearchCursor(haltestelle, ["stop_id"]) as cursor:
    stop_ids = [row[0] for row in cursor]

ausstattungstypen = [
    "Fahrkartenautomat",
    "Wetterschutzhaus",
    "Beleuchtung",
    "Blindenleitsystem",
    "Dynamische Fahrgastinformation",
    "Fahrradabstellanlage",
]

zustaende = [
    "Neu",
    "Gut",
    "Mittel",
    "Reparaturbeduerftig",
    "Defekt",
]

hersteller = [
    "Siemens",
    "Scheidt & Bachmann",
    "INIT SE",
    "Hoermann",
]

heute = datetime.today()


def zufalls_datum():
    tage = random.randint(30, 3650)
    return heute - timedelta(days=tage)


nummer = 1

with arcpy.da.InsertCursor(
    ausstattung,
    [
        "AusstattungID",
        "HaltestelleID",
        "Ausstattungstyp",
        "Einbaudatum",
        "Zustand",
        "Hersteller",
    ],
) as cursor:

    for stop_id in stop_ids:
        anzahl = random.randint(1, 4)

        for _ in range(anzahl):
            ausstattung_id = f"A{nummer:05d}"
            typ = random.choice(ausstattungstypen)
            zustand = random.choice(zustaende)
            firma = random.choice(hersteller)
            datum = zufalls_datum()

            cursor.insertRow([
                ausstattung_id,
                stop_id,
                typ,
                datum,
                zustand,
                firma,
            ])

            nummer += 1

print("Ausstattung erstellt.")
print(f"Anzahl: {nummer - 1}")
