# Data folder

## Included (CSV)

Shareable derived tables used in the report and appendix (policy allocation, quartiles, cost summary, transmission extracts).

## Excel inputs (add locally — not redistributed)

Place these files in `data/` (or project root) so appendix scripts can find them:

| File | Used by |
|------|---------|
| `rai_county_analysis.xlsx` | `appendix/appendix_a/rai_sensitivity.py` |
| `rpt.00013060.0000000000000000.DAMLZHBSPP_2025 (1).xlsx` | `appendix/appendix_b/cost_model_appendix.py` |
| `county_capacity_comparison - Copy.xlsx` | Appendix B (zone weights), `scripts/build_visuals.py`, `build_mismatch_map.py` |
| `data_centres_doe_texas.xlsx` | `appendix/appendix_c/pipeline_summary.py` |
| `stakeholder_summary.xlsx` | `appendix/appendix_d/build_stakeholder_matrix.py` (optional; script has defaults) |

## Oxford Economics (not in this repo)

Web scraper code and raw scraped facility records are proprietary; use was authorised for the capstone only.

## Optional GIS

For full map scripts (`scripts/build_mismatch_map.py`, `policy_priority_counties.py`):

- `texas_counties_cache.gpkg` — place under `data/` or keep under `texas cleaned/` locally.
- `Electric_Power_Transmission_Lines_shp.geojson` — place under `data/` if you use the map script.
