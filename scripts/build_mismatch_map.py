import pandas as pd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, FancyArrowPatch
from shapely.geometry import Point
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
    return BASE / "data" / rel


# ── PATHS (place large GIS files under data/ or repo root) ──
GEOJSON_PATH = str(_input("Electric_Power_Transmission_Lines_shp.geojson"))
COUNTY_CACHE = _input("texas_counties_cache.gpkg")
if not COUNTY_CACHE.exists():
    COUNTY_CACHE = BASE / "texas cleaned" / "texas_counties_cache.gpkg"
CAPACITY_PATH = str(_input("county_capacity_comparison - Copy.xlsx"))
DC_PATH = str(_input("data_centres_doe_texas_cleaned.xlsx"))
if not Path(DC_PATH).exists():
    DC_PATH = str(_input("data_centres_doe_texas.xlsx"))

print("Loading counties...")
counties = gpd.read_file(COUNTY_CACHE)
counties["NAME_UPPER"] = counties["NAME"].astype(str).str.upper().str.strip()

print("Loading capacity data...")
cap = pd.read_excel(CAPACITY_PATH)
cap["NAME_UPPER"] = cap["County"].astype(str).str.upper().str.strip()
counties = counties.merge(
    cap[["NAME_UPPER", "Wind Capacity (MW)", "Solar Capacity (MW)",
         "Total Renewable Capacity (MW)", "Data Center Demand (MW)"]],
    on="NAME_UPPER", how="left"
)
counties["Total Renewable Capacity (MW)"] = counties["Total Renewable Capacity (MW)"].fillna(0)
counties["Data Center Demand (MW)"] = counties["Data Center Demand (MW)"].fillna(0)

print("Loading transmission lines (this may take a minute)...")
lines = gpd.read_file(GEOJSON_PATH)
lines["VOLTAGE"] = pd.to_numeric(lines["VOLTAGE"], errors="coerce")
texas_bounds = counties.total_bounds  # minx, miny, maxx, maxy
lines_texas = lines.cx[texas_bounds[0]:texas_bounds[2], texas_bounds[1]:texas_bounds[3]].copy()
print(f"  Texas lines: {len(lines_texas)}")

# HV lines only (345+)
hv = lines_texas[lines_texas["VOLTAGE"] >= 345].copy()
print(f"  HV lines (345+ kV): {len(hv)}")

print("Loading data centre points...")
dc = pd.read_excel(DC_PATH, sheet_name="Data_Centres")
dc = dc[dc["Name"].astype(str).str.contains(", TX", na=False)].copy()
dc["Total MW"] = pd.to_numeric(dc["Total MW"], errors="coerce").fillna(0)

def parse_centroid(s):
    try:
        parts = str(s).replace("\xa0", " ").split(",")
        lon, lat = float(parts[0].strip()), float(parts[1].strip())
        if 25 <= lat <= 37 and -107 <= lon <= -93:
            return Point(lon, lat)
        if 25 <= lon <= 37 and -107 <= lat <= -93:
            return Point(lat, lon)
    except:
        pass
    return None

dc["geometry"] = dc["Centroid"].apply(parse_centroid)
dc = dc.dropna(subset=["geometry"])
gdf_dc = gpd.GeoDataFrame(dc, geometry="geometry", crs="EPSG:4326")

# ── I-35 CORRIDOR COUNTIES ──
I35_COUNTIES = [
    "DALLAS", "TARRANT", "COLLIN", "DENTON", "ELLIS",
    "HOOD", "JOHNSON", "KAUFMAN",
    "TRAVIS", "WILLIAMSON", "HAYS", "BASTROP",
    "BEXAR", "GUADALUPE", "COMAL", "MEDINA", "CALDWELL",
    "BELL", "MCLENNAN", "HILL", "CORYELL", "FALLS",
    "NAVARRO", "MILAM",
]
counties["is_i35"] = counties["NAME_UPPER"].isin(I35_COUNTIES)

# ── BUILD THE MAP ──
print("Building map...")
fig, ax = plt.subplots(figsize=(18, 22))
ax.set_aspect("equal")

# 1. County fill: renewable capacity (green gradient), grey if zero
ren_col = "Total Renewable Capacity (MW)"
max_ren = counties[ren_col].quantile(0.95)

has_ren = counties[counties[ren_col] > 0]
no_ren = counties[counties[ren_col] == 0]

cmap_ren = plt.cm.YlGn
norm_ren = mcolors.Normalize(vmin=0, vmax=max_ren)

no_ren.plot(ax=ax, color="#f0f0f0", edgecolor="#cccccc", linewidth=0.3)
has_ren.plot(ax=ax, column=ren_col, cmap=cmap_ren, norm=norm_ren,
             edgecolor="#cccccc", linewidth=0.3)

# 2. I-35 corridor highlight (hatched border)
i35_gdf = counties[counties["is_i35"]]
i35_gdf.plot(ax=ax, facecolor="none", edgecolor="#e74c3c", linewidth=2.0, linestyle="--", zorder=5)

