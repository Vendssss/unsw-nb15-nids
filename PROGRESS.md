# Progress Log

Resume point for working across machines. Update after every phase.

## Status

| Phase | Description | Status |
|---|---|---|
| 1 | Repo setup | ✅ Done |
| 2 | Data exploration | ✅ Done |
| 3 | Preprocessing | ✅ Done |
| 4 | Random forest baseline | ✅ Done |
| 5 | PyTorch feed-forward network | ⏭️ Next |
| 6 | Honest model comparison in README | ⬜ |
| 7 | Stretch: multi-class by attack category | ⬜ |
| 8 | Stretch: FastAPI endpoint + Dockerfile | ⬜ |

## Resume on a new machine

1. `git clone https://github.com/Vendssss/unsw-nb15-nids.git` and `cd` into it
2. `python -m venv .venv` then `.venv\Scripts\Activate.ps1`
3. `pip install -r requirements.txt` then `pip install -e .`
4. Put the two UNSW-NB15 CSVs into `data/raw/` **with their original names** (data is not in git). Source used: Hugging Face `Mireu-Lab/UNSW-NB15`, file `Archives/UNSW-NB15.zip`; or the official UNSW SharePoint
5. Check the files match (PowerShell: `Get-FileHash data\raw\*.csv`):
   - `UNSW_NB15_testing-set.csv` (official **train**, 175,341 rows): `BEC7DD5EC88DC2A0CCC7A07879D338395ED7421750F675FD0339E07DFE0648FA`
   - `UNSW_NB15_training-set.csv` (official **test**, 82,332 rows): `734FE6642EDF758F7C94D7D9149426B49D202FE8E7BF0BEF47392489C3C0A559`
6. Run `pytest` (14 should pass). To regenerate the RF model (git-ignored): `python -m nids.train_rf` (~1 min), read the latest phase notes below, then continue from **Next step**

For the why behind each decision and a plain-English glossary, see [docs/LEARNING_LOG.md](docs/LEARNING_LOG.md).

## Phase notes

### Phase 1: Repo setup

- Folder layout, `.gitignore`, `requirements.txt`, README, this file
- `src/nids/config.py`: all paths anchored on `__file__`, plus `RANDOM_STATE = 42`
- `docs/LEARNING_LOG.md`: architecture, glossary, change log
- GitHub: `Vendssss/unsw-nb15-nids`, branch `main`; `.venv` on Python 3.14.7

### Phase 2: Data exploration

- Dataset downloaded and verified (row counts, columns, per-category counts match the paper)
- **File names are swapped** in the distributed copy; `config.py` maps `TRAIN_CSV` → `testing-set.csv`, `TEST_CSV` → `training-set.csv`
- `src/nids/data.py`: `load_split("train" | "test")` with row-count check; `tests/test_data.py`
- `pyproject.toml` makes `nids` pip-installable (`pip install -e .`) so notebooks can import it
- `notebooks/01_data_exploration.ipynb` (executed) + 3 figures in `reports/figures/`
- README: dataset note, citation, exploration highlights

**Key numbers**
- Train 175,341 flows (68.1% attack), test 82,332 (55.1% attack). "Always attack" baseline = 55.1% test accuracy
- 9 attack categories; Generic 40,000 to Worms 130 in train
- 133 `proto` values, 13 `service` (54% are `-`), 9 `state`; `ACC` and `CLO` appear only in test
- `sttl` correlation with label 0.69 (lab artifact), `ct_state_ttl` 0.58
- 42.4% duplicate feature rows in train; 229 patterns with conflicting labels; 10.4% of test rows appear in train

**Decisions**
- Drop `id` and `attack_cat` for binary models (`attack_cat` encodes the label)
- One-hot `proto`, `service`, `state` with `handle_unknown="ignore"`
- Consider `log1p` on skewed volume features before scaling (matters for the NN)
- Keep TTL features for headline results; Phase 4 adds an ablation without `sttl`, `dttl`, `ct_state_ttl`
- Don't de-duplicate the official test set; document the overlap instead

