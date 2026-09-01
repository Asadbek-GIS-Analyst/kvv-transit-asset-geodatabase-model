# Karlsruhe GIS Scripts

The original ArcGIS Pro Notebook was split into focused Python scripts.

## Execution order

1. `01_project_setup.py` — inspect project, map and Haltestelle layer
2. `02_create_ausstattung.py` — populate Ausstattung
3. `03_create_wartung.py` — populate Wartung
4. `04_create_vertragspartner.py` — populate Vertragspartner
5. `05_create_wartungsvertrag.py` — populate Wartungsvertrag
6. `06_validate_results.py` — validate record counts

`analysis_original.ipynb` is retained as the original notebook for reference.

## Important

The source notebook generates example values for several attributes using Python's
`random` module. Therefore, the generated Ausstattung/Wartung/Vertrag data are
synthetic example data, not authoritative operational data.
