# Learning Log

A running record of how this project is built and why. Three parts:

1. **Architecture**: how the project is laid out and the decisions behind it
2. **Glossary**: the jargon, in plain English (with networking analogies where they fit)
3. **Change log**: what changed each phase, including the problems we hit

Updated every phase, alongside [PROGRESS.md](../PROGRESS.md).

---

## 1. Architecture

### Current layout

```
Network Intrusion Detection/      <- local folder (GitHub repo: unsw-nb15-nids)
├── data/
│   ├── raw/                      original UNSW-NB15 CSVs (git-ignored)
│   └── processed/                transformed data (git-ignored)
├── docs/
│   └── LEARNING_LOG.md           this file
├── models/                       saved trained models (git-ignored)
├── notebooks/
│   ├── 01_data_exploration.ipynb class balance, features, traps (Phase 2)
│   └── 02_preprocessing.ipynb    pipeline walkthrough + leakage demos (Phase 3)
├── reports/
│   ├── figures/                  charts used in the README (01_*, 02_*, 04_*)
│   └── metrics/rf.json           every RF number, machine-readable (committed)
├── src/nids/
│   ├── __init__.py               marks nids as an importable package
│   ├── config.py                 every path and constant in one place
│   ├── data.py                   load_split(): loads + validates a split
│   ├── preprocess.py             prepare(): train/val/test arrays, fitted on train only
│   ├── evaluate.py               shared metrics + confusion-matrix plot (all models)
│   └── train_rf.py               random forest: tune on val, test once, ablation
├── tests/
│   ├── test_evaluate.py          metrics checked against a hand calculation
│   ├── test_config.py            checks config paths are wired correctly
│   ├── test_data.py              checks row counts and schema of the data
│   └── test_preprocess.py        unseen categories, train-only fitting, no label columns
├── .gitignore                    what git must never track
├── .vscode/extensions.json       recommended VS Code extensions
├── pyproject.toml                package metadata + pytest settings
├── requirements.txt              libraries the project needs
├── PROGRESS.md                   phase checklist + how to resume
└── README.md                     the public face of the project
```

### How the pieces talk to each other

```
data/raw/*.csv ──► data.load_split ──► preprocess.prepare ──► models (Phase 4-5) ──► models/*.joblib, *.pt
                         ▲                                     │
                notebooks/ import from here                    ▼
                                                    reports/figures + README results
```

Notebooks are where we **explore**; `src/nids/` is where code goes once it has
to run the **same way every time**. Notebooks import from `src/`, never the
other way round.

### Decisions (and why)

