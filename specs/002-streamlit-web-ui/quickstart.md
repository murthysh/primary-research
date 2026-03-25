# Quickstart: Streamlit Web UI

**Branch**: `002-streamlit-web-ui` | **Date**: 2026-03-25

---

## Local Development

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure secrets

```bash
mkdir -p .streamlit
```

Create `.streamlit/secrets.toml`:
```toml
APP_PASSWORD = "your_team_password"
SERPAPI_KEY  = "your_serpapi_key"
```

> This file is gitignored. Never commit it.

### 3. Run the app

```bash
streamlit run streamlit_app.py
```

The app opens at `http://localhost:8501`. Enter your password to access the UI.

---

## Deploy to Streamlit Community Cloud

1. Push the branch to GitHub (merge to `main` first, or deploy directly from branch).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**.
4. Select your repo, branch (`main`), and set **Main file path** to `streamlit_app.py`.
5. Expand **Advanced settings → Secrets** and paste:
   ```
   APP_PASSWORD = "your_team_password"
   SERPAPI_KEY  = "your_serpapi_key"
   ```
6. Click **Deploy**.

Share the generated `https://<your-app>.streamlit.app` URL with your team.

---

## Validation Checklist

- [ ] Password gate blocks access with wrong password
- [ ] Password gate allows access with correct password
- [ ] Run with `--keyword "AI in healthcare"` returns records and shows download button
- [ ] `--type ebook` filter produces ebook-only results (or zero-results warning)
- [ ] Excel download opens correctly in Excel
- [ ] CSV download opens correctly in Excel (UTF-8 BOM preserved)
- [ ] Both formats selected → two download buttons appear
- [ ] Missing `SERPAPI_KEY` in secrets → error message shown, no traceback
- [ ] Empty keyword → Run button disabled
