"""
04_create_vertragspartner.py
Populate the Vertragspartner table.
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
vertragspartner = os.path.join(gdb, "Vertragspartner")

if not arcpy.Exists(vertragspartner):
    raise RuntimeError(f"Vertragspartner nicht gefunden: {vertragspartner}")

vertragspartner_daten = [
    ["VP001", "Siemens Mobility", "Thomas Mueller", "+49 721 100001", "Fahrkartenautomaten"],
    ["VP002", "INIT SE", "Michael Schneider", "+49 721 100002", "Fahrgastinformation"],
    ["VP003", "Hoermann", "Stefan Weber", "+49 721 100003", "Wetterschutz"],
    ["VP004", "Scheidt & Bachmann", "Andreas Fischer", "+49 721 100004", "Fahrkartenautomaten"],
    ["VP005", "Signify", "Daniel Klein", "+49 721 100005", "Beleuchtung"],
    ["VP006", "RTB GmbH", "Thomas Bauer", "+49 721 100006", "Blindenleitsystem"],
    ["VP007", "Strabag", "Markus Wagner", "+49 721 100007", "Haltestelleninfrastruktur"],
    ["VP008", "Kienzler", "Peter Hoffmann", "+49 721 100008", "Fahrradabstellanlagen"],
    ["VP009", "Vossloh", "Frank Richter", "+49 721 100009", "Verkehrsinfrastruktur"],
    ["VP010", "SWARCO", "Christian Wolf", "+49 721 100010", "Verkehrstechnik"],
]

with arcpy.da.InsertCursor(
    vertragspartner,
    [
        "VertragspartnerID",
        "Firmenname",
        "Ansprechpartner",
        "Telefon",
        "Zustaendigkeitsbereich",
    ],
) as cursor:

    for row in vertragspartner_daten:
        cursor.insertRow(row)

print("Vertragspartner erstellt.")
print(f"Anzahl: {arcpy.management.GetCount(vertragspartner)}")
