"""ForgeQA dashboard. Enter a goal, review generated Playwright code, save it.

Run with:  streamlit run app/dashboard.py

This is deliberately a "human in the loop" screen. The agent proposes code; you
review it and decide whether to keep it. Nothing runs against your app here.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import streamlit as st

# Make the forgeqa package importable when Streamlit runs this file directly.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from forgeqa.agents.test_generator import generate_test  # noqa: E402
from forgeqa.config import settings  # noqa: E402

GENERATED_DIR = ROOT / "generated_tests"
GENERATED_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="ForgeQA", page_icon="🔨", layout="wide")

st.title("🔨 ForgeQA")
st.caption("Governed AI test generation. Local model, reviewable code, your infra.")

# --- Sidebar: show what backend we're talking to (transparency) ---
with st.sidebar:
    st.subheader("Model")
    st.write(f"**Mode:** `{settings.llm_mode}`")
    st.write(f"**Model:** `{settings.active_model}`")
    st.write(f"**Endpoint:** `{settings.active_base_url}`")
    st.info("Nothing leaves this machine unless cloud fallback is explicitly enabled.")

# --- Inputs ---
col_in, col_out = st.columns(2)

with col_in:
    st.subheader("What do you want to test?")
    goal = st.text_area(
        "Goal / scenario",
        placeholder="Log in with a valid user and confirm the products page loads.",
        height=120,
    )
    context = st.text_area(
        "Context (optional): app details, selectors, user story, Jira ticket",
        placeholder="Username field id=user-name, password id=password, login button id=login-button. "
        "Valid creds: standard_user / secret_sauce.",
        height=140,
    )
    base_url = st.text_input(
        "Base URL of the app under test (optional)",
        value="https://www.saucedemo.com",
    )
    generate = st.button("Generate test", type="primary", use_container_width=True)

with col_out:
    st.subheader("Generated Playwright test")

    if generate:
        if not goal.strip():
            st.warning("Give it a goal first.")
        else:
            with st.spinner("Agent is writing the test..."):
                try:
                    result = generate_test(goal=goal, context=context, base_url=base_url)
                except RuntimeError as err:
                    st.error(str(err))
                    result = None

            if result:
                # Store in session so the Save button survives a rerun.
                st.session_state["last_result"] = result

    result = st.session_state.get("last_result")
    if result:
        if result["is_valid"]:
            st.success("Code parses cleanly. Review it before you keep it.")
        else:
            st.error(f"Generated code has a syntax issue: {result['validation_error']}")

        st.code(result["code"], language="python")

        default_name = f"test_{datetime.now():%Y%m%d_%H%M%S}.py"
        fname = st.text_input("Save as", value=default_name)
        if st.button("Save to generated_tests/", use_container_width=True):
            out_path = GENERATED_DIR / fname
            out_path.write_text(result["code"], encoding="utf-8")
            st.success(f"Saved to {out_path}")
    else:
        st.info("Your generated test will appear here.")
