"""Metrics and plots shared by every model, so results are directly comparable."""

import json

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from nids import config

METRICS_DIR = config.PROJECT_ROOT / "reports" / "metrics"


def binary_metrics(y_true, y_pred, y_score=None) -> dict:
    """Attack (1) is the positive class: precision/recall/F1 describe attack detection."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    metrics = {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        # Share of normal flows wrongly flagged: the "alert fatigue" number for a SOC.
        "false_positive_rate": fp / (fp + tn),
        "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }
    if y_score is not None:
        metrics["roc_auc"] = roc_auc_score(y_true, y_score)
    return {k: (round(float(v), 4) if not isinstance(v, dict) else v) for k, v in metrics.items()}


def save_metrics(name: str, metrics: dict) -> None:
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    (METRICS_DIR / f"{name}.json").write_text(json.dumps(metrics, indent=2))


def plot_confusion(metrics: dict, title: str, filename: str) -> None:
    """2×2 confusion matrix with counts and row percentages."""
    c = metrics["confusion"]
    cm = np.array([[c["tn"], c["fp"]], [c["fn"], c["tp"]]])
    row_share = cm / cm.sum(axis=1, keepdims=True)

    fig, ax = plt.subplots(figsize=(4.6, 4))
    fig.patch.set_facecolor("#fcfcfb")
    ax.imshow(row_share, cmap="Blues", vmin=0, vmax=1)
    for i in range(2):
        for j in range(2):
            ink = "#fcfcfb" if row_share[i, j] > 0.5 else "#0b0b0b"
            ax.text(j, i, f"{cm[i, j]:,}\n{row_share[i, j]:.1%}", ha="center", va="center", color=ink)
    ax.set_xticks([0, 1], ["normal", "attack"])
    ax.set_yticks([0, 1], ["normal", "attack"])
    ax.set_xlabel("predicted")
    ax.set_ylabel("actual")
    ax.set_title(title, loc="left", fontsize=10)
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / filename, dpi=150, bbox_inches="tight")
    plt.close(fig)
