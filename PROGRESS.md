# Progress Log

Resume point for working across machines. Update after every phase.

## Status

| Phase | Description | Status |
|---|---|---|
| 1 | Repo setup | ✅ Done |
| 2 | Data exploration | ✅ Done |
| 3 | Preprocessing | ⏭️ Next |
| 4 | Random forest baseline | ⬜ |
| 5 | PyTorch feed-forward network | ⬜ |
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
6. Run `pytest` (6 should pass), read the latest phase notes below, then continue from **Next step**

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

## Next step

Phase 3: preprocessing pipeline in `src/nids/preprocess.py` (drop leaky columns, one-hot, scale, fit on train only), plus a validation split carved from train.
