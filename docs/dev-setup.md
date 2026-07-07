# ForgeQA — Local Dev Setup

Quick reference for running ForgeQA on your Mac with LM Studio. For architecture and phases, see [FORGEQA_ARCHITECTURE.md](../FORGEQA_ARCHITECTURE.md).

## Prerequisites

- Python 3.9+ (3.11+ recommended)
- [LM Studio](https://lmstudio.ai) with a capable instruct model (e.g. Qwen 2.5 7B)
- Git

## First-time setup

```bash
cd forgeqa
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

## Two URLs — don't mix them up

| URL | What it is | Open in browser? |
|-----|------------|------------------|
| `http://localhost:1234` | LM Studio **API** (the LLM backend) | No — ForgeQA talks to this in the background |
| `http://localhost:8501` | **ForgeQA dashboard** (Streamlit UI) | Yes — this is your app |

## LM Studio checklist

1. Load a model (e.g. `qwen2.5-7b-instruct`).
2. Open the **Developer** / **Local Server** tab in the left sidebar.
3. Select the loaded model.
4. Click **Start Server** — status should show **Running** on port **1234**.
5. Leave LM Studio open while using ForgeQA.

**Note:** Visiting `http://127.0.0.1:1234` in a browser may log `Unexpected endpoint or method (GET /)`. That is normal — the API is not a website.

Verify the API (optional):

```bash
curl http://localhost:1234/v1/models
```

You should see JSON listing your model.

## Run the dashboard

```bash
source .venv/bin/activate
streamlit run app/dashboard.py
```

Open **http://localhost:8501**.

On first Streamlit run, you may be prompted for an email — press **Enter** to skip.

While Streamlit is running, the terminal will not return to a prompt. That is expected. Press `Ctrl+C` to stop.

## Sidebar sanity check

When the dashboard loads, the sidebar should show:

- **Mode:** `lmstudio`
- **Model:** `qwen2.5-7b-instruct` (or your configured model)
- **Endpoint:** `http://localhost:1234/v1`

## Common issues

### Broken virtual environment (`No module named 'blinker'`, `pydantic`, `requests`, etc.)

If multiple packages fail to import even after `pip install`, the venv may be corrupted (metadata without actual files). Rebuild it:

```bash
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### `Local LLM at ... is unreachable`

- Confirm LM Studio server is **Running**.
- Confirm `.env` has `LLM_MODE=lmstudio`.
- Confirm model identifier in LM Studio matches `LMSTUDIO_MODEL` in `.env`.

### Terminal stuck on `dquote>`

An unclosed `"` in a command (often `git commit -m "..."`). Press `Ctrl+C` and re-run the command with matching quotes on one line.

### `NotOpenSSLWarning` from urllib3

Harmless on macOS with the system Python/LibreSSL stack. Safe to ignore for local dev.

## Run tests

```bash
pytest tests/
```

Smoke tests mock the LLM — no network or LM Studio required.

## Docker (alternative to LM Studio)

```bash
cp .env.example .env
docker compose up --build
```

Dashboard at http://localhost:8501. Uses Ollama inside Docker instead of LM Studio.
