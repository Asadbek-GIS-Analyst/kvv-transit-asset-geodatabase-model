// Overpass QL query — extracts tram and light rail line geometry
// for the KVV (Karlsruhe) network area from OpenStreetMap.
//
// Used because the KVV GTFS feed does not include shapes.txt,
// so line geometry for Tram/Stadtbahn was sourced from OSM instead.
//
// Run via Overpass Turbo (https://overpass-turbo.eu) or QuickOSM plugin in QGIS.
// Bounding box: 48.43,7.90,49.36,9.53 (south,west,north,east)

[out:json][timeout:60];
(
  way["railway"="tram"](48.43,7.90,49.36,9.53);
  way["railway"="light_rail"](48.43,7.90,49.36,9.53);
);
out geom;
