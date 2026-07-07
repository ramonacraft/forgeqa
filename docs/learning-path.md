# ForgeQA — Build Phases

Implementation roadmap from Phase 1 through RAG, execution, and enterprise hardening.

## Phase 1 — Generation + review ✅

**You can do this today.**

1. Set up local dev ([dev-setup.md](dev-setup.md))
2. Run the dashboard, connect LM Studio
3. Generate a Playwright test from a plain-English goal
4. Review output, save to `generated_tests/`

**Lesson 1 — Feel the context gap**

| Step | Action |
|------|--------|
| A | Generate a test with **empty** context |
| B | Generate the same goal with **selectors + test data** pasted in context |
| C | Compare outputs — notice invented locators vs reused patterns |

That gap is what Phase 2 RAG closes automatically.

## Phase 2 — RAG context (next)

See [rag-phase2-plan.md](rag-phase2-plan.md) for technical detail.

**Slice 1 — Local test retrieval**

1. Add `forgeqa/retrieval/` module
2. Index `examples/` into a local vector store
3. Add `retrieve` LangGraph node before `generate`
4. Dashboard toggle + show retrieved snippets

**Demo win:** Goal *"locked-out user login"* pulls saucedemo selectors without manual paste.

**Slice 2 — Expand sources**

- Jira/Confluence static exports
- Configurable index path for customer repos

**Slice 3 — Integrations**

- TestMCP output as retrieval query input
- Live Jira/Confluence APIs (optional)

## Phase 3 — Execution + self-healing

Run generated tests in-container, feed failures back for a fix attempt. Gated behind an explicit toggle.

## Phase 4 — Audit trail

Persist each run with timestamps; human approve/reject as a graph node.

## Phase 5 — TypeScript + deploy hardening

TypeScript output option, K8s / air-gapped deployment patterns.

## Suggested session rhythm

1. **One concept** — understand before coding
2. **One small build** — mergeable slice, not a mega-feature
3. **One demo** — prove it works end-to-end
4. **Document** — update docs if setup or behavior changed

## Key files to know

| File | Purpose |
|------|---------|
| `app/dashboard.py` | Streamlit UI |
| `forgeqa/agents/test_generator.py` | LangGraph pipeline |
| `forgeqa/agents/prompts.py` | System prompt + context assembly |
| `forgeqa/llm.py` | LiteLLM gateway (local-first) |
| `forgeqa/config.py` | Environment-driven settings |
| `examples/test_saucedemo_login.py` | Gold-standard output style |