**Open exercise:** `bytes_ratio(df)` at the end of the notebook (send for review)

### Phase 3: Preprocessing

- `src/nids/preprocess.py`: `split_xy()`, `build_preprocessor()`, `prepare(exclude=(), log_transform=True)` → `Splits` dataclass
- Pipeline: drop `id`/`attack_cat`/`label` → one-hot `proto`/`service`/`state` (`handle_unknown="ignore"`) → `log1p` on 26 skewed columns (`config.LOG_COLS`) → `StandardScaler`
- Validation: 20% of official train, stratified, `random_state=42`
- Fit on the training part only; validation and test are transform-only
- `tests/test_preprocess.py` (6 tests; 12 total pass)
- `notebooks/02_preprocessing.ipynb` (executed) + `reports/figures/02_log_and_scale.png`

**Key numbers**
- Train 140,272 × 192, val 35,069 × 192, test 82,332 × 192 (133 proto + 13 service + 7 state + 39 numeric)
- Attack share: train 68.1%, val 68.1% (stratified), test 55.1%
- Leakage demo: keeping `attack_cat` gives a depth-1 tree **100.0%** test accuracy
- Overfitting demo: unlimited decision tree 99.8% on train vs 94.9% on validation (depth 44, 4,692 leaves)
- Scaled test columns drift (mean +0.025) as expected; train is exactly 0/1

**Decisions**
- Same features for RF and NN; log/scale is harmless for trees and needed for the NN
- `prepare(exclude=config.TTL_COLS)` for the Phase 4 ablation
- Arrays are float32 (half the memory, what PyTorch uses)

**Open exercise:** `test_validation_keeps_class_ratio` in `tests/test_preprocess.py` (see end of notebook 02)

### Phase 4: Random forest baseline

- `src/nids/evaluate.py`: `binary_metrics()` (accuracy, precision, recall, F1, false-positive rate, ROC AUC, confusion counts), `plot_confusion()`, `save_metrics()`; reused by Phase 5
- `src/nids/train_rf.py` (`python -m nids.train_rf`, ~1 min on 12 threads): tunes 4 settings on validation, one test evaluation, TTL ablation, false-positive TTL check
- Outputs: `reports/metrics/rf.json` (committed), `models/rf.joblib` (git-ignored, preprocessor + model), figures `04_rf_confusion_test.png`, `04_rf_feature_importance.png`
- `tests/test_evaluate.py` (hand-calculated confusion matrix); 14 tests pass

**Key numbers (test, attack = positive)**
- Accuracy 87.0%, precision 81.6%, recall 98.7%, F1 0.893, false-positive rate 27.2%, ROC AUC 0.979
- Confusion: TN 26,919 · FP 10,081 · FN 610 · TP 44,722
- Validation F1 0.971 → test F1 0.893 (different traffic in the official test split)
- Best settings: `min_samples_leaf=1`, `class_weight=None` (val F1 0.9709)
- Ablation without TTL: F1 0.892, false-positive rate 27.4%, so essentially no change
- 88.0% of false positives have `sttl=254`; normal flows with TTL 254 are 20.1% in train vs 40.7% in test
- Top features: `sttl`, `ct_state_ttl`, `dttl`, `dload`, `rate`

**Decisions**
- Threshold stays at 0.5: tuning it on test would be leakage, and validation has the wrong mix to tune it for test
- Report the false-positive rate alongside F1 (SOC alert-fatigue view)

**Open exercises:** `bytes_ratio` (notebook 01), `test_validation_keeps_class_ratio` (notebook 02), compute precision/recall by hand from the confusion matrix (see chat)

## Next step

Phase 5: PyTorch feed-forward network on the same `prepare()` arrays, with early stopping on validation and class-imbalance handling, evaluated with `nids.evaluate`.
