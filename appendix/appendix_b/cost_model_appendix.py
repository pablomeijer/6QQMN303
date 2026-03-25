import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "appendix" / "appendix_b"
OUT.mkdir(parents=True, exist_ok=True)


def _input(rel: str) -> Path:
    p = BASE / "data" / rel
    if p.exists():
        return p
    return BASE / rel

DARK_RED = "#8B0000"
DARK_BLUE = "#00008B"

def df_to_md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for _, r in df.iterrows():
        vals = [str(r[c]).replace("\n", " ") for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)

# 1) DAM zonal prices
DAM_PATH = _input("rpt.00013060.0000000000000000.DAMLZHBSPP_2025 (1).xlsx")
sheets = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
frames = []
for s in sheets:
    try:
        frames.append(pd.read_excel(DAM_PATH, sheet_name=s))
    except Exception:
        pass
dam = pd.concat(frames, ignore_index=True)
dam.columns = dam.columns.str.strip()
dam["Price"] = pd.to_numeric(dam["Settlement Point Price"], errors="coerce")
dam["SP"] = dam["Settlement Point"].astype(str).str.strip()
zone_prices = dam.groupby("SP")["Price"].mean().to_dict()

lz_north = float(zone_prices.get("LZ_NORTH", np.nan))
lz_west = float(zone_prices.get("LZ_WEST", np.nan))
hb_pan = float(zone_prices.get("HB_PAN", np.nan))

# 2) Derive 8,900 MW shift allocation by renewable-capacity weighting (West vs Panhandle)
cap = pd.read_excel(_input("county_capacity_comparison - Copy.xlsx"))
cap["COUNTY"] = cap["County"].astype(str).str.upper().str.strip()

PANHANDLE = {
    "DALLAM","SHERMAN","HANSFORD","OCHILTREE","LIPSCOMB","HARTLEY","MOORE","HUTCHINSON",
    "ROBERTS","HEMPHILL","OLDHAM","POTTER","CARSON","GRAY","WHEELER","DEAF SMITH","RANDALL",
    "ARMSTRONG","DONLEY","COLLINGSWORTH","PARMER","CASTRO","SWISHER","BRISCOE","HALL",
    "CHILDRESS","BAILEY","LAMB","HALE","FLOYD","MOTLEY","COTTLE","HARDEMAN","FOARD",
    "KNOX","HASKELL","STONEWALL","KING","WILBARGER"
}
WEST = {
    "PECOS","REEVES","WARD","CRANE","UPTON","MIDLAND","ECTOR","ANDREWS","WINKLER",
    "TAYLOR","NOLAN","HOWARD","MARTIN","SCURRY","MITCHELL","FISHER","JONES","CALLAHAN"
}

ren_col = "Total Renewable Capacity (MW)"
pan_ren = cap.loc[cap["COUNTY"].isin(PANHANDLE), ren_col].fillna(0).sum()
west_ren = cap.loc[cap["COUNTY"].isin(WEST), ren_col].fillna(0).sum()

TOTAL_SHIFT = 8900
pan_weight = pan_ren / (pan_ren + west_ren)
west_weight = west_ren / (pan_ren + west_ren)
shift_pan = round(TOTAL_SHIFT * pan_weight, 0)
shift_west = round(TOTAL_SHIFT * west_weight, 0)
# enforce exact total
shift_west = TOTAL_SHIFT - shift_pan

# 3) Inputs table
inputs = pd.DataFrame([
    ["EPA social cost of carbon (baseline)", 51, "$/tonne"],
    ["EPA social cost of carbon (sensitivity)", 36, "$/tonne"],
    ["EIA emissions factor", 0.435, "tCO2/MWh"],
    ["Average zonal DAM price 2025 - LZ_NORTH", round(lz_north, 2), "$/MWh"],
    ["Average zonal DAM price 2025 - LZ_WEST", round(lz_west, 2), "$/MWh"],
    ["Average zonal DAM price 2025 - HB_PAN", round(hb_pan, 2), "$/MWh"],
    ["Renewable capacity used for weighting - West Texas", round(west_ren, 1), "MW"],
    ["Renewable capacity used for weighting - Panhandle", round(pan_ren, 1), "MW"],
    ["Derived shift allocation to LZ_WEST", int(shift_west), "MW"],
    ["Derived shift allocation to HB_PAN", int(shift_pan), "MW"],
    ["Total shift", int(TOTAL_SHIFT), "MW"],
], columns=["parameter", "value", "unit"])
inputs.to_csv(OUT / "cost_model_inputs.csv", index=False)
(OUT / "cost_model_inputs.md").write_text("# Cost Model Inputs\n\n" + df_to_md(inputs), encoding="utf-8")

# 4) Sensitivity scenarios
# from existing model summary
private_savings_m = 120
foregone_revenue_m = 335
avoided_co2_m_t = 20.3

def scenario_row(name: str, scc: float):
    carbon_externality_m = round(avoided_co2_m_t * scc, 1)
    net_benefit_m = round(carbon_externality_m - private_savings_m + foregone_revenue_m, 1)
    return [name, private_savings_m, carbon_externality_m, foregone_revenue_m, net_benefit_m]

sens = pd.DataFrame([
    scenario_row("Baseline SCC $51/t", 51),
    scenario_row("Sensitivity SCC $36/t", 36),
], columns=["scenario", "private_savings_M", "carbon_externality_M", "foregone_revenue_M", "net_benefit_M"])

sens.to_csv(OUT / "cost_model_sensitivity.csv", index=False)
(OUT / "cost_model_sensitivity.md").write_text("# Cost Model Sensitivity\n\n" + df_to_md(sens), encoding="utf-8")

# 5) Chart
fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(sens["scenario"], sens["net_benefit_M"], color=[DARK_RED, DARK_BLUE], edgecolor="white")
ax.bar_label(bars, fmt="%.1f", padding=3)
ax.set_ylabel("Net benefit (USD million/year)")
ax.set_title("Net Benefit Sensitivity to Social Cost of Carbon")
ax.grid(axis="y", alpha=0.3)
plt.xticks(rotation=10)
plt.tight_layout()
fig.savefig(OUT / "cost_sensitivity_chart.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

# 6) Methodology markdown
method_text = f"""# Cost Model Methodology (Appendix B)

## Calculation chain

- Annual electricity cost = Capacity (MW) x 8,760 x Average zonal DAM price ($/MWh)
- Carbon cost (externality) = Curtailed energy avoided (TWh converted to MWh) x 0.435 tCO2/MWh x Social cost of carbon ($/tCO2)

## 8,900 MW shift derivation

The appendix applies a total 8,900 MW shift from the I-35 load concentration toward receiving renewable zones (LZ_WEST and HB_PAN).

To derive zone shares, the shift is weighted by existing renewable capacity in mapped West Texas and Panhandle counties:

- West Texas renewable capacity used: {west_ren:,.1f} MW
- Panhandle renewable capacity used: {pan_ren:,.1f} MW

Weights are computed as each zone's renewable MW share of combined receiving-zone renewable MW.
This yields:

- Allocation to LZ_WEST: {int(shift_west):,} MW
- Allocation to HB_PAN: {int(shift_pan):,} MW

Total = {TOTAL_SHIFT:,} MW.

This weighting logic is used to document the directional rationale for reallocating load to renewable-rich zones under Tier 2/3 policy assumptions.
"""
(OUT / "cost_model_methodology.md").write_text(method_text, encoding="utf-8")

print("Generated Appendix B outputs in", OUT)
