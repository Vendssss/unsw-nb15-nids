# Progress Log

Resume point for working across machines. Update after every phase.

## Status

| Phase | Description | Status |
|---|---|---|
| 1 | Repo setup | ✅ Done |
| 2 | Data exploration | ⏭️ Next |
| 3 | Preprocessing | ⬜ |
| 4 | Random forest baseline | ⬜ |
| 5 | PyTorch feed-forward network | ⬜ |
| 6 | Honest model comparison in README | ⬜ |
| 7 | Stretch: multi-class by attack category | ⬜ |
| 8 | Stretch: FastAPI endpoint + Dockerfile | ⬜ |

## Resume on a new machine

1. `git clone <repo-url>` and `cd` into it
2. `python -m venv .venv` then `.venv\Scripts\Activate.ps1`
3. `pip install -r requirements.txt`
4. Download the UNSW-NB15 training and testing CSVs into `data/raw/` (data is not in git)
5. Run `pytest` (should pass), read the latest phase notes below, then continue from **Next step**

For the why behind each decision and a plain-English glossary, see [docs/LEARNING_LOG.md](docs/LEARNING_LOG.md).

## Phase notes

### Phase 1: Repo setup

- Created folder layout: `data/{raw,processed}`, `notebooks/`, `src/nids/`, `models/`, `reports/figures/`, `tests/`
- `.gitignore` excludes data, model artifacts, `.venv`, notebook checkpoints
- `requirements.txt` with lower-bound versions; Python 3.14 on dev machine
- `src/nids/config.py`: all paths anchored on `__file__`, plus `RANDOM_STATE = 42`
- `tests/test_config.py` + `pyproject.toml` (pytest finds `src/`)
- `docs/LEARNING_LOG.md`: architecture, glossary, change log
- GitHub: `Vendssss/unsw-nb15-nids`, branch `main`
- `.venv` created (Python 3.14.7); packages being installed

**Decisions**
- Use the official training/testing CSVs as-is; never tune on the test set
- Validation split will be carved out of the training set (phases 4–5)

## Next step

1. Finish `pip install -r requirements.txt` inside the active `.venv`
2. Download the two CSVs into `data/raw/`
3. Start Phase 2: data exploration notebook
