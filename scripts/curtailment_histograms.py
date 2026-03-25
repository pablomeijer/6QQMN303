"""
Curtailment by site: two side-by-side histograms (Wind and Solar).
Each bar = one site. Site names omitted per user request.
"""
import matplotlib
matplotlib.use("Agg")
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
CSV_PATH = BASE / "data" / "curtailment_by_site_flourish.csv"
if not CSV_PATH.exists():
    CSV_PATH = BASE / "data" / "flourish_curtailment_data.csv"

df = pd.read_csv(CSV_PATH)
solar = df[df["Resource Type"] == "Solar"]["Curtailed Solar"].values / 1000  # convert to GWh
wind = df[df["Resource Type"] == "Wind"]["Wind"].values / 1000  # convert to GWh

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# LEFT: Wind histogram
x_wind = range(len(wind))
ax1.bar(x_wind, wind, color="#3498db", edgecolor="#2980b9", linewidth=0.5)
ax1.set_xlabel("Site (ordered by curtailment)", fontsize=11, fontweight="bold")
ax1.set_ylabel("Curtailed Energy (GWh)", fontsize=11, fontweight="bold")
ax1.set_title("Wind Curtailment by Site", fontsize=13, fontweight="bold")
ax1.set_xticks([])
ax1.set_xticklabels([])
ax1.grid(axis="y", alpha=0.3)
ax1.text(0.98, 0.97, "The most curtailed wind sites lose 200 GWh —\nwhile some sites aren't curtailed at all.",
         transform=ax1.transAxes, fontsize=10, va="top", ha="right",
         bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="#2980b9", alpha=0.95))

# RIGHT: Solar histogram
x_solar = range(len(solar))
ax2.bar(x_solar, solar, color="#f39c12", edgecolor="#d68910", linewidth=0.5)
ax2.set_xlabel("Site (ordered by curtailment)", fontsize=11, fontweight="bold")
ax2.set_ylabel("Curtailed Energy (GWh)", fontsize=11, fontweight="bold")
ax2.set_title("Solar Curtailment by Site", fontsize=13, fontweight="bold")
ax2.set_xticks([])
ax2.set_xticklabels([])
ax2.grid(axis="y", alpha=0.3)

plt.suptitle("Curtailment Rates Vary Widely by Site", fontsize=15, fontweight="bold", y=1.02)
plt.tight_layout(rect=[0, 0.03, 1, 1])
fig.text(0.5, 0.01, "Source: ERCOT", ha="center", fontsize=10, style="italic", color="#666666")
out_path = str(BASE / "curtailment_by_site_histograms.png")
fig.savefig(out_path, dpi=300, bbox_inches="tight", facecolor="white")
plt.close(fig)
print(f"Saved: {out_path}")
