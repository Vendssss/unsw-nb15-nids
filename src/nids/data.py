"""Loading the raw UNSW-NB15 split."""

import pandas as pd

from nids import config


def load_split(split: str) -> pd.DataFrame:
    """Load the official "train" or "test" split, checking its row count."""
    paths = {"train": config.TRAIN_CSV, "test": config.TEST_CSV}
    if split not in paths:
        raise ValueError(f"split must be 'train' or 'test', got {split!r}")

    df = pd.read_csv(paths[split])

    expected = config.EXPECTED_ROWS[split]
    if len(df) != expected:
        raise ValueError(
            f"{paths[split].name} has {len(df):,} rows; the official {split} "
            f"split has {expected:,}. Check the TRAIN_CSV/TEST_CSV mapping in config.py."
        )

    # Normalise text columns: some copies pad values with spaces.
    for col in config.CATEGORICAL + [config.ATTACK_CAT]:
        df[col] = df[col].astype(str).str.strip()
    return df
