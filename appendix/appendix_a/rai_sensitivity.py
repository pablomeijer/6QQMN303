import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "appendix" / "appendix_a"
OUT.mkdir(parents=True, exist_ok=True)


def _input(rel: str) -> Path:
    """Prefer data/ subfolder (repo layout), fall back to project root."""
    p = BASE / "data" / rel
    if p.exists():
        return p
    return BASE / rel

def df_to_md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = []
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("|" + "|".join(["---"] * len(cols)) + "|")
    for _, r in df.iterrows():
        vals = [str(r[c]).replace("\n", " ") for c in cols]
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)

df = pd.read_excel(_input("rai_county_analysis.xlsx"), sheet_name="County RAI v2")
df = df.rename(columns={
    "County": "county",
    "Surplus Ratio (Full Pipeline)": "surplus_ratio",
    "Cap. Density (pct rank)": "transmission_density_rank",
    "Proximity (pct rank)": "proximity_rank",
})
for col in ["surplus_ratio", "transmission_density_rank", "proximity_rank"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

surplus_rank = df["surplus_ratio"].rank(pct=True)

def assign_quartile(series):
    q = pd.qcut(series.rank(method='first'), 4, labels=["Q4", "Q3", "Q2", "Q1"])
    return q.astype(str)

schemes = {
    "equal_weights": (0.33, 0.33, 0.34),
    "transmission_heavy": (0.2, 0.6, 0.2),
    "surplus_heavy": (0.6, 0.2, 0.2),
}

scores = {}
for name, (w_surplus, w_tx, w_prox) in schemes.items():
    scores[name] = w_surplus * surplus_rank + w_tx * df["transmission_density_rank"] + w_prox * df["proximity_rank"]

out = pd.DataFrame({"county": df["county"]})
out["equal_weights_quartile"] = assign_quartile(scores["equal_weights"])
out["transmission_heavy_quartile"] = assign_quartile(scores["transmission_heavy"])
out["surplus_heavy_quartile"] = assign_quartile(scores["surplus_heavy"])
out["quartile_stable"] = (
    (out["equal_weights_quartile"] == out["transmission_heavy_quartile"]) &
    (out["equal_weights_quartile"] == out["surplus_heavy_quartile"])
)

changed_pct = round((~out["quartile_stable"]).mean() * 100, 2)
summary_row = pd.DataFrame([{
    "county": "SUMMARY",
    "equal_weights_quartile": "-",
    "transmission_heavy_quartile": "-",
    "surplus_heavy_quartile": "-",
    "quartile_stable": f"{100 - changed_pct:.2f}% stable / {changed_pct:.2f}% changed"
}])
out_with_summary = pd.concat([out, summary_row], ignore_index=True)

csv_path = OUT / "rai_sensitivity_table.csv"
out_with_summary.to_csv(csv_path, index=False)

md_path = OUT / "rai_sensitivity_table.md"
with md_path.open("w", encoding="utf-8") as f:
    f.write("# RAI Sensitivity Table\n\n")
    f.write(df_to_md(out_with_summary))
    f.write(f"\n\n**Share of counties changing quartile across schemes:** {changed_pct:.2f}%\n")

sets = {
    "Equal": set(out.loc[out["equal_weights_quartile"] == "Q1", "county"]),
    "Tx-heavy": set(out.loc[out["transmission_heavy_quartile"] == "Q1", "county"]),
    "Surplus-heavy": set(out.loc[out["surplus_heavy_quartile"] == "Q1", "county"]),
}
labels = ["Equal ∩ Tx-heavy", "Equal ∩ Surplus-heavy", "Tx-heavy ∩ Surplus-heavy", "All three"]
values = [
    len(sets["Equal"].intersection(sets["Tx-heavy"])),
    len(sets["Equal"].intersection(sets["Surplus-heavy"])),
    len(sets["Tx-heavy"].intersection(sets["Surplus-heavy"])),
    len(sets["Equal"].intersection(sets["Tx-heavy"]).intersection(sets["Surplus-heavy"])),
]
fig, ax = plt.subplots(figsize=(9, 5))
colors = ["#8B0000", "#00008B", "#8B0000", "#00008B"]
bars = ax.bar(labels, values, color=colors, edgecolor="white")
ax.bar_label(bars, padding=3)
ax.set_ylabel("Number of counties")
ax.set_title("Top-Quartile County Overlap Across RAI Weighting Schemes")
ax.grid(axis="y", alpha=0.3)
plt.xticks(rotation=10)
plt.tight_layout()
fig.savefig(OUT / "rai_sensitivity_chart.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

formula_md = OUT / "rai_formula.md"
formula_md.write_text(
"""# RAI Formula and Variable Definitions

The Renewable Accessibility Index (RAI) is constructed as a weighted composite of three normalized metrics:

RAI_i = w_s * S_i + w_t * T_i + w_p * P_i

Where for county i:

- S_i = normalized renewable surplus ratio score
- T_i = normalized transmission capacity density score
- P_i = normalized proximity score

Variable definitions:

- **Transmission capacity density (GW-miles per sq mile)**: total GW-miles of transmission in county / county area.
- **High-voltage line count (>=345 kV)**: count of high-voltage lines in county.
- **Proximity to renewable surplus counties**: distance (miles) to nearest county where renewable capacity > 2x estimated demand.

Weighting schemes in sensitivity test:

1) Equal weights: surplus 0.33, transmission density 0.33, proximity 0.33 (implemented as 0.33/0.33/0.34 for sum=1)
2) Transmission-heavy: surplus 0.20, transmission density 0.60, proximity 0.20
3) Surplus-heavy: surplus 0.60, transmission density 0.20, proximity 0.20

Quartiles are assigned Q1 (top 25%) to Q4 (bottom 25%) under each scheme.
""",
encoding="utf-8"
)

print("Generated Appendix A outputs in", OUT)
