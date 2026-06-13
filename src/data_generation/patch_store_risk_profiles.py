from pathlib import Path
import numpy as np
import pandas as pd


SEED = 42
np.random.seed(SEED)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
STORE_FILE = RAW_DATA_DIR / "dim_store.csv"


def main():
    stores = pd.read_csv(STORE_FILE)

    n_stores = len(stores)

    n_high = max(1, round(n_stores * 0.10))
    n_medium = round(n_stores * 0.30)
    n_low = n_stores - n_high - n_medium

    risk_profiles = (
        ["High"] * n_high
        + ["Medium"] * n_medium
        + ["Low"] * n_low
    )

    np.random.shuffle(risk_profiles)

    stores["risk_profile"] = risk_profiles

    stores.to_csv(STORE_FILE, index=False)

    print("Updated dim_store.csv risk profile distribution:")
    print(stores["risk_profile"].value_counts())


if __name__ == "__main__":
    main()