| # | Decision | Why |
|---|---|---|
| D1 | Data and trained models are never committed | Large files bloat git history forever; the dataset has its own license. Folders are kept with `.gitkeep`. |
| D2 | Use the official training/testing CSVs as-is | Makes results comparable to published work. The test set is a sealed final exam: no tuning on it. |
| D3 | Validation set will be carved from the training set | Gives us a "practice exam" for tuning and early stopping without touching the test set (Phases 4-5). |
| D4 | All paths live in `config.py`, anchored on `__file__` | A path like `"data/raw"` depends on where you launched Python and breaks in notebooks. Anchoring on the file itself always works. |
| D5 | One random seed (`RANDOM_STATE = 42`) used everywhere | Same seed means same splits and same model init, so results can be reproduced. |
| D6 | `src/` layout + `pyproject.toml` pytest config | Tests import `nids` cleanly without path hacks. |
| D7 | `requirements.txt` uses minimum versions (`>=`) | Flexible across machines. Run `pip freeze > requirements-lock.txt` for an exact snapshot. |
| D8 | Keep downloaded CSVs untouched; fix the swapped names in `config.py` | The distributed files have train/test names swapped. Renaming by hand would differ on every machine; mapping in code is written down once and works everywhere. |
| D9 | `load_split()` checks row counts and fails loudly | Training on the wrong split would silently ruin every result. A check that crashes is better than a wrong answer. |
| D10 | Make `nids` an installable package (`pip install -e .`) | Notebooks in `notebooks/` can `from nids import ...` with no `sys.path` hacks. "Editable" means code changes take effect without reinstalling. |
| D11 | Drop `id` and `attack_cat` for binary models | `id` is a row number (no meaning); `attack_cat == "Normal"` exactly equals `label == 0`, so keeping it is label leakage. |
| D12 | Keep TTL features, but run an ablation without them in Phase 4 | `sttl` is the top signal only because of how the lab was set up. Measuring the drop without it shows whether the model learned attacks or machines. |
| D13 | Don't de-duplicate the official test set | It's the shared benchmark; changing it makes results incomparable. The 10.4% train/test overlap is documented instead. |
| D14 | One `ColumnTransformer` does all preprocessing, fitted once on the training part | Bundling the steps means they can't be applied in the wrong order or fitted on the wrong data. The same fitted object will serve the API in Phase 8. |
| D15 | 20% stratified validation split from official train | Big enough (35k rows) for reliable metrics; stratified so it has the same 68/32 mix as the training part. |
| D16 | `log1p` on 26 skewed columns, then standard scaling | Byte and packet counts have skew 40+. Trees don't care, but the neural net would otherwise be dominated by a few huge flows. |
| D17 | Same feature arrays for both models | A fair comparison: any difference in results comes from the model, not from different inputs. |
| D18 | Arrays stored as float32 | Half the memory of float64, and it's PyTorch's default type. |
| D19 | One shared `evaluate.py` for every model | The RF and the neural net are scored by identical code, so the Phase 6 comparison is fair. |
| D20 | Training is a script (`python -m nids.train_rf`), not a notebook | Reproducible in one command; notebooks are for exploring and explaining. |
| D21 | Tune 4 settings on validation, then evaluate on test exactly once | Picking settings by test score would make the test score optimistic (leakage through decisions). |
| D22 | Save metrics as JSON in git, models in `models/` (ignored) | Numbers are small and worth versioning; models are large and can be regenerated in a minute. |
| D23 | Report false-positive rate next to F1 | With attacks as the majority class, F1 can look good while a quarter of normal traffic raises alarms. |
| D24 | Keep the 0.5 threshold | Tuning it on test is leakage; validation has a 68% attack mix, so a threshold tuned there wouldn't transfer. |

---

## 2. Glossary

### Git & GitHub

| Term | Plain English | Networking analogy |
|---|---|---|
| **Repository (repo)** | A project folder whose full history git tracks. | |
| **Git** | Software that records snapshots of your files over time, so you can see or undo any change. | Like `archive` / config rollback on a router: every saved config is kept. |
| **Untracked file** | A file git can see but isn't recording yet. | |
| **Staging (`git add`)** | Choosing which changes go into the next snapshot. Like putting items in a box before sealing it. | |
| **Commit** | A sealed, labeled snapshot of the staged changes. | `copy running-config startup-config`, plus a note saying why. |
| **Conventional commit** | A message format: `type: summary`. `feat` = new feature, `fix` = bug fix, `chore` = setup/maintenance, `docs` = documentation. | |
| **Branch** | A separate line of work. `main` is the default. | |
| **Remote / `origin`** | A copy of the repo on another computer (GitHub). `origin` is just its nickname. | Like a TFTP server holding your backup configs. |
| **Push** | Upload your commits to the remote. | |
| **Upstream (tracking branch)** | The remote branch your local branch is linked to (`main` → `origin/main`). Lets plain `git push`/`git pull` work and makes `git status` report "ahead/behind". Check with `git branch -vv`. | A default route: once set, you don't name the destination every time. |
| **`-u` / `--set-upstream`** | Flag on the first push of a branch that saves the upstream link. Only needed once per branch; `git clone` sets it for you. | |
| **Clone** | Download a full copy of a remote repo. | |
| **Pathspec** | The file or folder name you gave a git command. "Pathspec did not match" = that path doesn't exist. | |
| **`.gitignore`** | A list of patterns git should pretend don't exist. | An ACL that denies certain files. |
| **`.gitkeep`** | An empty placeholder file. Git can't track empty folders, so this keeps the folder in the repo. | |

### Python environment

