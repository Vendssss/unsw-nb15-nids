# Network Intrusion Detection on UNSW-NB15

Classifying network flows as **normal** or **attack** using the
[UNSW-NB15](https://research.unsw.edu.au/projects/unsw-nb15-dataset) dataset,
comparing a scikit-learn random forest against a PyTorch feed-forward network.

> 🚧 Work in progress. See [PROGRESS.md](PROGRESS.md) for current status and
> [docs/LEARNING_LOG.md](docs/LEARNING_LOG.md) for design decisions and a glossary.

## Goals

- Binary classification (normal vs. attack) evaluated on the **official test split**
- Honest comparison of a tree ensemble vs. a neural network on tabular data
- Metrics that matter for imbalanced security data: precision, recall, F1, confusion matrix
- Stretch: multi-class by attack category; FastAPI prediction service in Docker

## Dataset

UNSW-NB15 was created by the Cyber Range Lab at UNSW Canberra. Each row is a
network flow described by features such as protocol, service, connection state,
bytes, packets, and duration.

The data is **not** included in this repo. Download the two partitioned CSVs and
place them in `data/raw/` without renaming them:

```
data/raw/UNSW_NB15_training-set.csv
data/raw/UNSW_NB15_testing-set.csv
```

> **Note on file names:** in the distributed copies, the names are swapped relative to
> the paper. The official training split (175,341 flows) is in `UNSW_NB15_testing-set.csv`,
> and the official testing split (82,332 flows) is in `UNSW_NB15_training-set.csv`.
> [`src/nids/config.py`](src/nids/config.py) maps them correctly, and the loader checks
> row counts so a mix-up fails loudly.

**Citation:** N. Moustafa and J. Slay, "UNSW-NB15: a comprehensive data set for network
intrusion detection systems (UNSW-NB15 network data set)," *Military Communications and
Information Systems Conference (MilCIS)*, 2015.

## Data exploration highlights

Full analysis: [notebooks/01_data_exploration.ipynb](notebooks/01_data_exploration.ipynb)

| Finding | Why it matters |
|---|---|
| Attacks are the **majority**: 68.1% of train, 55.1% of test | Always predicting "attack" scores 55.1% test accuracy, so accuracy alone is misleading |
| Nine attack families from 40,000 (Generic) down to 130 (Worms) flows | Rare classes will be hard in multi-class |
| Median attack flow: 2 packets out, **0 back**, ~9 µs | Scans and floods rarely get a reply; `state=INT` (no reply) is 93% attack |
| Source TTL is the strongest single signal (corr 0.69) | A lab artifact: TTL identifies the attacker machines. Tested with an ablation in Phase 4 |
| 42.4% of training rows repeat another row's features; 10.4% of test rows also appear in train | Documented, not hidden; slightly inflates test scores |

![Class balance](reports/figures/01_class_balance.png)
![Bytes by label](reports/figures/01_bytes_by_label.png)

## Preprocessing

Walkthrough: [notebooks/02_preprocessing.ipynb](notebooks/02_preprocessing.ipynb) · Code: [src/nids/preprocess.py](src/nids/preprocess.py)

1. Drop `id` (row number) and `attack_cat` (encodes the label: with it, a one-question tree scores 100% on test)
2. Hold out 20% of the official training split as a stratified validation set
3. One-hot encode `proto`, `service`, `state`; categories unseen in training are ignored
4. `log1p` on 26 heavily skewed volume and timing features, then standard scaling
5. **Fit on the training part only**; validation and test are transform-only

| Split | Flows | Features | Attack share |
|---|---|---|---|
| Train | 140,272 | 192 | 68.1% |
| Validation | 35,069 | 192 | 68.1% |
| Test (official) | 82,332 | 192 | 55.1% |

## Project structure

```
data/raw/          original CSVs (git-ignored)
data/processed/    transformed data (git-ignored)
docs/              learning log: architecture decisions + glossary
notebooks/         exploration and experiments
src/nids/          reusable code: config, preprocessing, models
models/            trained model artifacts (git-ignored)
reports/figures/   plots used in this README
tests/             unit tests
```

## Setup (Windows / PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
pytest
```

`pip install -e .` makes the `nids` package importable from notebooks and scripts.

## Results

_Coming in phases 4–6._

## Model comparison

_Coming in phase 6._
