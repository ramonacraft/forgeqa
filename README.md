# ForgeQA

**Self-hosted AI QA tool.** A LangGraph agent turns a plain-English test goal into clean, reviewable **Playwright Python** test code, using a local LLM (LM Studio for dev, Ollama in Docker for deploy). Nothing leaves your machine unless you explicitly enable cloud fallback.

**Architecture (shareable):** [ramonacraft.github.io/forgeqa](https://ramonacraft.github.io/forgeqa)

**Pairs with [TestMCP](https://github.com/ramonacraft/testmcp)** — TestMCP predicts *what* to test from a GitHub PR; ForgeQA generates *how* to test it in Playwright.

## What it does today (Phase 1)

- Enter a goal → receive Playwright Python test code
- LangGraph pipeline: **generate** → **validate** (syntax gate before you see output)
- Streamlit dashboard to review and save tests
- Local-first LLMs via LiteLLM (LM Studio or Ollama, one env var switch)

## Quick start (dev)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

1. Start **LM Studio**, load a capable model (e.g. Qwen 2.5 7B), click **Start Server** (port 1234).
2. Run the dashboard:

```bash
streamlit run app/dashboard.py
```

Open http://localhost:8501

## Quick start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

Dashboard at http://localhost:8501. First boot pulls the Ollama model automatically.

## Run tests

```bash
pytest tests/
```

## Docs

| Guide | Purpose |
|-------|---------|
| [docs/dev-setup.md](docs/dev-setup.md) | Local setup, LM Studio, troubleshooting |
| [docs/learning-path.md](docs/learning-path.md) | Build phases roadmap |
| [docs/rag-phase2-plan.md](docs/rag-phase2-plan.md) | RAG implementation plan |
| [FORGEQA_ARCHITECTURE.md](FORGEQA_ARCHITECTURE.md) | Full build brief |

## Layout

```
forgeqa/          Core package (config, LLM, LangGraph agent)
app/              Streamlit dashboard
docs/             GitHub Pages + guides
examples/         Hand-written reference tests
generated_tests/  Saved output from the UI
tests/            Smoke tests (no network)
```

## Roadmap

1. Test generation + review *(current)*
2. RAG over private repos / Jira / Confluence
3. Optional execution + self-healing
4. TypeScript output option

## License

MIT — Ramona Bonitatis