| Term | Plain English | Networking analogy |
|---|---|---|
| **Interpreter** | The program that runs Python code (`python.exe`). You can have several on one machine. | |
| **Global environment** | The Python installed on your whole computer. Installing project libraries here causes version clashes between projects. | |
| **Virtual environment (venv)** | A private copy of Python for one project, in `.venv/`. Its libraries don't affect anything else. Needed because global Python holds only one version of each package, so installing for project B can silently break project A. It's rebuildable from `requirements.txt`, so it is never committed. | A VRF/VLAN: same hardware, isolated tables. |
| **Activate** | Tell your terminal to use the venv's Python first. Your prompt shows `(.venv)`. | |
| **`sys.prefix`** | Tells you which environment Python is running in. Check it before installing. | `show ip interface brief` before configuring. |
| **PATH** | The list of folders Windows searches when you type a command. Activating a venv puts `.venv\Scripts` at the front. | A routing table: first match wins. |
| **pip** | Python's package installer. Downloads libraries from PyPI (the public library index). | |
| **Package / library** | Reusable code someone else wrote (pandas, torch). | |
| **Wheel** | A pre-built package file. If no wheel exists for your Python version, install can fail. | |
| **`requirements.txt`** | The shopping list of packages this project needs. | |
| **`pyproject.toml`** | The standard settings file for Python tools. Here it tells pytest where the code is. | |

### Code concepts

| Term | Plain English |
|---|---|
| **Module** | One `.py` file you can import (`config.py`). |
| **Package** | A folder of modules with an `__init__.py` (`src/nids/`). |
| **`import`** | Loading code from another module so you can use it. |
| **`__file__`** | A built-in variable holding the path of the current `.py` file. |
| **`pathlib.Path`** | A Python object for file paths. Joins with `/` and handles Windows backslashes for you. |
| **`.resolve()`** | Turns a path into its full absolute form (`C:\...`). |
| **`.parents[n]`** | Goes up `n+1` folder levels. From `src/nids/config.py`: `[0]` = `nids`, `[1]` = `src`, `[2]` = project root. |
| **Constant** | A value that shouldn't change, written in `UPPER_CASE` by convention. |
| **Unit test** | A tiny program that checks one piece of code does what it should. Run with `pytest`. |
| **Extension (VS Code)** | An add-on for the editor. Python + Jupyter are the ones we need. |

### Security & data

| Term | Plain English |
|---|---|
| **NIDS** | Network Intrusion Detection System: watches traffic and flags attacks. |
| **UNSW-NB15** | University of New South Wales, Network-Based dataset from 2015. Lab traffic with labeled attacks. |
| **pcap** | A raw packet capture file, what Wireshark or `tcpdump` saves. |
| **Flow record** | A one-row summary of a conversation (IPs, ports, protocol, bytes, packets, duration). Like NetFlow/IPFIX. Each CSV row is a flow. |
| **Argus / Zeek (Bro)** | Tools that turned UNSW-NB15's pcaps into flow features. |
| **KDD Cup 99 / NSL-KDD** | Older intrusion datasets built on 1998 traffic. UNSW-NB15 was made to replace them. |
| **`proto`** | The IP protocol of the flow (tcp, udp, arp, ospf...). Layer 3/4. |
| **`service`** | The application protocol guessed from the port (dns, http, ssh...). Layer 7. `-` means "not recognised", not missing. |
| **`state`** | The connection state. `FIN` = TCP closed cleanly, `CON` = two-way exchange, `INT` = no reply (93% attack), `REQ` = request waiting, `RST` = refused. |
| **`sbytes` / `dbytes`, `spkts` / `dpkts`** | Bytes and packets sent by the source vs. sent back by the destination. |
| **`dur`** | How long the flow lasted, in seconds. |
| **TTL (`sttl`, `dttl`)** | IP header hop counter. Starts at an OS-specific value (64/128/255) and drops by 1 per router. In this dataset it identifies the lab machines. |
| **Attack categories** | Generic, Exploits, Fuzzers, DoS, Reconnaissance, Analysis, Backdoor, Shellcode, Worms. Described in the exploration notebook. |
| **Mirror** | A copy of a dataset hosted by someone other than the original authors. Convenient, but verify it. |
| **Checksum (SHA-256)** | A fingerprint of a file. Same file = same fingerprint, so you can prove two machines have identical data. `Get-FileHash` on Windows. |

### Machine learning

