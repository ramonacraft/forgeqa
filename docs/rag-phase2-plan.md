# ForgeQA — Phase 2 RAG Plan

**Goal:** Automatically inject relevant selectors, page objects, and test patterns into the generation prompt — so users don't have to paste context by hand.

Pairs with [TestMCP](https://github.com/ramonacraft/testmcp): TestMCP predicts *what* to test from a PR; ForgeQA generates *how* to test it with real app knowledge.

## What RAG adds

| Today (Phase 1) | Phase 2 (RAG) |
|-----------------|---------------|
| User pastes context manually | ForgeQA retrieves context from indexed sources |
| LLM guesses selectors when context is empty | LLM reuses patterns from existing tests/docs |
| More `# TODO: verify selector` comments | Fewer invented locators |

**RAG** = Retrieval-Augmented Generation. Before the LLM writes code, ForgeQA searches indexed project knowledge and prepends the best-matching chunks to the prompt.

## Current pipeline (Phase 1)

```
START → generate → validate → END
```

Context enters via `build_user_prompt()` in `forgeqa/agents/prompts.py` — only if the user typed it in the dashboard.

## Target pipeline (Phase 2)

```
START → retrieve → generate → validate → END
              ↑ optional when RAG_ENABLED=true
```

The `retrieve` node enriches `state["context"]` before `generate` runs.

## Proposed module layout

```
forgeqa/retrieval/
├── __init__.py
├── indexer.py      # Walk a folder, chunk .py / .md files
├── store.py        # Local vector store (e.g. ChromaDB on disk)
└── retrieve.py     # Embed the goal, return top-k chunks
```

## Index sources (in order of implementation)

1. **Local Playwright tests** — `examples/`, `generated_tests/`, or a configurable repo path *(start here)*
2. **Jira export** — static JSON/Markdown files before live API integration
3. **Confluence export** — same pattern as Jira
4. **Live Jira/Confluence APIs** — defer until static exports prove the loop

## Config additions (`.env.example`)

```env
RAG_ENABLED=false
RAG_INDEX_PATH=./examples
RAG_TOP_K=5
RAG_PERSIST_DIR=./.forgeqa_index
RAG_EMBEDDING_MODEL=nomic-embed-text   # via Ollama / LM Studio embedding endpoint
```

## Dashboard changes

- Toggle: **Use RAG** (or auto-on when `RAG_ENABLED=true`)
- Optional: **Index path** override
- Show retrieved snippets before generation (audit trail — reviewer sees what the model received)

## Dependencies to add

- `chromadb` (or similar) for local vector persistence
- Embedding model via Ollama/LM Studio to stay local-first

## Acceptance criteria

- [ ] With `examples/` indexed, goal *"locked-out user sees error on login"* retrieves `test_locked_out_user_sees_error` patterns without manual paste
- [ ] `RAG_ENABLED=false` → behavior identical to Phase 1
- [ ] `pytest tests/` still passes (mock retrieval in smoke tests)
- [ ] Retrieved context visible in UI or logged for review

## What good context looks like

High-value chunks for test generation:

```
Username: get_by_placeholder("Username")
Password: get_by_placeholder("Password")
Login button: get_by_role("button", name="Login")
Locked-out user: locked_out_user / secret_sauce
Expected: error message containing "locked out"
```

User stories alone (*"user can unlock their account"*) are useful but insufficient without selectors and test data.

## Out of scope for Phase 2 v1

- TestMCP PR integration (pipe risk-ranked cases into the retrieval query)
- Full monorepo indexing with smart chunking
- Cloud embedding providers by default

## References

- Architecture brief: [FORGEQA_ARCHITECTURE.md](../FORGEQA_ARCHITECTURE.md) — Section 8, Phase 2
- Gold-standard test style: [examples/test_saucedemo_login.py](../examples/test_saucedemo_login.py)
- Learning curriculum: [docs/learning-path.md](learning-path.md)
