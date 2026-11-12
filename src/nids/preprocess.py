"""Turning raw flows into model-ready arrays.

The rule this module enforces: every statistic (category lists, means, standard
deviations) is learned from the training portion only, then applied unchanged
to validation and test data.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from nids import config
from nids.data import load_split

# Never features: a row number and the two targets (attack_cat encodes the label).
NON_FEATURES = [config.ID_COL, config.TARGET, config.ATTACK_CAT]


def split_xy(df: pd.DataFrame, exclude=()) -> tuple[pd.DataFrame, pd.Series]:
    """Separate features from the binary label, dropping non-features and `exclude`."""
    X = df.drop(columns=NON_FEATURES + list(exclude))
    y = df[config.TARGET]
    return X, y


def build_preprocessor(X: pd.DataFrame, log_transform: bool = True) -> ColumnTransformer:
    """One-hot the categorical columns; log1p (optional) + standardise the numeric ones.

    `X` is only used to read column names, nothing is fitted here.
    """
    categorical = [c for c in config.CATEGORICAL if c in X.columns]
    numeric = [c for c in X.columns if c not in categorical]
    log_cols = [c for c in config.LOG_COLS if c in numeric] if log_transform else []
    plain_cols = [c for c in numeric if c not in log_cols]

    onehot = OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=np.float32)
    log_then_scale = Pipeline([
        ("log1p", FunctionTransformer(np.log1p, feature_names_out="one-to-one")),
        ("scale", StandardScaler()),
    ])

    return ColumnTransformer(
        [
            ("cat", onehot, categorical),
            ("log_num", log_then_scale, log_cols),
            ("num", StandardScaler(), plain_cols),
        ],
        verbose_feature_names_out=False,
    )


@dataclass
class Splits:
    X_train: np.ndarray
    y_train: np.ndarray
    X_val: np.ndarray
    y_val: np.ndarray
    X_test: np.ndarray
    y_test: np.ndarray
    feature_names: list[str]
    preprocessor: ColumnTransformer


def prepare(exclude=(), log_transform: bool = True) -> Splits:
    """Load the official split, carve a stratified validation set, fit on train only."""
    X_full, y_full = split_xy(load_split("train"), exclude)
    X_test, y_test = split_xy(load_split("test"), exclude)

    X_train, X_val, y_train, y_val = train_test_split(
        X_full, y_full,
        test_size=config.VAL_SIZE,
        stratify=y_full,               # keep the 68/32 attack/normal mix in both parts
        random_state=config.RANDOM_STATE,
    )

    pre = build_preprocessor(X_train, log_transform)
    to32 = lambda a: np.asarray(a, dtype=np.float32)

    return Splits(
        X_train=to32(pre.fit_transform(X_train)),   # fit happens here, and only here
        y_train=y_train.to_numpy(),
        X_val=to32(pre.transform(X_val)),
        y_val=y_val.to_numpy(),
        X_test=to32(pre.transform(X_test)),
        y_test=y_test.to_numpy(),
        feature_names=list(pre.get_feature_names_out()),
        preprocessor=pre,
    )
