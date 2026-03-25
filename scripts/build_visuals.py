import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
OUT_DIR = str(BASE)


def _input(rel: str) -> Path:
    p = BASE / "data" / rel
    if p.exists():
        return p
    p2 = BASE / rel
    if p2.exists():
        return p2
    return p


DATA_PATH = _input("county_capacity_comparison - Copy.xlsx")
df = pd.read_excel(DATA_PATH)

DC = "Data Center Demand (MW)"
REN = "Total Renewable Capacity (MW)"
GEN = "Total Generation Capacity (MW)"
WIND = "Wind Capacity (MW)"
SOLAR = "Solar Capacity (MW)"

# ── VISUAL 1: Two-panel horizontal bar chart ──

top_dc = df.nlargest(10, DC).sort_values(DC, ascending=True)
top_ren = df.nlargest(10, REN).sort_values(REN, ascending=True)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), sharey=False)

bar_height = 0.35
y_dc = np.arange(len(top_dc))
y_ren = np.arange(len(top_ren))

# Left panel: Top 10 by DC Demand
ax1.barh(y_dc + bar_height/2, top_dc[DC].values, bar_height, color="#c0392b", label="Data Center Demand", zorder=3)
ax1.barh(y_dc - bar_height/2, top_dc[REN].values, bar_height, color="#27ae60", label="Renewable Capacity", zorder=3)
ax1.set_yticks(y_dc)
ax1.set_yticklabels(top_dc["County"].values, fontsize=11)
ax1.set_xlabel("Capacity (MW)", fontsize=12)
ax1.set_title("Top 10 Counties by Data Center Demand", fontsize=13, fontweight="bold")
ax1.legend(loc="lower right", fontsize=10)
ax1.grid(axis="x", alpha=0.3, zorder=0)
ax1.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

# Right panel: Top 10 by Renewable Capacity
ax2.barh(y_ren + bar_height/2, top_ren[REN].values, bar_height, color="#27ae60", label="Renewable Capacity", zorder=3)
ax2.barh(y_ren - bar_height/2, top_ren[DC].values, bar_height, color="#c0392b", label="Data Center Demand", zorder=3)
ax2.set_yticks(y_ren)
ax2.set_yticklabels(top_ren["County"].values, fontsize=11)
ax2.set_xlabel("Capacity (MW)", fontsize=12)
ax2.set_title("Top 10 Counties by Renewable Capacity", fontsize=13, fontweight="bold")
ax2.legend(loc="lower right", fontsize=10)
ax2.grid(axis="x", alpha=0.3, zorder=0)
ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

fig.suptitle("The Geographic Mismatch: Data Center Demand vs Renewable Capacity by County",
             fontsize=14, fontweight="bold", y=1.01)
plt.tight_layout()
chart_path = f"{OUT_DIR}\\dc_vs_renewable_bar_chart.png"
fig.savefig(chart_path, dpi=300, bbox_inches="tight")
plt.close()
print(f"Chart saved: {chart_path}")

# ── VISUAL 2: Regional summary table ──

# Define regions by county lists
REGIONS = {
    "I-35 Corridor": [
        "Dallas", "Tarrant", "Collin", "Denton", "Ellis",
        "Hood", "Johnson", "Kaufman",
        "Travis", "Williamson", "Hays", "Bastrop",
        "Bexar", "Guadalupe", "Comal", "Medina", "Caldwell",
        "Bell", "McLennan", "Hill", "Coryell", "Falls",
        "Navarro", "Milam",
    ],
    "West Texas": [
        "Pecos", "Reeves", "Ward", "Crane", "Upton", "Midland", "Ector",
        "Andrews", "Winkler", "Loving", "Culberson", "Hudspeth",
        "Jeff Davis", "Presidio", "Brewster", "Terrell", "Crockett",
        "Reagan", "Irion", "Sterling", "Glasscock", "Howard", "Martin",
        "Borden", "Scurry", "Mitchell", "Nolan", "Tom Green", "Concho",
        "Coke", "Runnels", "Fisher", "Jones", "Taylor", "Callahan",
    ],
    "Panhandle": [
        "Dallam", "Sherman", "Hansford", "Ochiltree", "Lipscomb",
        "Hartley", "Moore", "Hutchinson", "Roberts", "Hemphill",
        "Oldham", "Potter", "Carson", "Gray", "Wheeler",
        "Deaf Smith", "Randall", "Armstrong", "Donley", "Collingsworth",
        "Parmer", "Castro", "Swisher", "Briscoe", "Hall", "Childress",
        "Bailey", "Lamb", "Hale", "Floyd", "Motley", "Cottle",
        "Hardeman", "Foard", "Knox", "Haskell", "Stonewall", "King",
        "Wilbarger",
    ],
    "Houston Metro": [
        "Harris", "Fort Bend", "Montgomery", "Brazoria", "Galveston",
        "Liberty", "Chambers", "Waller", "Austin", "Wharton",
    ],
    "South Texas": [
        "Willacy", "Webb", "Cameron", "San Patricio", "Starr", "Kenedy",
    ],
}

