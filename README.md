# Lidl Promotions Fetcher

This script fetches current promotions from the Lidl Bulgaria website and saves them to a JSON file.

## Requirements

You need Python 3 installed. This script uses the `requests` library.

## Setup (uv)

Create a uv-managed virtual environment and install dependencies:

```bash
uv venv .venv
uv pip install --python .venv/bin/python requests
```

Activate the virtual environment:

```bash
source .venv/bin/activate
```

## How to run

Run the script using Python:

```bash
python fetch_promos.py
```

This will create or overwrite a `promotions.json` file in the same directory with the latest promotions data.
