"""The test-generation agent, built as a small LangGraph.

Why LangGraph for something this simple? Because it gives us an explicit,
inspectable state machine we grow later. Today it's two nodes:

    generate  ->  validate

`generate` asks the LLM for code. `validate` strips stray markdown and checks
the code actually parses as Python (a fast, deterministic quality gate before a
human ever sees it). When we add self-healing or an approval gate, they become
new nodes in this same graph. That's the governance story: every step is a
named, auditable node, not a hidden prompt chain.
"""

from __future__ import annotations

import ast
import re
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from forgeqa.agents.prompts import SYSTEM_PROMPT, build_user_prompt
from forgeqa.llm import complete


class GenState(TypedDict):
    """Everything that flows through the graph. Also our audit record."""

    goal: str
    context: str
    base_url: str
    raw_output: str          # what the model returned
    code: str                # cleaned code
    is_valid: bool           # did it parse as Python?
    validation_error: str    # why not, if invalid


def _strip_markdown_fences(text: str) -> str:
    """Models sometimes wrap code in ```python ... ``` despite instructions."""
    fenced = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    return fenced.group(1).strip() if fenced else text.strip()


def generate_node(state: GenState) -> GenState:
    """Call the LLM and capture the raw output."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(
            state["goal"], state["context"], state["base_url"]
        )},
    ]
    state["raw_output"] = complete(messages)
    return state


def validate_node(state: GenState) -> GenState:
    """Clean the output and confirm it parses. Deterministic quality gate."""
    code = _strip_markdown_fences(state["raw_output"])
    state["code"] = code
    try:
        ast.parse(code)
        state["is_valid"] = True
        state["validation_error"] = ""
    except SyntaxError as err:
        state["is_valid"] = False
        state["validation_error"] = f"{err.msg} (line {err.lineno})"
    return state


def build_graph():
    """Wire the nodes. Compiled once, reused per request."""
    graph = StateGraph(GenState)
    graph.add_node("generate", generate_node)
    graph.add_node("validate", validate_node)
    graph.add_edge(START, "generate")
    graph.add_edge("generate", "validate")
    graph.add_edge("validate", END)
    return graph.compile()


# Compile at import so the UI doesn't rebuild it on every click.
_AGENT = build_graph()


def generate_test(goal: str, context: str = "", base_url: str = "") -> GenState:
    """Public API. Give it a goal, get back code + validation result."""
    initial: GenState = {
        "goal": goal,
        "context": context,
        "base_url": base_url,
        "raw_output": "",
        "code": "",
        "is_valid": False,
        "validation_error": "",
    }
    return _AGENT.invoke(initial)