# Case-insensitive matching: normalise both sides to upper
df["_county_upper"] = df["County"].astype(str).str.upper().str.strip()

rows = []
assigned = set()
for region, counties in REGIONS.items():
    counties_upper = [c.upper() for c in counties]
    mask = df["_county_upper"].isin(counties_upper)
    assigned.update(counties_upper)
    dc_mw = df.loc[mask, DC].sum()
    ren_mw = df.loc[mask, REN].sum()
    n_counties = mask.sum()
    rows.append({"Region": region, "Counties": n_counties, "Data Center MW": dc_mw, "Renewable MW": ren_mw})

# Rest of Texas
rest_mask = ~df["_county_upper"].isin(assigned)
n_rest = rest_mask.sum()
rows.append({
    "Region": "Rest of Texas",
    "Counties": n_rest,
    "Data Center MW": df.loc[rest_mask, DC].sum(),
    "Renewable MW": df.loc[rest_mask, REN].sum(),
})

table = pd.DataFrame(rows)
total_dc = table["Data Center MW"].sum()
total_ren = table["Renewable MW"].sum()
table["DC % of Total"] = (100 * table["Data Center MW"] / total_dc).round(1).astype(str) + "%"
table["Renewable % of Total"] = (100 * table["Renewable MW"] / total_ren).round(1).astype(str) + "%"
table["Data Center MW"] = table["Data Center MW"].round(0).astype(int)
table["Renewable MW"] = table["Renewable MW"].round(0).astype(int)

# Add total row
total_counties = table["Counties"].sum()
total_row = pd.DataFrame([{
    "Region": "Total",
    "Counties": int(total_counties),
    "Data Center MW": int(round(total_dc)),
    "Renewable MW": int(round(total_ren)),
    "DC % of Total": "100.0%",
    "Renewable % of Total": "100.0%",
}])
table = pd.concat([table, total_row], ignore_index=True)

print("\nTable 1: Data Center Demand vs Renewable Capacity by Texas Region")
print(table.to_string(index=False))

# Save as figure
fig2, ax_t = plt.subplots(figsize=(10, 3.5))
ax_t.axis("off")

col_labels = ["Region", "Counties", "Data Center\nMW", "Renewable\nMW", "DC % of\nTotal", "Renewable %\nof Total"]
cell_text = table.values.tolist()

tbl = ax_t.table(
    cellText=cell_text,
    colLabels=col_labels,
    cellLoc="center",
    loc="center",
)
tbl.auto_set_font_size(False)
tbl.set_fontsize(11)
tbl.scale(1.0, 1.6)

for (row, col), cell in tbl.get_celld().items():
    if row == 0:
        cell.set_facecolor("#2c3e50")
        cell.set_text_props(color="white", fontweight="bold")
    elif row == len(cell_text):
        cell.set_facecolor("#ecf0f1")
        cell.set_text_props(fontweight="bold")
    else:
        cell.set_facecolor("white")
    cell.set_edgecolor("#bdc3c7")

ax_t.set_title("Table 1: Data Center Demand vs Renewable Capacity by Texas Region",
               fontsize=13, fontweight="bold", pad=20)
table_path = f"{OUT_DIR}\\regional_summary_table.png"
fig2.savefig(table_path, dpi=300, bbox_inches="tight")
plt.close()
print(f"\nTable saved: {table_path}")

# ── EXCEL EXPORT: Regional summary + county-level detail by region ──

# Build county-level detail with region assignment
df["_county_upper"] = df["County"].astype(str).str.upper().str.strip()
county_region = []
for region, counties in REGIONS.items():
    counties_upper = [c.upper() for c in counties]
    for _, r in df[df["_county_upper"].isin(counties_upper)].iterrows():
        county_region.append({
            "Region": region,
            "County": r["County"],
            DC: r[DC],
            REN: r[REN],
            WIND: r[WIND],
            SOLAR: r[SOLAR],
            GEN: r[GEN],
        })
rest_upper = set()
for counties in REGIONS.values():
    rest_upper.update(c.upper() for c in counties)
for _, r in df[~df["_county_upper"].isin(rest_upper)].iterrows():
    county_region.append({
        "Region": "Rest of Texas",
        "County": r["County"],
        DC: r[DC],
        REN: r[REN],
        WIND: r[WIND],
        SOLAR: r[SOLAR],
        GEN: r[GEN],
    })

detail = pd.DataFrame(county_region)
detail = detail.sort_values(["Region", DC], ascending=[True, False]).reset_index(drop=True)

excel_path = f"{OUT_DIR}\\regional_capacity_analysis.xlsx"
with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    table.to_excel(writer, sheet_name="Regional Summary", index=False)
    detail.to_excel(writer, sheet_name="County Detail by Region", index=False)
print(f"\nExcel saved: {excel_path}")