| Term | Plain English |
|---|---|
| **Label** | The answer we want to predict. Here `label` = 0 (normal) or 1 (attack). |
| **Feature** | An input column the model learns from (e.g. `sbytes`). |
| **Training set** | Data the model learns from. |
| **Test set** | Data held back to measure final performance. Look at it once, at the end. |
| **Validation set** | A slice of training data used for tuning, so the test set stays untouched. |
| **Data leakage** | When information about the answer sneaks into the inputs, or test data influences training. Gives fake-good scores. |
| **Random seed** | A fixed starting number for randomness, so "random" results repeat exactly. |
| **EDA (exploratory data analysis)** | Looking at the data before modelling: sizes, balance, distributions, oddities. |
| **Class balance / imbalance** | How evenly the labels are split. Here attacks are the majority (68% train). |
| **Majority-class baseline** | The score you get by always guessing the most common label. Here "always attack" = 55.1% test accuracy. Any real model must beat it clearly. |
| **Accuracy** | % of predictions that are right. Misleading when classes are unbalanced. |
| **Precision / recall / F1** | Precision: of the flows we flagged, how many were attacks? Recall: of the real attacks, how many did we catch? F1 balances the two. (Used from Phase 4.) |
| **Distribution shift** | Train and test data don't look the same (68% vs 55% attack). Models can lose accuracy when this happens. |
| **Skewness** | How lopsided a distribution is. Byte counts have a skew of 40+: most flows are tiny, a few are huge. |
| **Log transform (`log1p`)** | Replacing x with log(1 + x) to squash huge values so they don't dominate. The `+1` keeps 0 valid. |
| **Correlation** | How strongly two columns move together, from 0 (unrelated) to 1 (identical pattern). |
| **One-hot encoding** | Turning a text column into 0/1 columns, one per value. `state=FIN` becomes `state_FIN=1`, all other `state_*`=0. (Phase 3.) |
| **Unseen category** | A value in test that never appeared in training (`ACC`, `CLO`). The encoder must ignore it instead of crashing. |
| **Shortcut learning** | A model latching onto an easy clue that only works in this dataset (TTL = which lab machine), not the real pattern. |
| **Ablation** | Removing a feature or component and re-measuring to see how much it mattered. |
| **Duplicate rows** | Identical rows. Floods and scans create many; they make the model over-weight those patterns. |
| **Irreducible error** | Mistakes no model can avoid, e.g. identical inputs labelled differently. |
| **Notebook (`.ipynb`)** | A document mixing code, its output and explanations. Good for exploring and showing work. |
| **Fit / transform** | `fit` *learns* from data (categories, mean, std). `transform` *applies* what was learned. Fit on train only; transform everything. |
| **Standardisation (StandardScaler)** | Rescale a column to mean 0, spread (std) 1: `(x − mean) / std`. Puts bytes and seconds on the same footing. |
| **Pipeline** | A chain of steps run in order as one object (e.g. log1p → scale). |
| **ColumnTransformer** | Applies different pipelines to different columns (one-hot for text, scaling for numbers) and glues the results together. |
| **Stratified split** | A random split that keeps the same label mix in each part. |
| **Decision tree** | A model that asks yes/no questions ("is sbytes > 430?") until it reaches an answer. A *stump* is a tree with one question. |
| **Overfitting** | Memorising the training data instead of learning general patterns. Shows up as a big gap between training and validation scores (99.8% vs 94.9% here). |
| **float32 / float64** | Number precision. float32 uses 4 bytes per number, float64 uses 8. ML rarely needs the extra precision. |
| **Random forest** | Many decision trees, each trained on a random resample of the rows and allowed to look at a random subset of features at each split. They vote; the majority wins. Averaging many over-confident trees cancels out their individual mistakes. |
| **Ensemble** | A model made of many models whose predictions are combined. |
| **Bagging (bootstrap aggregating)** | Training each tree on a random sample *with replacement* of the training rows, so every tree sees slightly different data. |
| **Hyperparameter** | A setting you choose before training (number of trees, leaf size), as opposed to what the model learns. Chosen on validation. |
| **`min_samples_leaf`** | The smallest group of rows a tree leaf may hold. Bigger = less memorising. |
| **`class_weight="balanced"`** | Makes mistakes on the rarer class cost more during training. Here it lowered false alarms but missed more attacks; F1 preferred the default. |
| **`predict_proba` / threshold** | The model outputs a score from 0 to 1 (the share of trees voting "attack"). The threshold (0.5) turns it into a yes/no. |
| **Confusion matrix** | 2×2 table of actual vs. predicted. **TP** = attack caught, **FN** = attack missed, **FP** = normal flagged (false alarm), **TN** = normal left alone. |
| **False-positive rate (FPR)** | FP / (FP + TN): the share of normal flows that raise an alarm. A SOC's alert-fatigue number. |
| **ROC AUC** | The chance a random attack gets a higher score than a random normal flow. 1.0 = perfect ranking, 0.5 = coin flip. Independent of the threshold. |
| **Feature importance (impurity)** | How much each feature's splits cleaned up the trees' groups, averaged. Quick, but biased toward features with many distinct values. |
| **Generalisation gap** | The drop from validation to test (F1 0.971 → 0.893 here): how much worse the model does on traffic unlike its training data. |
| **joblib** | Saves Python objects (a fitted model + preprocessor) to a file and loads them back. |
| **`python -m package.module`** | Runs a module inside an installed package as a script. |
| **Fixture (pytest)** | Setup code shared between tests, e.g. running `prepare()` once for several tests. |
| **Editable install (`pip install -e .`)** | Installs your own `src/` package as a link, so edits apply immediately and any script can import it. |

