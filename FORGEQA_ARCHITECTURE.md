# ForgeQA — Architecture & Build Spec (for Cursor)

This document is a build brief. Point Cursor's agent at it to scaffold the project in the `cursorcraft` repo. It describes the target architecture, the exact file tree, what each file does, the interfaces between components, and phased acceptance criteria. Build Phase 1 first and stop for review before Phase 2.

## 1. What we're building

ForgeQA is a self-hosted AI QA platform. Governed AI agents turn a plain-English goal (plus optional Jira/codebase context) into clean, reviewable **Playwright Python** test code. Everything runs in the user's own infrastructure with local LLMs. The agent only writes code during generation — it never drives a browser or touches the app under test. Execution is a later, opt-in phase.

Core principles that constrain every design choice:

- **Local-first.** Default model runs on the user's machine (LM Studio in dev, Ollama in Docker for deploy). No data leaves the environment unless a cloud fallback is explicitly enabled.
- **Ownable output.** The product emits code the user reviews and commits, not black-box test runs.
- **Governed & auditable.** Generation is an explicit state machine (LangGraph), so every step is a named, inspectable node rather than a hidden prompt chain.
- **Simple.** One command to run in dev, one command to deploy.

## 2. Stack (do not substitute without flagging)

| Concern | Choice | Why |
|---------|--------|-----|
| Language | Python 3.11+ | Core agents, backend, orchestration |
| Agent orchestration | LangGraph | Explicit, auditable node graph; grows into approval/self-healing nodes |
| LLM gateway | LiteLLM | One call signature for LM Studio, Ollama, and cloud fallback |
| Local model (dev) | LM Studio, OpenAI-compatible at `http://localhost:1234/v1` | Ramona's dev setup (Qwen 7B) |
| Local model (deploy) | Ollama, OpenAI-compatible at `http://ollama:11434/v1` | One-command Docker for customers |
| Test output target | Playwright **Python** (pytest-playwright) | Readable API, web-first assertions, role locators map to plain English |
| UI | Streamlit | Fast dashboard, pure Python |
| Config | pydantic-settings + `.env` | Switch model with one env var, no code change |
| Deploy | Docker Compose | Kubernetes / air-gapped later |

No Selenium. TypeScript output is a later phase, not now.

## 3. Architecture

```
User → Streamlit UI → LangGraph Agent (generate → validate) → LiteLLM → Local LLM
                                                                   ↓
                          Clean Playwright test file → Review → Commit
```

The key simplification: LM Studio and Ollama both expose the **same OpenAI-compatible API**. The app talks to one abstract endpoint. A single env var (`LLM_MODE`) selects which. That is why dev and deploy share one code path.

## 4. File tree (build exactly this)

```
forgeqa/
├── forgeqa/                     # Core package
│   ├── __init__.py
│   ├── config.py                # env-driven settings; single source of truth
│   ├── llm.py                   # LiteLLM wrapper: local-first, cloud fallback
│   └── agents/
│       ├── __init__.py
│       ├── prompts.py           # system prompt + user-prompt builder
│       └── test_generator.py    # LangGraph graph: generate → validate
├── app/
│   └── dashboard.py             # Streamlit UI
├── examples/
│   └── test_saucedemo_login.py  # hand-written reference test (the gold standard)
├── generated_tests/
│   └── .gitkeep                 # output folder for saved tests
├── tests/
│   └── test_agent_smoke.py      # unit test: graph runs with a mocked LLM
├── docker-compose.yml           # Ollama + model-init + app
├── Dockerfile                   # Playwright Python base image
├── Makefile                     # setup / run / example / compose shortcuts
├── requirements.txt
├── .env.example
├── .gitignore
├── .cursorrules                 # coding conventions for the agent (see §9)
└── README.md
```

## 5. Component contracts

### `forgeqa/config.py`
A pydantic-settings `Settings` class loaded from `.env`. Exposes computed properties so the rest of the app never branches on mode:

- Fields: `llm_mode` ("lmstudio" | "ollama"), plus `lmstudio_*`, `ollama_*`, `cloud_*` groups, `llm_temperature`, `llm_timeout_seconds`.
- Properties: `active_base_url`, `active_model`, `active_api_key` — return the LM Studio or Ollama values based on `llm_mode`.
- Export a module-level singleton `settings = Settings()`.

### `forgeqa/llm.py`
- `complete(messages: list[dict]) -> str` is the only public function.
- Internally: `_local_completion` calls `litellm.completion(model=f"openai/{settings.active_model}", api_base=settings.active_base_url, api_key=settings.active_api_key, ...)`.
- On any local exception: if `cloud_fallback_enabled` and `cloud_model` set, call `_cloud_completion`; otherwise raise a clear `RuntimeError` telling the user their local model server is unreachable. Never fail silently to cloud.
- Set `litellm.drop_params = True` and `litellm.suppress_debug_info = True`.

### `forgeqa/agents/prompts.py`
- `SYSTEM_PROMPT`: instructs the model to produce pytest-style Playwright Python using `expect()` web-first assertions, role/label locators (`get_by_role`, `get_by_label`, `get_by_placeholder`), **no** `time.sleep`/`wait_for_timeout`, one `test_<behavior>` function per scenario with a plain-English docstring, `BASE_URL = "REPLACE_ME"` when no URL given, and a `# TODO: verify selector` comment on any invented selector. Output raw Python only, no markdown fences, no prose.
- `build_user_prompt(goal, context, base_url) -> str`: assembles the user turn from the three inputs, omitting empty sections.

