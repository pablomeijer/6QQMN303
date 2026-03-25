import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
OUT = BASE / "appendix" / "appendix_d"
OUT.mkdir(parents=True, exist_ok=True)


def _input(rel: str) -> Path:
    p = BASE / "data" / rel
    if p.exists():
        return p
    return BASE / rel


# Build stakeholder power-interest map from stakeholder_summary.xlsx
x = _input("stakeholder_summary.xlsx")
if x.exists():
    df = pd.read_excel(x)
else:
    df = pd.DataFrame([
        ["ERCOT", "High", "High"],
        ["Hyperscalers (Google, Meta, Microsoft)", "High", "High"],
        ["PUCT", "High", "Medium"],
        ["Investor-owned utilities", "High", "High"],
        ["Texas Legislature", "High", "Medium"],
        ["Rural counties", "Low", "Low"],
    ], columns=["Stakeholder", "Power", "Interest"])

map_level = {"Low": 1, "Medium": 2, "High": 3}
df["power_n"] = df["Power"].map(map_level).fillna(2)
df["interest_n"] = df["Interest"].map(map_level).fillna(2)

fig, ax = plt.subplots(figsize=(10, 7))
ax.axvline(2, color="gray", linewidth=1)
ax.axhline(2, color="gray", linewidth=1)
ax.set_xlim(0.5, 3.5)
ax.set_ylim(0.5, 3.5)
ax.set_xticks([1,2,3], ["Low", "Medium", "High"])
ax.set_yticks([1,2,3], ["Low", "Medium", "High"])
ax.set_xlabel("Interest")
ax.set_ylabel("Power")
ax.set_title("Stakeholder Power-Interest Matrix")

for i, r in df.iterrows():
    color = "#8B0000" if r["power_n"] >= 2 and r["interest_n"] >= 2 else "#00008B"
    ax.scatter(r["interest_n"], r["power_n"], s=140, color=color, edgecolor="white", zorder=3)
    ax.text(r["interest_n"] + 0.03, r["power_n"] + 0.03, str(r["Stakeholder"]), fontsize=8)

ax.text(1.05, 3.25, "Keep Satisfied", fontsize=9)
ax.text(2.15, 3.25, "Key Players", fontsize=9)
ax.text(1.05, 1.05, "Monitor", fontsize=9)
ax.text(2.15, 1.05, "Keep Informed", fontsize=9)

plt.tight_layout()
fig.savefig(OUT / "stakeholder_matrix.png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)

notes = """# Stakeholder Notes

Hyperscalers (Meta, Google, Microsoft) sit in the high-power high-interest quadrant as key players whose siting decisions are the primary lever for change, but whose incentives currently favor urban I-35 locations.

Rural counties and environmental groups sit in the monitor quadrant with low power but direct stakes in transmission investment and curtailment revenue.

ERCOT and investor-owned utilities are keep-satisfied stakeholders with high power over market rules but mixed incentives toward reform.

The Texas Legislature sits in the keep-satisfied quadrant and is the primary veto player for statutory reform, making ERCOT protocol-level interventions the path of least resistance for Tier 1.
"""
(OUT / "stakeholder_notes.md").write_text(notes, encoding="utf-8")
print("Generated Appendix D outputs in", OUT)
