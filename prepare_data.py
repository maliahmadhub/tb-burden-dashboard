"""
prepare_data.py  —  one-shot real-data fetcher
-----------------------------------------------
Downloads the full, current WHO Global TB Programme CSV files into ./data so the
repository is self-contained (and can be committed to GitHub / zipped for Moodle).

Run once before deploying / submitting:

    python prepare_data.py

The Streamlit app loads these bundled files first, falls back to live download,
then to the small committed sample. No data is fabricated — everything comes
straight from WHO.
"""
import os
import sys
import pandas as pd

DATA_DIR = "data"
WHO = "https://extranet.who.int/tme/generateCSV.asp?ds="

FILES = {
    "TB_estimates.csv": WHO + "estimates",        # incidence, mortality, TB/HIV, CDR
    "TB_age_sex.csv":   WHO + "estimates_age_sex", # incidence by age band & sex
    "TB_mdr_rr.csv":    WHO + "mdr_rr_estimates",  # drug-resistant TB
    "TB_outcomes.csv":  WHO + "outcomes",          # treatment success
}


def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    ok, fail = 0, 0
    for fname, url in FILES.items():
        dest = os.path.join(DATA_DIR, fname)
        try:
            print(f"↓ downloading {fname} …", flush=True)
            df = pd.read_csv(url, low_memory=False)
            df.to_csv(dest, index=False)
            print(f"  saved {dest}  ({len(df):,} rows, {df.shape[1]} cols)")
            ok += 1
        except Exception as e:
            print(f"  ! could not fetch {fname}: {e}", file=sys.stderr)
            fail += 1
    print(f"\nDone. {ok} file(s) saved, {fail} failed.")
    if fail:
        print("If downloads failed, check your internet/proxy and re-run. "
              "The app still works on live download or the bundled sample.")


if __name__ == "__main__":
    main()
