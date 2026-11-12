import numpy as np
import pandas as pd
import pytest

from nids import config
from nids.preprocess import build_preprocessor, prepare, split_xy

needs_data = pytest.mark.skipif(
    not (config.TRAIN_CSV.exists() and config.TEST_CSV.exists()),
    reason="UNSW-NB15 CSVs not downloaded into data/raw/",
)


def tiny_frame(states, sbytes):
    n = len(states)
    return pd.DataFrame({
        "id": range(n), "proto": ["tcp"] * n, "service": ["-"] * n, "state": states,
        "sbytes": sbytes, "sttl": [254] * n,
        "attack_cat": ["Normal"] * n, "label": [0] * n,
    })


def test_split_xy_drops_id_and_targets():
    X, y = split_xy(tiny_frame(["FIN", "INT"], [100, 200]))
    assert not {"id", "label", "attack_cat"} & set(X.columns)
    assert list(y) == [0, 0]


def test_unseen_category_is_ignored_not_an_error():
    X_train, _ = split_xy(tiny_frame(["FIN", "INT"], [100, 200]))
    X_test, _ = split_xy(tiny_frame(["ACC"], [150]))     # ACC never seen in training
    pre = build_preprocessor(X_train).fit(X_train)
    out = pd.DataFrame(pre.transform(X_test), columns=pre.get_feature_names_out())
    assert out[["state_FIN", "state_INT"]].to_numpy().sum() == 0


def test_scaler_statistics_come_from_training_data_only():
    X_train, _ = split_xy(tiny_frame(["FIN"] * 3, [100, 100, 100]))
    X_test, _ = split_xy(tiny_frame(["FIN"], [1_000_000]))
    pre = build_preprocessor(X_train).fit(X_train)
    pre.transform(X_test)
    scaler = pre.named_transformers_["log_num"].named_steps["scale"]
    assert scaler.mean_[0] == pytest.approx(np.log1p(100))  # the huge test value had no effect


@pytest.fixture(scope="module")
def splits():
    return prepare()


@needs_data
def test_shapes_and_no_missing_values(splits):
    n_features = len(splits.feature_names)
    assert splits.X_train.shape == (140_272, n_features)
    assert splits.X_val.shape == (35_069, n_features)
    assert splits.X_test.shape == (82_332, n_features)
    for X in (splits.X_train, splits.X_val, splits.X_test):
        assert np.isfinite(X).all()


@needs_data
def test_no_label_information_in_features(splits):
    assert not [f for f in splits.feature_names if f.startswith(("attack_cat", "label", "id"))]


@needs_data
def test_exclude_removes_ttl_features():
    names = prepare(exclude=config.TTL_COLS).feature_names
    assert not set(config.TTL_COLS) & set(names)
