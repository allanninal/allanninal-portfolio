"""Quick profile of CPA datasets + headline summaries."""
from pathlib import Path
import pandas as pd

DATA = Path("/tmp/cebu-logistics/cpa_data")
OUT = Path("/tmp/cebu-logistics/cpa_summaries")
OUT.mkdir(exist_ok=True)

files = {
    "cargo (metric tons)":     ("cpa_cargo.csv",    "volume_metrictons"),
    "container (TEUs)":         ("cpa_container.csv","volume_teus"),
    "passenger (count)":        ("cpa_passenger.csv","number_passengers"),
    "rolling cargo (units)":    ("cpa_rolling.csv",  "volume_units"),
    "ship calls (count)":       ("cpa_shipcall.csv", "   count"),
}

for label, (fname, valcol) in files.items():
    df = pd.read_csv(DATA / fname)
    df.columns = [c.strip() for c in df.columns]
    valcol = valcol.strip()
    print(f"\n=== {label}  ({fname}) ===")
    print(f"  rows: {len(df):,}   cols: {list(df.columns)}")
    print(f"  years: {sorted(df['year'].dropna().unique().tolist())}")
    print(f"  PMOs: {df['pmo'].dropna().unique().tolist()}")
    if 'port_type' in df.columns:
        print(f"  port_type: {df['port_type'].dropna().unique().tolist()}")

    # Annual totals by PMO
    annual = (df.groupby(['year', 'pmo'])[valcol].sum()
                .unstack(fill_value=0).round(0))
    print(f"\n  Annual totals by PMO ({valcol}):")
    print(annual.to_string())

    annual.to_csv(OUT / f"annual_by_pmo_{fname.replace('cpa_','').replace('.csv','')}.csv")

print(f"\n→ tidy summaries written to {OUT}/")
