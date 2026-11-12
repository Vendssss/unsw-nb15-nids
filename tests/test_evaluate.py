import pytest

from nids.evaluate import binary_metrics


def test_metrics_match_hand_calculation():
    # 4 normal, 6 attack. Predictions: 1 normal flagged (FP), 2 attacks missed (FN).
    y_true = [0, 0, 0, 0, 1, 1, 1, 1, 1, 1]
    y_pred = [0, 0, 0, 1, 1, 1, 1, 1, 0, 0]
    m = binary_metrics(y_true, y_pred)

    assert m["confusion"] == {"tn": 3, "fp": 1, "fn": 2, "tp": 4}
    assert m["precision"] == pytest.approx(4 / 5)          # tp / (tp + fp)
    assert m["recall"] == pytest.approx(4 / 6, abs=1e-4)   # tp / (tp + fn)
    assert m["false_positive_rate"] == pytest.approx(1 / 4)
    assert m["accuracy"] == pytest.approx(7 / 10)


def test_always_attack_has_perfect_recall_but_useless_fpr():
    m = binary_metrics([0, 0, 1, 1, 1], [1, 1, 1, 1, 1])
    assert m["recall"] == 1.0
    assert m["false_positive_rate"] == 1.0