# 3. All transmission lines (faint)
lines_texas.plot(ax=ax, color="#bdc3c7", linewidth=0.3, alpha=0.5, zorder=2)

# 4. HV lines (345+ kV) colored by voltage
VOLT_COLORS = {345: "#f39c12", 500: "#e74c3c"}
VOLT_LW = {345: 1.8, 500: 2.8}
for volt in [345, 500]:
    subset = hv[hv["VOLTAGE"] == volt]
    if len(subset) > 0:
        subset.plot(ax=ax, color=VOLT_COLORS[volt], linewidth=VOLT_LW[volt], zorder=3)

# 5. Data center bubbles (sized by MW, red)
dc_sizes = gdf_dc["Total MW"].apply(lambda mw: max(15, min(220, 15 + 4 * np.sqrt(max(0.1, mw)))))
ax.scatter(
    gdf_dc.geometry.x, gdf_dc.geometry.y,
    s=dc_sizes, c="#e74c3c", edgecolors="#7b241c", linewidths=0.8,
    zorder=10, alpha=0.85
)

# 6. City labels
CITIES = {
    "Dallas": (-96.80, 32.78),
    "Austin": (-97.74, 30.27),
    "San Antonio": (-98.49, 29.42),
    "Houston": (-95.37, 29.76),
    "Midland": (-102.08, 31.99),
    "Amarillo": (-101.83, 35.22),
    "El Paso": (-106.45, 31.76),
}
for city, (lon, lat) in CITIES.items():
    ax.annotate(
        city, (lon, lat), fontsize=10, fontweight="bold",
        color="#2c3e50", ha="center", va="bottom",
        bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.7),
        zorder=12,
    )

# 7. Annotation arrow: "~300 miles" between DFW and West TX
ax.annotate(
    "", xy=(-102.0, 32.0), xytext=(-97.0, 32.8),
    arrowprops=dict(arrowstyle="<->", color="#2c3e50", lw=2.5, connectionstyle="arc3,rad=0.1"),
    zorder=11,
)
ax.text(-99.5, 33.3, "~300 miles", fontsize=12, fontweight="bold", color="#2c3e50",
        ha="center", va="bottom",
        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#2c3e50", alpha=0.9),
        zorder=12)

# 8. Region labels
ax.text(-101.5, 30.5, "WEST TEXAS\nRenewable Hub\n22,529 MW", fontsize=11,
        fontweight="bold", color="#1a5e20", ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#27ae60", alpha=0.9, linewidth=1.5),
        zorder=12)
ax.text(-101.2, 35.5, "PANHANDLE\nWind Corridor\n12,799 MW", fontsize=11,
        fontweight="bold", color="#1a5e20", ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#27ae60", alpha=0.9, linewidth=1.5),
        zorder=12)
ax.text(-96.0, 31.0, "I-35 CORRIDOR\nData Center Hub\n22,230 MW DC", fontsize=11,
        fontweight="bold", color="#c0392b", ha="center", va="center",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#c0392b", alpha=0.9, linewidth=1.5),
        zorder=12)

# ── COLORBAR ──
sm = plt.cm.ScalarMappable(cmap=cmap_ren, norm=norm_ren)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, shrink=0.35, pad=0.02, aspect=25)
cbar.set_label("Renewable Generation Capacity (MW)", fontsize=11)

# ── LEGEND ──
legend_elements = [
    Line2D([0], [0], marker="o", markersize=14, color="#e74c3c",
           markerfacecolor="#e74c3c", markeredgecolor="#7b241c",
           label="Data Centre (size = MW)", linestyle="None"),
    Line2D([0], [0], color="#f39c12", linewidth=VOLT_LW[345], label="345 kV Transmission"),
    Line2D([0], [0], color="#e74c3c", linewidth=VOLT_LW[500], label="500 kV Transmission"),
    Line2D([0], [0], color="#bdc3c7", linewidth=1.0, label="All Other Transmission"),
    Patch(facecolor="none", edgecolor="#e74c3c", linewidth=2.0, linestyle="--",
          label="I-35 Corridor"),
    Patch(facecolor=cmap_ren(0.7), edgecolor="#cccccc", label="High Renewable Capacity"),
    Patch(facecolor="#f0f0f0", edgecolor="#cccccc", label="No Renewable Capacity"),
]

ax.legend(
    handles=legend_elements,
    loc="lower left",
    fontsize=10,
    framealpha=0.95,
    title="Map Legend",
    title_fontsize=11,
)

ax.set_title(
    "The Geographic Mismatch: Data Centres, Renewable Generation & Transmission Infrastructure in Texas",
    fontsize=15, fontweight="bold", pad=15
)
ax.set_axis_off()
plt.tight_layout()

map_path = f"{OUT_DIR}\\mismatch_map.png"
fig.savefig(map_path, dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print(f"\nMap saved: {map_path}")
