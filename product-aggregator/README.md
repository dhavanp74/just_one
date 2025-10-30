# Product Aggregator

Small project to scrape product listings from multiple e-commerce sites (Amazon, Flipkart, JioMart, Snapdeal) and compare prices via a Streamlit UI.

Quick start

Recommended: use conda (easiest on Windows) — steps below. A venv works too but may require extra native build tooling for some packages.

Using conda (recommended)

1. Create and activate the environment (only once):

```powershell
conda create -n product-agg python=3.11 -y
conda activate product-agg
```

2. Install pyarrow (prebuilt) and runtime packages:

```powershell
conda install -c conda-forge pyarrow -y
python -m pip install --upgrade pip
python -m pip install streamlit pandas requests beautifulsoup4 lxml selenium undetected-chromedriver
```

3. Run the Streamlit UI from the repository root:

```powershell
python -m streamlit run product-aggregator\ui\app.py
```

Using venv (alternate)

1. Create and activate venv (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install runtime packages (may fail to build pyarrow on Windows — use conda if you see build errors):

```powershell
python -m pip install --upgrade pip
python -m pip install streamlit pandas requests beautifulsoup4 lxml selenium undetected-chromedriver
```

Run a smoke scraper (Amazon is requests-based and lighter):

```powershell
python product-aggregator\scrapers\test_amazon.py
```

Run the UI:

```powershell
streamlit run product-aggregator\ui\app.py
```

Notes
- The project includes Selenium-based scrapers that require Chrome and `undetected_chromedriver`.
- `core/aggregator.py` provides `fetch_combined(query, max_per_site, sources, headless)` which the UI calls. The aggregator is defensive: if a site scraper fails it will continue with others.

Small troubleshooting
- If you see errors importing modules when running the Streamlit app, ensure you run Streamlit from the repository root. The UI adds the `product-aggregator` folder to `sys.path` so imports work, but working-directory mismatches can still occur.
- If Streamlit install fails on Windows with pyarrow build errors, prefer the conda steps above to install `pyarrow` from conda-forge.

Contribution guide (short)
- Implement missing persistence in `database/db_helper.py` (suggested SQLite API).
- Add unit tests for `core/aggregator.py` (pytest) and mock scrapers to avoid network.
- Improve normalization and add more fields (brand, availability, discount).
- Add CI config to run linters and tests on PRs.

Quick diagnostics
-----------------
If you run into Selenium/Chrome errors (SessionNotCreatedException), run the diagnostic script to verify undetected_chromedriver can start a headless Chrome:

```powershell
conda activate product-agg  # or activate your venv
python product-aggregator\tools\uc_smoke.py
```

Inspect saved snapshots (after running aggregator with persistence enabled):

```powershell
python product-aggregator\tools\inspect_snapshots.py --query "your-query"
```


Contact
Raise issues or PRs in the repository.
