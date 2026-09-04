# kvv-transit-asset-geodatabase-model

Geodatabase data model & cartographic analysis for KVV (Karlsruhe) transit stop equipment, maintenance, and service contracts — built with ArcGIS Pro, Arcade attribute rules, and GTFS data

---

## Data Sources

| Dataset | Source | License | Notes |
|---|---|---|---|
| GTFS (stops) | [projekte.kvv-efa.de/GTFS/google_transit.zip](https://projekte.kvv-efa.de/GTFS/google_transit.zip) | CC0 | Updated almost daily (~7 MB). Only `stops.txt` is used. Alternative access: [kvv.de/fahrplan/fahrplaene/open-data.html](https://www.kvv.de/fahrplan/fahrplaene/open-data.html) |
| Administrative boundary | [BKG WFS – VG25](https://sgx.geodatenzentrum.de/wfs_vg25) (via [gdz.bkg.bund.de](https://gdz.bkg.bund.de/index.php)) | Official German federal source | `Regierungsbezirk` layer, filtered to Karlsruhe |
| Tram / light rail geometry | [OpenStreetMap](https://www.openstreetmap.org) via [Overpass API](https://overpass-turbo.eu) | ODbL | GTFS feed has no `shapes.txt`, so line geometry was extracted separately via Overpass QL (see query below) |

⚠️ **Note:** the GTFS link is a live feed and may change over time — if the direct download breaks, use the alternative KVV Open Data page above.

**Overpass QL query used** (also saved as [`scripts/tram_light_rail_query.overpassql`](scripts/tram_light_rail_query.overpassql)):

```overpassql
[out:json][timeout:60];
(
  way["railway"="tram"](48.43,7.90,49.36,9.53);
  way["railway"="light_rail"](48.43,7.90,49.36,9.53);
);
out geom;
```

---

## Tech Stack

- **ArcGIS Pro** — geodatabase design, geoprocessing, cartography
- **Arcade** — Attribute Rules (Constraint / Calculation / Validation)
- **QGIS** — WFS extraction for the administrative boundary; QuickOSM for Overpass queries
- **Python (arcpy)** — synthetic data generation for equipment/maintenance tables
- **Overpass API** — tram/light rail line geometry from OpenStreetMap

---
## Workflow

### 1. Data acquisition
- Downloaded the KVV GTFS feed and extracted only stops.txt (stop_id, stop_name, stop_lat, stop_lon, location_type)
- Retrieved the Karlsruhe administrative boundary from the BKG WFS server (Regierungsbezirk layer), filtered and exported in QGIS, then loaded into ArcGIS Pro

### 2. Project setup
- Created ArcGIS Pro project with folders: GTFS_raw, Geodatabase, Excel_synthetic, Layouts
- Created File Geodatabase **Karlsruhe.gdb**
- Created Feature Dataset **Haltestellennetz*ETRS89 / UTM zone 32N (EPSG:25832)25832)**

### 3. Building the stop layer
- Converted stops.txt to pointXY Table To Point Point** (input CRS: WGS84 / EPSG:4326, as GTFS coordinates are always geographic)
- ReprojeEPSG:25832:25832*Projectroject**
- Copied into the Haltestellennetz dataset as **Haltestelle** via **Feature Class To Feature Class**
- Kept only the relevant fistop_ideld: **stop_id**

### 4. Data model schema

| Table | Type | Relationship |
Haltestelle **Haltestelle** | Point Feature Class (froAusstattung **Ausstattung** | Standalone Table | 1:M with Wartung |
| **Wartung** | Standalone Table | 1:M with Vertragspartnerertragspartner** | StandalonWartungsvertragartungsvertrag** | Standalone Table (junction) | M:N between Ausstattung ↔ Vertragspartner |

### 5. Empty table creation
Created the following standalone tables inside the geodatabase (via the Create Table wizard / Fields view). GlobalIDs were enabled on all of them (required for Attribute Rules).

Ausstattung

| Field | Type |
|---|---|
| AusstattungID | Long Integer |
| HaltestelleID | Long Integer |
| Ausstattungstyp | Short Text |
| Einbaudatum | Date |
| Zustand | Short Text |
| Hersteller | Short Text |

Wartung

| Field | Type |
|---|---|
| WartungID | Long Integer |
| AusstattungID | Long Integer |
| Wartungsdatum | Date |
| Wartungstyp | Short Text |
| Techniker | Short Text |
| Kosten | Double |
| Naechste_Wartung | Date *(populated later via a Calculation Rule)* |

Vertragspartner

| Field | Type |
|---|---|
| VertragspartnerID | Long Integer |
| Firmenname | Short Text |
| Ansprechpartner | Short Text |
| Telefon | Short Text |
| Zustaendigkeitsbereich | Short Text |

Wartungsvertrag *(junction table)*

| Field | Type |
|---|---|
| VertragID | Long Integer |
| AusstattungID | Long Integer |
| VertragspartnerID | Long Integer |
| Vertragsbeginn | Date |
| Vertragsende | Date |
| Vertragsart | Short Text |
| Jaehrliche_Kosten | Double |

---
### 6. Synthetic equipment data generation (Python)

Instead of manually generating data in Excel, synthetic `Ausstattung` records were created programmatically using **ArcGIS Pro's Python Notebook** (`arcpy`), reading directly from the real `Haltestelle` layer (built from GTFS `stop_id` values).

**6.1 — Verify the Python Notebook has access to the project**

```python
import arcpy

aprx = arcpy.mp.ArcGISProject("CURRENT")
print(aprx.filePath)
```

**6.2 — Locate the `Haltestelle` layer**

```python
maps = aprx.listMaps()

for m in maps:
    print("MAP:", m.name)
    for layer in m.listLayers():
        print("   ", layer.name)
```

**6.3 — Confirm the `stop_id` field and its type**

```python
haltestelle = None

for m in maps:
    for layer in m.listLayers():
        if layer.name == "Haltestelle":
            haltestelle = layer
            break

print(haltestelle.dataSource)

fields = arcpy.ListFields(haltestelle)
for field in fields:
    print(field.name, "→", field.type)
```

Confirmed `stop_id → String`, consistent with the GTFS source data.

**6.4 — Read all `stop_id` values into a list**

```python
stop_ids = []

with arcpy.da.SearchCursor(haltestelle, ["stop_id"]) as cursor:
    for row in cursor:
        stop_ids.append(row[0])

print("Total stops:", len(stop_ids))
print("First 10 IDs:", stop_ids[:10])
```

> **Note:** at this stage no data was modified — only the real `stop_id` values were extracted from the `Haltestelle` point layer into a Python list, to be used as the foreign key basis for the synthetic `Ausstattung` records generated in the next step.
**6.5 — Create the `Ausstattung` table and its fields**

Created via **Catalog → Databases → `Karlsruhe.gdb` → Right-click → New → Table**, named `Ausstattung`.

| Field Name | Data Type | Notes |
|---|---|---|
| `AusstattungID` | Text | Equipment ID |
| `HaltestelleID` | Text | Links to `Haltestelle.stop_id` — **must be Text**, since `stop_id` values look like `de:07334:1714:1:1` |
| `Ausstattungstyp` | Text | Equipment type |
| `Einbaudatum` | Date | Installation date |
| `Zustand` | Text | Condition |
| `Hersteller` | Text | Manufacturer |

> GlobalIDs were deferred at this stage and added later once Relationship Classes / Attribute Rules were set up.

**6.6 — Locate the `Ausstattung` table path and verify it exists**

```python
gdb = arcpy.Describe(haltestelle).path
ausstattung = gdb + r"\Ausstattung"

print(ausstattung)
print(arcpy.Exists(ausstattung))
```

**6.7 — Define the synthetic value pools**

```python
ausstattungstypen = [
    "Fahrkartenautomat", "Wetterschutzhaus", "Beleuchtung",
    "Blindenleitsystem", "Dynamische Fahrgastinformation",
    "Fahrradabstellanlage"
]

zustaende = ["Neu", "Gut", "Mittel", "Reparaturbeduerftig", "Defekt"]

hersteller = ["Siemens", "Scheidt & Bachmann", "INIT SE", "Hoermann"]
```

**6.8 — Random installation date generator**

```python
from datetime import datetime, timedelta
import random

heute = datetime.today()

def zufalls_datum():
    tage = random.randint(30, 3650)
    return heute - timedelta(days=tage)
```

**6.9 — Populate `Ausstattung` for every `Haltestelle` (1–4 items each)**

```python
with arcpy.da.InsertCursor(
    ausstattung,
    ["AusstattungID", "HaltestelleID", "Ausstattungstyp", "Einbaudatum", "Zustand", "Hersteller"]
) as cursor:

    nummer = 1

    for stop_id in stop_ids:
        anzahl = random.randint(1, 4)

        for i in range(anzahl):
            ausstattung_id = f"A{nummer:05d}"

            cursor.insertRow([
                ausstattung_id,
                stop_id,
                random.choice(ausstattungstypen),
                zufalls_datum(),
                random.choice(zustaende),
                random.choice(hersteller)
            ])

            nummer += 1

print("Ausstattung created. Total rows:", nummer - 1)
```

Each of the 5,865 real `Haltestelle` records received 1–4 randomly generated `Ausstattung` entries — a true **1:M relationship**, with `HaltestelleID` (`stop_id`) repeating across multiple equipment rows by design.

Example result:

| AusstattungID | HaltestelleID | Ausstattungstyp | Einbaudatum | Zustand | Hersteller |
|---|---|---|---|---|---|
| A00001 | de:07334:1714:1:1 | Beleuchtung | 2023-04-12 | Gut | Siemens |
| A00002 | de:07334:1714:1:1 | Fahrkartenautomat | 2021-08-21 | Mittel | INIT SE |
| A00003 | de:07334:1721:1:1 | Blindenleitsystem | 2022-06-13 | Gut | Scheidt & Bachmann |

> This replaced the earlier Excel-based synthetic data plan entirely — `stop_id` values are read directly from the geodatabase and written back via `arcpy.da.InsertCursor`, with no manual copy-paste step.
**6.10 — Locate the `Ausstattung` table path**

```python
gdb = arcpy.Describe(haltestelle).path
print(gdb)

ausstattung = gdb + r"\Ausstattung"
print(ausstattung)
```

**6.11 — Verify the `Ausstattung` table exists**

```python
print(arcpy.Exists(ausstattung))
```

**6.12 — Define the synthetic value pools**

```python
ausstattungstypen = [
    "Fahrkartenautomat", "Wetterschutzhaus", "Beleuchtung",
    "Blindenleitsystem", "Dynamische Fahrgastinformation",
    "Fahrradabstellanlage"
]

zustaende = ["Neu", "Gut", "Mittel", "Reparaturbeduerftig", "Defekt"]

hersteller = ["Siemens", "Scheidt & Bachmann", "INIT SE", "Hoermann"]
```

**6.13 — Random installation date generator**

```python
heute = datetime.today()

def zufalls_datum():
    tage = random.randint(30, 3650)
    return heute - timedelta(days=tage)
```

**6.14 — Populate `Ausstattung` for every `Haltestelle` (1–4 items each)**

```python
with arcpy.da.InsertCursor(
    ausstattung,
    ["AusstattungID", "HaltestelleID", "Ausstattungstyp", "Einbaudatum", "Zustand", "Hersteller"]
) as cursor:

    nummer = 1

    for stop_id in stop_ids:
        anzahl = random.randint(1, 4)

        for i in range(anzahl):
            ausstattung_id = f"A{nummer:05d}"

            cursor.insertRow([
                ausstattung_id,
                stop_id,
                random.choice(ausstattungstypen),
                zufalls_datum(),
                random.choice(zustaende),
                random.choice(hersteller)
            ])

            nummer += 1

print("Ausstattung created. Total rows:", nummer - 1)
```

Each of the 5,865 real `Haltestelle` records received 1–4 randomly generated `Ausstattung` entries — a true **1:M relationship**, with `HaltestelleID` (`stop_id`) repeating across multiple equipment rows by design.
**Result check for `Ausstattung`:**

```python
print(arcpy.management.GetCount(ausstattung))
```

Produced ~14,000–15,000 synthetic `Ausstattung` records across 5,865 real stops (1–4 per stop, randomly distributed).

---

### 7. Maintenance (`Wartung`) table

Models the relationship: **1 `Ausstattung` → M `Wartung`** — a single piece of equipment can have multiple maintenance events (or none).

| Field | Type |
|---|---|
| `WartungID` | Text |
| `AusstattungID` | Text |
| `Wartungsdatum` | Date |
| `Wartungstyp` | Text |
| `Techniker` | Text |
| `Kosten` | Double |
| `Naechste_Wartung` | Date |

```python
import os

wartung = os.path.join(gdb, "Wartung")
print(arcpy.Exists(wartung))

# Read all Ausstattung IDs as the foreign key basis
ausstattung_ids = []
with arcpy.da.SearchCursor(ausstattung, ["AusstattungID"]) as cursor:
    for row in cursor:
        ausstattung_ids.append(row[0])

print("Ausstattung count:", len(ausstattung_ids))

wartungstypen = ["Inspektion", "Reparatur", "Wartung", "Austausch", "Sicherheitspruefung"]
techniker = ["Thomas Mueller", "Michael Schneider", "Stefan Weber", "Andreas Fischer", "Daniel Klein"]

with arcpy.da.InsertCursor(
    wartung,
    ["WartungID", "AusstattungID", "Wartungsdatum", "Wartungstyp", "Techniker", "Kosten", "Naechste_Wartung"]
) as cursor:

    nummer = 1

    for ausstattung_id in ausstattung_ids:
        anzahl = random.randint(0, 3)  # not every device has a maintenance record

        for i in range(anzahl):
            wartungsdatum = zufalls_datum()
            naechste_wartung = wartungsdatum + timedelta(days=random.randint(180, 730))
            kosten = round(random.uniform(50, 2500), 2)

            cursor.insertRow([
                f"W{nummer:05d}",
                ausstattung_id,
                wartungsdatum,
                random.choice(wartungstypen),
                random.choice(techniker),
                kosten,
                naechste_wartung
            ])

            nummer += 1

print("Wartung created. Total:", nummer - 1)
```

Each `Ausstattung` record received **0–3** maintenance events — deliberately including zero, since not every device requires servicing yet.

---

### 8. `Vertragspartner` table

A small reference table of service/contract companies.

Created via **Catalog → `Karlsruhe.gdb` → Right-click → New → Table**, named `Vertragspartner`.

| Field Name | Data Type | Length | Notes |
|---|---|---|---|
| `VertragspartnerID` | Text | 10 | Primary ID (e.g. `VP001`) |
| `Firmenname` | Text | 100 | Company name |
| `Ansprechpartner` | Text | 100 | Contact person |
| `Telefon` | Text | 30 | Phone number |
| `Zustaendigkeitsbereich` | Text | 100 | Area of responsibility |

**Verify the table exists:**

```python
vertragspartner = os.path.join(gdb, "Vertragspartner")
print(vertragspartner)
print(arcpy.Exists(vertragspartner))
```

**Populate with 10 synthetic companies:**

```python
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
    ["VP010", "SWARCO", "Christian Wolf", "+49 721 100010", "Verkehrstechnik"]
]

with arcpy.da.InsertCursor(
    vertragspartner,
    ["VertragspartnerID", "Firmenname", "Ansprechpartner", "Telefon", "Zustaendigkeitsbereich"]
) as cursor:
    for row in vertragspartner_daten:
        cursor.insertRow(row)

print("Vertragspartner created. Total:", arcpy.management.GetCount(vertragspartner))
```
---

### 9. `Wartungsvertrag` (junction table)

Models the **M:N** relationship between `Ausstattung` and `Vertragspartner` — a piece of equipment can have multiple contracts over time (e.g. one contractor 2023–2025, another 2025–2027), and one company can be responsible for many pieces of equipment. Storing the contractor ID directly on `Ausstattung` would not support this, hence a dedicated junction table.

Created via **Catalog → `Karlsruhe.gdb` → Right-click → New → Table**, named `Wartungsvertrag`.

| Field Name | Data Type | Length |
|---|---|---|
| `VertragID` | Text | 10 |
| `AusstattungID` | Text | 10 |
| `VertragspartnerID` | Text | 10 |
| `Vertragsbeginn` | Date | — |
| `Vertragsende` | Date | — |
| `Vertragsart` | Text | 50 |
| `Jaehrliche_Kosten` | Double | — |

> `AusstattungID` and `VertragspartnerID` values must match the real IDs already generated in the `Ausstattung` (`A00001`, `A00002`, …) and `Vertragspartner` (`VP001`–`VP010`) tables.

**Verify the table exists:**

```python
wartungsvertrag = os.path.join(gdb, "Wartungsvertrag")
print(wartungsvertrag)
print(arcpy.Exists(wartungsvertrag))
```

**Helper functions for contract dates:**

```python
def zufalls_vertragsbeginn():
    # contract start within the last 5 years
    return heute - timedelta(days=random.randint(30, 5 * 365))

def zufalls_vertragsende(beginn):
    # contract duration: 1–3 years
    return beginn + timedelta(days=random.randint(365, 3 * 365))

vertragsarten = ["Wartungsvertrag", "Servicevertrag", "Rahmenvertrag", "Vollwartungsvertrag"]
```

**Populate `Wartungsvertrag` — 1–2 contracts per equipment item:**

```python
vertragspartner_ids = [row[0] for row in vertragspartner_daten]
print(vertragspartner_ids)

with arcpy.da.InsertCursor(
    wartungsvertrag,
    ["VertragID", "AusstattungID", "VertragspartnerID", "Vertragsbeginn",
     "Vertragsende", "Vertragsart", "Jaehrliche_Kosten"]
) as cursor:

    nummer = 1

    for ausstattung_id in ausstattung_ids:
        anzahl = random.randint(1, 2)

        for i in range(anzahl):
            beginn = zufalls_vertragsbeginn()
            ende = zufalls_vertragsende(beginn)
            jaehrliche_kosten = round(random.uniform(500, 10000), 2)

            cursor.insertRow([
                f"V{nummer:05d}",
                ausstattung_id,
                random.choice(vertragspartner_ids),
                beginn,
                ende,
                random.choice(vertragsarten),
                jaehrliche_kosten
            ])

            nummer += 1

print("Wartungsvertrag created. Total:", nummer - 1)
```
### 10. Relationship Classes

Creating the tables alone isn't enough — ArcGIS doesn't yet know that `Ausstattung.HaltestelleID` refers to `Haltestelle`, or that `Wartungsvertrag` links `Ausstattung` and `Vertragspartner`. **Relationship Classes** make these connections explicit.

Four relationship classes were created via **`Karlsruhe.gdb` → New → Relationship Class**:

| # | Name | Origin → Destination | Cardinality | Primary Key | Foreign Key |
|---|---|---|---|---|---|
| 1 | `rel_Haltestelle_Ausstattung` | `Haltestelle` → `Ausstattung` | ONE_TO_MANY | `HaltestelleID` | `HaltestelleID` |
| 2 | `rel_Ausstattung_Wartung` | `Ausstattung` → `Wartung` | ONE_TO_MANY | `AusstattungID` | `AusstattungID` |
| 3 | `rel_Ausstattung_Wartungsvertrag` | `Ausstattung` → `Wartungsvertrag` | ONE_TO_MANY | `AusstattungID` | `AusstattungID` |
| 4 | `rel_Vertragspartner_Wartungsvertrag` | `Vertragspartner` → `Wartungsvertrag` | ONE_TO_MANY | `VertragspartnerID` | `VertragspartnerID` |

**Modeling the M:N relationship**

`Ausstattung` and `Vertragspartner` have a true many-to-many relationship (one device can have multiple contractors over time; one contractor serves many devices). ArcGIS relationship classes only support 1:1 and 1:M directly, so the M:N is implemented through the `Wartungsvertrag` junction table via two 1:M relationships (#3 and #4 above):
### Domains

To keep text fields consistent (preventing entries like `GUT`, `good`, `g` instead of `Gut`), three coded-value domains were created at the geodatabase level and attached to their fields:

| Domain | Field | Attached to | Values |
|---|---|---|---|
| `Zustand_Domain` | `Zustand` | `Ausstattung` | Neu, Gut, Mittel, Reparaturbeduerftig, Defekt |
| `Wartungstyp_Domain` | `Wartungstyp` | `Wartung` | Inspektion, Reparatur, Wartung, Austausch, Sicherheitspruefung |
| `Vertragsart_Domain` | `Vertragsart` | `Wartungsvertrag` | Wartungsvertrag, Servicevertrag, Rahmenvertrag, Vollwartungsvertrag |

### Attribute Rules

Four Arcade-based Attribute Rules enforce data integrity beyond what domains and field types can guarantee:

**1. Calculation Rule — auto-compute next maintenance date**

`Wartung → Data Design → Attribute Rules → Add Rule`

| | |
|---|---|
| Rule Type | Calculation |
| Name | `Berechne_Naechste_Wartung` |
| Field | `Naechste_Wartung` |

```javascript
if (IsEmpty($feature.Wartungsdatum)) {
    return null;
}
return DateAdd($feature.Wartungsdatum, 365, 'days');
```

Automatically sets `Naechste_Wartung` to one year after `Wartungsdatum` (e.g. 20.08.2026 → 20.08.2027).

**2. Constraint Rule — contract end date must not precede start date**

| | |
|---|---|
| Table | `Wartungsvertrag` |
| Rule Type | Constraint |
| Name | `Vertragsende_muss_nach_Beginn_liegen` |

```javascript
IsEmpty($feature.Vertragsbeginn) ||
IsEmpty($feature.Vertragsende) ||
$feature.Vertragsende >= $feature.Vertragsbeginn
```

**3. Constraint Rule — annual cost cannot be negative**

| | |
|---|---|
| Table | `Wartungsvertrag` |
| Rule Type | Constraint |
| Name | `Jaehrliche_Kosten_muss_positiv_sein` |

```javascript
$feature.Jaehrliche_Kosten >= 0
```

**4. Constraint Rule — maintenance cost cannot be negative**

| | |
|---|---|
| Table | `Wartung` |
| Rule Type | Constraint |
| Field | `Kosten` |

```javascript
$feature.Kosten >= 0
```
### 11. Final data model

```
Karlsruhe.gdb
│
├── Haltestelle
│   └── GlobalID
│
├── Ausstattung
│   └── GlobalID
│
├── Wartung
│   └── GlobalID
│
├── Vertragspartner
│   └── GlobalID
│
├── Wartungsvertrag
│   └── GlobalID
│
├── Domains
│   ├── Zustand_Domain
│   ├── Wartungstyp_Domain
│   └── Vertragsart_Domain
│
└── Relationship Classes
    ├── Haltestelle → Ausstattung
    ├── Ausstattung → Wartung
    ├── Ausstattung → Wartungsvertrag
    └── Vertragspartner → Wartungsvertrag
Haltestelle
│
│ 1:M
▼
Ausstattung
│
├──────── 1:M ────────> Wartung
│
└──────── 1:M ────────> Wartungsvertrag <──── 1:M ──── Vertragspartner
```



---

## License

This project is licensed under the [MIT License](LICENSE). 
