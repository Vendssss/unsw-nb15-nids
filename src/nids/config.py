"""Project-wide paths and constants.

Every path is anchored on this file's location, so imports work the same from
the terminal, a notebook in notebooks/, or a test in tests/.
"""

from pathlib import Path

# src/nids/config.py -> parents[0]=nids, parents[1]=src, parents[2]=project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MODELS_DIR = PROJECT_ROOT / "models"
FIGURES_DIR = PROJECT_ROOT / "reports" / "figures"

# Official UNSW-NB15 partitioned split. Never tune anything on TEST_CSV.
TRAIN_CSV = RAW_DIR / "UNSW_NB15_training-set.csv"
TEST_CSV = RAW_DIR / "UNSW_NB15_testing-set.csv"

# Seed for every random operation (splits, model init) so results reproduce.
RANDOM_STATE = 42