---

## 3. Change log

### Phase 1: Repo setup

**What we built**
- Folder skeleton (`data/`, `src/nids/`, `notebooks/`, `models/`, `reports/`, `tests/`)
- `.gitignore`, `requirements.txt`, `README.md`, `PROGRESS.md`, `.vscode/extensions.json`
- `src/nids/config.py` with all paths + `RANDOM_STATE`; `tests/test_config.py`; `pyproject.toml`
- This learning log

**What we did outside the code**
- Moved the project to `Downloads\Network Intrusion Detection`
- `git init`, first commit `chore: scaffold project structure, dependencies, and gitignore`
- Created GitHub repo `unsw-nb15-nids` and pushed `main`
- Created `.venv` (Python 3.14.7) and installed all requirements
- Second commit `feat: add path config, tests, and learning log`; plain `git push` worked because the first push used `-u`

**Problems we hit and what they taught us**

| Problem | Cause | Fix | Lesson |
|---|---|---|---|
| `fatal: pathspec '.vscode/extensions.json' did not match any files` | The folder move skipped `.vscode/`, so the file didn't exist. | Recreated the file and re-ran `git add`. | If any path in `git add` is wrong, **nothing** gets staged. Read the error's key phrase. |
| "Something went wrong activating IntelliCode" | IntelliCode is a deprecated VS Code extension, unrelated to our command. | Uninstall/disable IntelliCode. | Tell apart a failed *command* (terminal) from a complaining *editor* (popup). |
| VS Code: "packages installed into your global environment?" | VS Code saw `requirements.txt` while the workspace wasn't using `.venv`. | Dismiss; select `.venv` as interpreter; check `sys.prefix` before `pip install`. | Installing without the venv active is the #1 Python setup mistake. |

### Phase 2: Data exploration

**What we built**
- Downloaded and verified the dataset (row counts, columns and per-category counts match the paper); SHA-256 hashes recorded in PROGRESS.md
- `config.py`: swapped-name mapping, expected row counts, column-role constants (`ID_COL`, `TARGET`, `ATTACK_CAT`, `CATEGORICAL`)
- `src/nids/data.py`: `load_split()` with a row-count guard; `tests/test_data.py` (6 tests pass)
- `pyproject.toml`: project metadata so `pip install -e .` works; `nbclient`/`nbformat` added to requirements
- `notebooks/01_data_exploration.ipynb` and figures `01_class_balance.png`, `01_attack_categories.png`, `01_bytes_by_label.png`
- README: dataset note, citation, exploration highlights table

**What the data told us**
- Attacks are the majority: 68.1% train, 55.1% test
- Median attack flow: 2 packets out, 0 back, ~9 µs. `state=INT` (no reply) is 93% attack
- `sttl` is the strongest single signal (corr 0.69), and it's a lab artifact
- 42.4% of training rows are feature duplicates; 10.4% of test rows also appear in train

**Problems we hit and what they taught us**

