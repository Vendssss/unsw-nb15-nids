"""Random forest baseline.

Run with:  python -m nids.train_rf

1. Try a few settings, scoring each on the validation set (never the test set).
2. Evaluate the best one on the test set exactly once.
3. Repeat the final model without TTL features to measure the lab shortcut.
"""

import time

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from nids import config
from nids.data import load_split
from nids.evaluate import binary_metrics, plot_confusion, save_metrics
from nids.preprocess import prepare

# Small, explainable search: leaf size controls memorisation, class_weight
# controls how much each class counts during training.
CANDIDATES = [
    {"min_samples_leaf": 1, "class_weight": None},
    {"min_samples_leaf": 5, "class_weight": None},
    {"min_samples_leaf": 1, "class_weight": "balanced"},
    {"min_samples_leaf": 5, "class_weight": "balanced"},
]


def make_forest(params: dict) -> RandomForestClassifier:
    return RandomForestClassifier(
        n_estimators=200,
        max_features="sqrt",       # each split considers ~14 of 192 features
        n_jobs=-1,
        random_state=config.RANDOM_STATE,
        **params,
    )


def evaluate(model, X, y) -> dict:
    score = model.predict_proba(X)[:, 1]
    return binary_metrics(y, (score >= 0.5).astype(int), score)


def tune(s) -> tuple[dict, pd.DataFrame]:
    rows = []
    for params in CANDIDATES:
        start = time.perf_counter()
        model = make_forest(params).fit(s.X_train, s.y_train)
        m = evaluate(model, s.X_val, s.y_val)
        rows.append({**params, **{k: m[k] for k in ("precision", "recall", "f1", "false_positive_rate")},
                     "seconds": round(time.perf_counter() - start, 1)})
        print(f"  {params} -> val F1 {m['f1']:.4f}")
    table = pd.DataFrame(rows).astype(object)
    table = table.where(table.notna(), None)    # class_weight=None stays null in JSON
    best = CANDIDATES[int(pd.to_numeric(table["f1"]).idxmax())]
    return best, table


def plot_importances(model, feature_names, filename, top=15):
    imp = pd.Series(model.feature_importances_, index=feature_names).nlargest(top).sort_values()
    fig, ax = plt.subplots(figsize=(6.5, 4.4))
    fig.patch.set_facecolor("#fcfcfb")
    ax.set_facecolor("#fcfcfb")
    ax.barh(imp.index, imp.values, color="#2a78d6", height=0.7)
    ax.set_xlabel("mean decrease in impurity")
    ax.set_title(f"Random forest: top {top} features", loc="left", fontsize=10)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.grid(axis="x", color="#e6e5e0", linewidth=0.6)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return imp.sort_values(ascending=False)


def main():
    s = prepare()

    print("Tuning on validation:")
    best, table = tune(s)
    print(table.to_string(index=False))
    print("best:", best)

    model = make_forest(best).fit(s.X_train, s.y_train)
    val = evaluate(model, s.X_val, s.y_val)
    test = evaluate(model, s.X_test, s.y_test)          # the one and only test evaluation
    always_attack = binary_metrics(s.y_test, np.ones_like(s.y_test))

    print("\nvalidation:", {k: val[k] for k in ("precision", "recall", "f1")})
    print("test:      ", {k: test[k] for k in ("accuracy", "precision", "recall", "f1", "false_positive_rate", "roc_auc")})
    print("always-attack baseline on test:", {k: always_attack[k] for k in ("accuracy", "precision", "recall", "f1")})

    imp = plot_importances(model, s.feature_names, "04_rf_feature_importance.png")
    print("\ntop features:\n", imp.head(10).round(4).to_string())
    plot_confusion(test, "Random forest, official test set", "04_rf_confusion_test.png")

    # Which normal flows get flagged? Compare their source TTL with training-normal traffic.
    test_raw, train_raw = load_split("test"), load_split("train")
    pred = (model.predict_proba(s.X_test)[:, 1] >= 0.5).astype(int)
    normal = test_raw[s.y_test == 0].assign(flagged=pred[s.y_test == 0] == 1)
    ttl_check = {
        "false_positives": int(normal["flagged"].sum()),
        "fp_share_with_sttl_254": round(float((normal.loc[normal["flagged"], "sttl"] == 254).mean()), 4),
        "normal_share_sttl_254_train": round(float((train_raw.loc[train_raw[config.TARGET] == 0, "sttl"] == 254).mean()), 4),
        "normal_share_sttl_254_test": round(float((normal["sttl"] == 254).mean()), 4),
    }
    print("false-positive TTL check:", ttl_check)

    print("\nAblation: same settings without TTL features")
    s_nottl = prepare(exclude=config.TTL_COLS)
    model_nottl = make_forest(best).fit(s_nottl.X_train, s_nottl.y_train)
    val_nottl = evaluate(model_nottl, s_nottl.X_val, s_nottl.y_val)
    test_nottl = evaluate(model_nottl, s_nottl.X_test, s_nottl.y_test)
    print("test without TTL:", {k: test_nottl[k] for k in ("accuracy", "precision", "recall", "f1", "false_positive_rate")})

    save_metrics("rf", {
        "params": {"n_estimators": 200, "max_features": "sqrt", **best},
        "tuning": table.to_dict(orient="records"),
        "validation": val,
        "test": test,
        "baseline_always_attack_test": always_attack,
        "ablation_no_ttl": {"validation": val_nottl, "test": test_nottl},
        "false_positive_ttl_check": ttl_check,
        "top_features": imp.head(15).round(4).to_dict(),
    })
    config.MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump({"preprocessor": s.preprocessor, "model": model}, config.MODELS_DIR / "rf.joblib", compress=3)
    print("\nsaved reports/metrics/rf.json and models/rf.joblib")


if __name__ == "__main__":
    main()
