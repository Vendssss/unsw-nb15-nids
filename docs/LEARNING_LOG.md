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
├── notebooks/                    exploration (Phase 2+)
├── reports/figures/              charts used in the README
├── src/nids/
│   ├── __init__.py               marks nids as an importable package
│   └── config.py                 every path and constant in one place
├── tests/
│   └── test_config.py            checks config paths are wired correctly
├── .gitignore                    what git must never track
├── .vscode/extensions.json       recommended VS Code extensions
├── pyproject.toml                tool settings (pytest for now)
├── requirements.txt              libraries the project needs
├── PROGRESS.md                   phase checklist + how to resume
└── README.md                     the public face of the project
```

### How the pieces talk to each other

```
data/raw/*.csv ──► src/nids (config → preprocessing → models) ──► models/*.joblib, *.pt
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
| **Clone** | Download a full copy of a remote repo. | |
| **Pathspec** | The file or folder name you gave a git command. "Pathspec did not match" = that path doesn't exist. | |
| **`.gitignore`** | A list of patterns git should pretend don't exist. | An ACL that denies certain files. |
| **`.gitkeep`** | An empty placeholder file. Git can't track empty folders, so this keeps the folder in the repo. | |

### Python environment

| Term | Plain English | Networking analogy |
|---|---|---|
| **Interpreter** | The program that runs Python code (`python.exe`). You can have several on one machine. | |
| **Global environment** | The Python installed on your whole computer. Installing project libraries here causes version clashes between projects. | |
| **Virtual environment (venv)** | A private copy of Python for one project, in `.venv/`. Its libraries don't affect anything else. | A VRF/VLAN: same hardware, isolated tables. |
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
- Created `.venv` (Python 3.14.7)

**Problems we hit and what they taught us**

| Problem | Cause | Fix | Lesson |
|---|---|---|---|
| `fatal: pathspec '.vscode/extensions.json' did not match any files` | The folder move skipped `.vscode/`, so the file didn't exist. | Recreated the file and re-ran `git add`. | If any path in `git add` is wrong, **nothing** gets staged. Read the error's key phrase. |
| "Something went wrong activating IntelliCode" | IntelliCode is a deprecated VS Code extension, unrelated to our command. | Uninstall/disable IntelliCode. | Tell apart a failed *command* (terminal) from a complaining *editor* (popup). |
| VS Code: "packages installed into your global environment?" | VS Code saw `requirements.txt` while the workspace wasn't using `.venv`. | Dismiss; select `.venv` as interpreter; check `sys.prefix` before `pip install`. | Installing without the venv active is the #1 Python setup mistake. |
