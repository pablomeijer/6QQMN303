"""
Identify priority counties for policy-induced data center reallocation.
Criteria: High RAI (renewable-ready) AND within reasonable distance of I-35/I-20 (fibre corridor).
"""
import pandas as pd
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point

BASE = Path(__file__).resolve().parent.parent


def _input(rel: str) -> Path:
    """Prefer data/ (repo layout), fall back to project root paths."""
    p = BASE / "data" / rel
    if p.exists():
        return p
    p2 = BASE / rel
    if p2.exists():
        return p2
    return p


COUNTY_CACHE = _input("texas_counties_cache.gpkg")
if not COUNTY_CACHE.exists():
    COUNTY_CACHE = BASE / "texas cleaned" / "texas_counties_cache.gpkg"
CAPACITY_PATH = _input("county_capacity_comparison - Copy.xlsx")
RAI_EXPORT = _input("rai_county_analysis.xlsx")

# Dallas centroid (I-35 corridor hub) for distance proxy
DALLAS_LON, DALLAS_LAT = -96.7970, 32.7767

def main():
    # Load counties with RAI (from exported Excel if exists, else compute)
    counties = gpd.read_file(COUNTY_CACHE)
    counties["NAME_UPPER"] = counties["NAME"].astype(str).str.upper().str.strip()
    
    # Get centroid in WGS84 for distance calc
    counties_prj = counties.to_crs(epsg=4326)
    counties["centroid"] = counties_prj.geometry.centroid
    
    # Distance to Dallas (miles) - proxy for fibre/I-35 proximity
    dallas = Point(DALLAS_LON, DALLAS_LAT)
    counties["dist_to_dallas_mi"] = counties["centroid"].apply(
        lambda c: c.distance(dallas) * 69.0  # ~69 miles per degree at this latitude
    )
    
    # Load RAI and renewable capacity
    cap = pd.read_excel(CAPACITY_PATH)
    cap["NAME_UPPER"] = cap["County"].astype(str).str.upper().str.strip()
    counties = counties.merge(
        cap[["NAME_UPPER", "Total Renewable Capacity (MW)", "Data Center Demand (MW)"]],
        on="NAME_UPPER", how="left"
    )
    counties["ren_mw"] = counties["Total Renewable Capacity (MW)"].fillna(0)
    counties["dc_mw"] = counties["Data Center Demand (MW)"].fillna(0)
    
    try:
        rai_df = pd.read_excel(RAI_EXPORT, sheet_name="County RAI v2")
        rai_df["NAME_UPPER"] = rai_df["County"].astype(str).str.upper().str.strip()
        counties = counties.merge(
            rai_df[["NAME_UPPER", "RAI (Full Pipeline)"]],
            on="NAME_UPPER", how="left"
        )
        counties["RAI"] = counties["RAI (Full Pipeline)"].fillna(0)
    except Exception:
        # Fallback: use renewable MW percentile as RAI proxy
        counties["RAI"] = counties["ren_mw"].rank(pct=True)
    
    # I-35 corridor counties (source of shift - exclude from receiving list)
    I35_COUNTIES = [
        "DALLAS", "TARRANT", "COLLIN", "DENTON", "ELLIS", "HOOD", "JOHNSON", "KAUFMAN",
        "TRAVIS", "WILLIAMSON", "HAYS", "BASTROP", "BEXAR", "GUADALUPE", "COMAL", "MEDINA",
        "CALDWELL", "BELL", "MCLENNAN", "HILL", "CORYELL", "FALLS", "NAVARRO", "MILAM",
    ]
    
    # Filter: High RAI (>= 0.60), within 250 mi of Dallas (I-20 corridor to Midland), EXCLUDE I-35 source counties
    candidates = counties[
        (counties["RAI"] >= 0.60) &
        (counties["dist_to_dallas_mi"] <= 250) &
        (~counties["NAME_UPPER"].isin(I35_COUNTIES))
    ].copy()
    
    # Composite score: RAI * (1 - dist/250) to favour high RAI + proximity
    candidates["proximity_score"] = 1 - (candidates["dist_to_dallas_mi"] / 250)
    candidates["priority_score"] = candidates["RAI"] * candidates["proximity_score"]
    candidates = candidates.sort_values("priority_score", ascending=False)
    
    # Priority tiers (distance from Dallas = proxy for fibre proximity)
    tier1 = candidates[candidates["dist_to_dallas_mi"] <= 120]   # North central: Jack, Young, Throckmorton
    tier2 = candidates[(candidates["dist_to_dallas_mi"] > 120) & (candidates["dist_to_dallas_mi"] <= 200)]  # I-20: Abilene, Sweetwater
    tier3 = candidates[candidates["dist_to_dallas_mi"] > 200]    # West Texas: Scurry, Howard, Nolan
    
    print("=" * 80)
    print("PRIORITY COUNTIES FOR POLICY-INDUCED DC REALLOCATION")
    print("Criteria: RAI >= 0.60, within 250 mi of Dallas, exclude I-35 corridor (source)")
    print("=" * 80)
    print("\nTIER 1: Within 120 mi (north central, closest to fibre)")
    print(tier1[["NAME_UPPER", "RAI", "ren_mw", "dc_mw", "dist_to_dallas_mi"]].to_string(index=False))
    print("\nTIER 2: 120-200 mi (I-20 corridor: Abilene, Sweetwater)")
    print(tier2[["NAME_UPPER", "RAI", "ren_mw", "dc_mw", "dist_to_dallas_mi"]].to_string(index=False))
    print("\nTIER 3: 200-250 mi (West Texas: Scurry, Howard, Nolan)")
    print(tier3[["NAME_UPPER", "RAI", "ren_mw", "dc_mw", "dist_to_dallas_mi"]].to_string(index=False))
    
    # Suggested MW allocation (proportional to priority_score * renewable headroom)
    total_shift = 8892
    candidates["ren_headroom"] = candidates["ren_mw"].clip(lower=50)  # min 50 MW to avoid zeros
    candidates["allocation_weight"] = candidates["priority_score"] * candidates["ren_headroom"]
    candidates["allocation_weight"] = candidates["allocation_weight"] / candidates["allocation_weight"].sum()
    candidates["suggested_mw"] = (candidates["allocation_weight"] * total_shift).round(0)
    
    # Take top 20 counties by suggested MW, scale to exact total
    priority = candidates.nlargest(20, "suggested_mw").copy()
    scale = total_shift / priority["suggested_mw"].sum()
    priority["suggested_mw"] = (priority["suggested_mw"] * scale).round(0)
    print("\n" + "=" * 80)
    print("SUGGESTED MW ALLOCATION (8,892 MW total, weighted by RAI × proximity × renewable headroom)")
    print("=" * 80)
    print(priority[["NAME_UPPER", "RAI", "ren_mw", "dist_to_dallas_mi", "suggested_mw"]].to_string(index=False))
    print(f"\nTotal allocated: {priority['suggested_mw'].sum():.0f} MW")
    
    # Export
    out = priority[["NAME_UPPER", "RAI", "ren_mw", "dc_mw", "dist_to_dallas_mi", "suggested_mw"]]
    out.columns = ["County", "RAI", "Renewable MW", "Current DC MW", "Dist to Dallas (mi)", "Suggested Policy MW"]
    out.to_csv(BASE / "policy_priority_counties.csv", index=False)
    print(f"\nExported: {BASE / 'policy_priority_counties.csv'}")

if __name__ == "__main__":
    main()
