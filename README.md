# 6QQMN303

Capstone repository: Texas data centre siting and renewable energy spatial mismatch (ERCOT).

**GitHub:** [https://github.com/pablomeijer/6QQMN303](https://github.com/pablomeijer/6QQMN303)

## Repository layout

| Folder | Contents |
|--------|----------|
| `data/` | Shareable CSV outputs and GIS extracts; see `data/README.md` for required Excel inputs to rerun appendix scripts. |
| `scripts/` | Main notebooks and Python utilities (cost model notebook, maps, visuals, curtailment plots, RAI notebook). |
| `appendix/` | Appendix A–D: formulas, sensitivity, cost model, pipeline summary, stakeholder scripts and generated tables (CSV/MD). |

Run Python appendix scripts from the **repository root** (`6QQMN303/`), e.g. `python appendix/appendix_b/cost_model_appendix.py`.

## What is not published

Oxford Economics web scraper code and raw scraped records are **not** included (proprietary; permission to use for research, not redistribution).

## Replication

1. Clone the repo.
2. Add Excel inputs listed in `data/README.md` to `data/` (or project root — scripts check both).
3. Install Python dependencies (pandas, numpy, matplotlib; geopandas/shapely for map scripts).
4. Run appendix scripts or open `scripts/cost_optimisation_model.ipynb`.