| Problem | Cause | Fix | Lesson |
|---|---|---|---|
| "Done" but `data/raw/` was empty and the commit wasn't there | A second, older clone in `Downloads\unsw-nb15-nids` was open in VS Code | Work only in `Network Intrusion Detection`; check the folder before running commands | Confirm *where* you are (`pwd`) before git or data steps, like checking the hostname before pasting config. |
| Official UNSW SharePoint wouldn't open from the tool browser | Access was denied | Used a Hugging Face mirror, then verified it | A mirror is fine **if** you verify it against the source's published numbers. |
| Files named "training" had 82,332 rows, "testing" 175,341 | Names are swapped in the distributed copy | Mapped in `config.py`; loader checks row counts | Never trust a filename. Check row counts against the paper. |
| Notebook execution failed: "directory name is invalid" | `notebooks/` didn't exist (empty folders aren't copied or tracked) | Created the folder | Same root cause as `.gitkeep`: empty folders don't survive moves or git. |

### Phase 3: Preprocessing

**What we built**
- `src/nids/preprocess.py`: `split_xy()`, `build_preprocessor()`, `prepare()` returning train/val/test arrays + feature names + the fitted preprocessor
- `config.py`: `LOG_COLS` (26 skewed columns), `TTL_COLS` (for the ablation), `VAL_SIZE = 0.2`
- `tests/test_preprocess.py`: unseen categories are ignored, scaler stats come from train only, shapes, no NaNs, no label columns, TTL exclusion
- `notebooks/02_preprocessing.ipynb` with two live demos, and figure `02_log_and_scale.png`

**What the demos showed**
- Leaving `attack_cat` in: a one-question tree scores **100.0%** on test. That's what leakage looks like
- An unlimited decision tree: **99.8%** on its own training data vs **94.9%** on validation. Never report training scores
- After scaling, train columns are exactly mean 0 / std 1, while test drifts slightly (+0.025). That gap is proof we didn't fit on test

**Problems we hit and what they taught us**

| Problem | Cause | Fix | Lesson |
|---|---|---|---|
| Phase 2 work wasn't committed when Phase 3 started | Commit step skipped | Committed and pushed Phase 2 on its own before Phase 3 | One commit per phase keeps history readable, and only pushed commits count on your GitHub graph. |
| Training part has 7 states, not 9 | The single `PAR` and `URN` rows fell into validation | Nothing to fix: `handle_unknown="ignore"` covers it | The encoder only knows what it was fitted on. Rare values can vanish from a split. |

### Phase 4: Random forest baseline

**What we built**
- `src/nids/evaluate.py`: one set of metrics and plots for every model
- `src/nids/train_rf.py`: tuning on validation, one test evaluation, TTL ablation, false-positive analysis; saves `reports/metrics/rf.json` and `models/rf.joblib`
- `tests/test_evaluate.py`: metrics checked against a 10-row hand calculation
- Figures `04_rf_confusion_test.png`, `04_rf_feature_importance.png`; README results section

**What the results told us**
- Test: recall **98.7%**, precision **81.6%**, F1 **0.893**, false-positive rate **27.2%**, ROC AUC 0.979
- Validation F1 0.971 vs test 0.893: the official test traffic differs from the training traffic
- 88% of false alarms have TTL 254. Normal traffic with TTL 254 doubles from 20.1% (train) to 40.7% (test)
- Removing the TTL columns changed almost nothing (F1 0.892). The shortcut runs deeper than three columns

**Problems we hit and what they taught us**

| Problem | Cause | Fix | Lesson |
|---|---|---|---|
| Phase 2 hypothesis ("dropping TTL will show the shortcut") wasn't confirmed | Other features carry the same host signal | Reported it as-is, with the false-positive TTL breakdown as evidence | A negative result is still a result. Report it instead of hiding it. |
| A quick check counted 9,961 false positives, the script 10,081 | `predict()` breaks exact 0.5 ties toward "normal"; the script uses `score >= 0.5` | Moved the analysis into the training script so all numbers come from one place | Small definition differences change numbers. Compute every reported number in one place. |
| `rf.json` contained `NaN` (invalid JSON) | pandas turned `class_weight=None` into NaN | Converted missing values to `None` before saving | Always re-load files you write to check they're valid. |
