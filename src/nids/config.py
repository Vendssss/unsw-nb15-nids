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
# The distributed files have their names swapped: the official training set
# (175,341 rows, per Moustafa & Slay 2016) ships as "testing-set.csv", and the
# official testing set (82,332 rows) ships as "training-set.csv". We keep the
# files exactly as downloaded and map them here; data.load_split() checks row
# counts so a corrected download can't silently flip them back.
TRAIN_CSV = RAW_DIR / "UNSW_NB15_testing-set.csv"
TEST_CSV = RAW_DIR / "UNSW_NB15_training-set.csv"
EXPECTED_ROWS = {"train": 175_341, "test": 82_332}

# Columns that are not features: a row index and the two targets.
ID_COL = "id"
TARGET = "label"            # 0 = normal, 1 = attack
ATTACK_CAT = "attack_cat"   # attack category (Phase 7); leaks the label in Phase 3-6
CATEGORICAL = ["proto", "service", "state"]

# Non-negative count/volume/timing columns with skew > 2 on the training split
# (see notebooks/01). log1p squashes their long tails before scaling.
LOG_COLS = [
    "dur", "spkts", "dpkts", "sbytes", "dbytes", "rate", "sload", "dload",
    "sloss", "dloss", "sinpkt", "dinpkt", "sjit", "djit", "tcprtt", "synack",
    "ackdat", "smean", "dmean", "trans_depth", "response_body_len",
    "ct_dst_ltm", "ct_src_dport_ltm", "is_ftp_login", "ct_ftp_cmd",
    "ct_flw_http_mthd",
]

# Lab-artifact features (TTL identifies the attacker machines); used for ablation.
TTL_COLS = ["sttl", "dttl", "ct_state_ttl"]

VAL_SIZE = 0.2   # share of the official train split held out for validation

# Seed for every random operation (splits, model init) so results reproduce.
RANDOM_STATE = 42
