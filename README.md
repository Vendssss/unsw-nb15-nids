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
place them in `data/raw/`:

```
data/raw/UNSW_NB15_training-set.csv
data/raw/UNSW_NB15_testing-set.csv
```

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
```

## Results

_Coming in phases 4–6._

## Model comparison

_Coming in phase 6._