### `forgeqa/agents/test_generator.py`
- `GenState(TypedDict)`: `goal, context, base_url, raw_output, code, is_valid, validation_error`. This dict is also the audit record for a run.
- `generate_node(state)`: builds messages from prompts, calls `complete()`, stores `raw_output`.
- `validate_node(state)`: strips accidental ```` ```python ```` fences via regex, then `ast.parse()` the code as a deterministic syntax gate. Sets `is_valid` / `validation_error`.
- `build_graph()`: `StateGraph(GenState)` with edges `START → generate → validate → END`; return `.compile()`.
- Compile once at import as `_AGENT`. Public API: `generate_test(goal, context="", base_url="") -> GenState`.
- Design intent: approval gates and self-healing become **new nodes** in this same graph later. Keep nodes small and pure.

### `app/dashboard.py`
- Streamlit page. Sidebar shows active mode/model/endpoint (transparency).
- Two columns: inputs (goal textarea, context textarea, base_url text input defaulting to `https://www.saucedemo.com`, Generate button) and output (validation banner, `st.code(..., language="python")`, filename input, "Save to generated_tests/" button).
- Persist the last result in `st.session_state` so the Save button survives Streamlit reruns.
- Catch `RuntimeError` from the agent and show it as `st.error` (this is the "local model not running" case).
- Insert `sys.path` for the repo root so `import forgeqa...` works when run via `streamlit run`.

### `examples/test_saucedemo_login.py`
Hand-written reference against `https://www.saucedemo.com`: `test_valid_login_shows_products` and `test_locked_out_user_sees_error`. Uses `get_by_placeholder`, `get_by_role`, `expect()`, no sleeps. This is the style the agent imitates and doubles as a smoke test.

### `tests/test_agent_smoke.py`
Monkeypatch `test_generator.complete` to return canned code (including a fenced variant) and assert: fences are stripped, valid code → `is_valid True`, broken code → `is_valid False` with an error. No network, no LLM.

## 6. Configuration (`.env.example`)

```
LLM_MODE=lmstudio

LMSTUDIO_BASE_URL=http://localhost:1234/v1
LMSTUDIO_MODEL=qwen2.5-7b-instruct
LMSTUDIO_API_KEY=lm-studio

OLLAMA_BASE_URL=http://ollama:11434/v1
OLLAMA_MODEL=qwen2.5:7b-instruct
OLLAMA_API_KEY=ollama

CLOUD_FALLBACK_ENABLED=false
CLOUD_MODEL=
CLOUD_API_KEY=

LLM_TEMPERATURE=0.1
LLM_TIMEOUT_SECONDS=120
```

## 7. Deployment

`docker-compose.yml` has three services:
1. `ollama` (ollama/ollama, port 11434, named volume, healthcheck `ollama list`).
2. `model-init` (one-shot `ollama pull qwen2.5:7b-instruct`, `depends_on ollama healthy`, `restart: no`).
3. `app` (builds Dockerfile, port 8501, env `LLM_MODE=ollama` + Ollama URL/model, `depends_on ollama healthy`).

`Dockerfile` uses `mcr.microsoft.com/playwright/python:v1.45.0-jammy` so Playwright browsers ship in the image for the later execution phase. Installs `requirements.txt`, copies source, runs Streamlit on `0.0.0.0:8501`.

## 8. Build phases & acceptance criteria

**Phase 1 — Generation + review (build this now).**
- `pip install -r requirements.txt` succeeds; every `.py` compiles.
- `pytest tests/test_agent_smoke.py` passes with a mocked LLM (no network).
- `pytest examples/ --collect-only` collects 2 tests.
- With LM Studio running, `streamlit run app/dashboard.py` generates code from a goal and saves it. With LM Studio **off**, the UI shows a clear "local model unreachable" error, not a stack trace.
- Stop here for review.

**Phase 2 — RAG context.** Add a `retrieval/` module that indexes a repo/Jira export and injects relevant selectors/page objects into the user prompt. New optional graph node before `generate`.

**Phase 3 — Optional execution + self-healing.** New nodes: `execute` (run the generated test in-container against a target URL) and `heal` (feed failures back for a fix attempt). Gated behind an explicit toggle.

**Phase 4 — Audit trail + approval gates.** Persist each `GenState` run with timestamps and a human approve/reject step as a graph node.

**Phase 5 — TypeScript output + K8s / air-gapped.**

## 9. `.cursorrules` (conventions for the agent)

- Python 3.11+, type hints on public functions, `from __future__ import annotations`.
- No `time.sleep` anywhere in generated or example tests; Playwright auto-waiting only.
- Keep LangGraph nodes small and pure; state flows through `GenState`.
- Never introduce a cloud LLM call that runs by default — local-first is a hard requirement.
- No Selenium. No secrets committed. `.env` is git-ignored; only `.env.example` is tracked.
- Prefer role/label Playwright locators over CSS/id.

## 10. First Cursor prompt (paste into the agent)

> Read `FORGEQA_ARCHITECTURE.md`. Scaffold the full file tree from section 4. Implement Phase 1 only (sections 5–6, 8). Follow `.cursorrules`. After creating files, run `pip install -r requirements.txt`, then `pytest tests/`, and confirm every module compiles. Do not implement Phases 2–5. Stop and summarize what you built and how to run it.
