# Contributing

Thanks for your interest!

Short checklist to get started as a contributor:

- Setup (recommended): use the `product-agg` conda env (see README.md). This avoids building heavy native deps on Windows.
- Run unit tests locally:

```powershell
conda activate product-agg
python -m pip install -r product-aggregator\requirements-test.txt
python -m pytest -q product-aggregator\tests
```

- Make small, focused PRs. Prefer tests for any new behaviour (pytest).
- Avoid running Selenium-based scrapers in CI; mock them in tests. The repository contains `tools/uc_smoke.py` to manually verify Chrome driver startup locally.
- Use the existing coding style in the repo. Keep changes minimal and document any public API changes (e.g., `core.fetch_combined` parameters).

If you'd like, open an issue describing what you want to work on and tag it `good-first-issue` to help others pick it up.

Thanks — maintainers
