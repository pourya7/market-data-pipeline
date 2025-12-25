# Dashboard & Components

Purpose
- A small web UI for visualizing stored market data, inspecting manifests, and downloading processed datasets.

Where the dashboard code lives
- `src/market_data/dashboard`
- Key files: `app.py`, `components/charts.py`, `components/status.py`, `pages/charts.py`, `pages/download.py`, `pages/health.py`.

Responsibilities
- `app.py`: initializes the web application, routes, and any app-level configuration (port, data paths).
- `components/charts.py`: chart components that read Parquet data and render interactive charts (likely using a framework like Plotly or Altair).
- `components/status.py`: small UI for manifest and storage health checks.
- `pages/*`: route handlers and page-level composition (charts page, download page, health check page).

Data flow in the dashboard
1. User requests a chart or download via the UI.
2. The dashboard consults the manifest (via storage helpers) to find relevant Parquet files.
3. It reads a subset of Parquet data into memory, prepares it (filtering, downsampling), and passes it to the chart component for rendering.
4. For downloads, the dashboard streams the requested Parquet/CSV file to the user.

Best practices and considerations
- Keep dashboard reads efficient: use the manifest to avoid scanning, and only read the partitions needed for the requested time range/symbol.
- Consider caching frequently-requested datasets or precomputing aggregated views for the UI.
- Sanitize inputs (symbol names, date ranges) to avoid exposing the file-system or large scans.

Running locally (conceptual)

```bash
# run with the project's Python env
python -m src.market_data.dashboard.app
# then open http://localhost:8000
```

Testing
- UI tests may be minimal; prefer integration tests that assert endpoints return data (see `tests/` for any dashboard-related tests).

Where to read next
- `src/market_data/dashboard/app.py` — app entrypoint and routing.
- `src/market_data/dashboard/components/charts.py` — chart construction and data preparation.
- `src/market_data/storage/manager.py` — how the dashboard locates data via the manifest.

Next: shall I add `docs/11-models.md` (models & schemas) or `docs/12-testing.md` (tests & CI)?
