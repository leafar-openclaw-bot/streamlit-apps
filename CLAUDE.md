# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

A multi-app Streamlit portfolio hosted on Streamlit Cloud. Each app lives in `apps/{app-slug}/` and is deployed independently via git integration.

## Running Apps Locally

```bash
cd apps/{app-slug}
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Via Dev Container (preferred): the container automatically installs deps and starts Streamlit on port 8501 with CORS/XSRF disabled.

## App Structure

Each app follows this layout:

```
apps/{app-slug}/
├── .streamlit/config.toml    # Dark theme config
├── requirements.txt
└── streamlit_app.py          # Entire app in one file
```

## Registry

When adding or updating an app, update `.openclaw-registry.json` with the slug, URL, and description. The URL pattern is `https://{slug}.streamlit.app`.

## Code Patterns

**Session state:** Mutable data (e.g., guest lists) lives in `st.session_state` so edits survive Streamlit reruns.

**Layout:** Sidebar holds forms, filters, and controls. Main area holds visualizations and tables.

**Theme:** All apps use dark theme (`base = "dark"`) with blue primary (`#1E88E5`), defined in `.streamlit/config.toml`.

**Network graphs:** Use `networkx` to build the graph model and `pyvis` to render it; embed the resulting HTML via `st.html()`.

## Commit Style

```
feat(app-slug): description
fix(app-slug): description
chore: description
```
