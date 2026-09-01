"""
05_create_wartungsvertrag.py
Create maintenance contracts for Ausstattung.
"""

import arcpy
import os
import random
from datetime import datetime, timedelta

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
ausstattung = os.path.join(gdb, "Ausstattung")
vertragspartner = os.path.join(gdb, "Vertragspartner")
wartungsvertrag = os.path.join(gdb, "Wartungsvertrag")

for dataset in [ausstattung, vertragspartner, wartungsvertrag]:
    if not arcpy.Exists(dataset):
        raise RuntimeError(f"Nicht gefunden: {dataset}")

with arcpy.da.SearchCursor(ausstattung, ["AusstattungID"]) as cursor:
    ausstattung_ids = [row[0] for row in cursor]

with arcpy.da.SearchCursor(vertragspartner, ["VertragspartnerID"]) as cursor:
    vertragspartner_ids = [row[0] for row in cursor]

vertragsarten = [
    "Wartungsvertrag",
    "Servicevertrag",
    "Rahmenvertrag",
    "Vollwartungsvertrag",
]

heute = datetime.today()


def zufalls_vertragsbeginn():
    return heute - timedelta(days=random.randint(30, 5 * 365))


def zufalls_vertragsende(beginn):
    return beginn + timedelta(days=random.randint(365, 3 * 365))


nummer = 1

with arcpy.da.InsertCursor(
    wartungsvertrag,
    [
        "VertragID",
        "AusstattungID",
        "VertragspartnerID",
        "Vertragsbeginn",
        "Vertragsende",
        "Vertragsart",
        "Jaehrliche_Kosten",
    ],
) as cursor:

    for ausstattung_id in ausstattung_ids:
        anzahl = random.randint(1, 2)

        for _ in range(anzahl):
            vertrag_id = f"V{nummer:05d}"
            vertragspartner_id = random.choice(vertragspartner_ids)
            beginn = zufalls_vertragsbeginn()
            ende = zufalls_vertragsende(beginn)
            vertragsart = random.choice(vertragsarten)
            jaehrliche_kosten = round(random.uniform(500, 10000), 2)

            cursor.insertRow([
                vertrag_id,
                ausstattung_id,
                vertragspartner_id,
                beginn,
                ende,
                vertragsart,
                jaehrliche_kosten,
            ])

            nummer += 1

print("Wartungsvertrag erstellt.")
print(f"Anzahl: {nummer - 1}")
