# Progress Log

Resume point for working across machines. Update after every phase.

## Status

| Phase | Description | Status |
|---|---|---|
| 1 | Repo setup | ✅ Done (pending first commit) |
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
5. Read the latest phase notes below, then continue from **Next step**

## Phase notes

### Phase 1: Repo setup

- Created folder layout: `data/{raw,processed}`, `notebooks/`, `src/nids/`, `models/`, `reports/figures/`, `tests/`
- `.gitignore` excludes data, model artifacts, `.venv`, notebook checkpoints
- `requirements.txt` with lower-bound versions; Python 3.14 on dev machine
- Exercise assigned: write `src/nids/config.py` (path constants with `pathlib`)

**Decisions**
- Use the official training/testing CSVs as-is; never tune on the test set
- Validation split will be carved out of the training set (phases 4–5)

## Next step

Finish `src/nids/config.py` exercise, then Phase 2: data exploration notebook.
