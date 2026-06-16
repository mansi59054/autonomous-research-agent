"""
Streamlit UI for the Autonomous Research Agent.
Run with: streamlit run app.py
"""

import os
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🔬 Autonomous Research Agent")
st.caption("Powered by Claude — searches arXiv & Semantic Scholar, then writes a literature review.")

with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input(
        "Anthropic API Key",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        type="password",
        help="Get yours at console.anthropic.com",
    )
    model = st.selectbox(
        "Model",
        ["claude-sonnet-4-5", "claude-haiku-4-5", "claude-opus-4-5"],
        index=0,
    )
    max_iter = st.slider("Max tool-call rounds", min_value=5, max_value=20, value=12)
    st.divider()
    st.markdown("**Example topics:**")
    examples = [
        "quantum reservoir computing",
        "spiking neural networks for edge AI",
        "diffusion models for protein structure",
        "neuromorphic computing energy efficiency",
        "large language models reasoning",
    ]
    for ex in examples:
        if st.button(ex, use_container_width=True):
            st.session_state["topic_input"] = ex

topic = st.text_input(
    "Research topic",
    value=st.session_state.get("topic_input", ""),
    placeholder="e.g. quantum reservoir computing energy forecasting",
    key="topic_input",
)

run_btn = st.button("🚀 Run Agent", type="primary", disabled=not api_key or not topic)

if run_btn:
    from agent import run_agent

    progress_bar = st.progress(0, text="Starting agent...")
    status_area = st.empty()
    steps_container = st.expander("🔍 Agent steps (live)", expanded=True)
    steps_log = steps_container.empty()
    all_steps_html = []
    start_time = time.time()

    def on_step(step):
        icon_map = {
            "thinking": "🧠",
            "tool_call": "🔧",
            "tool_result": "📋",
        }
        icon = icon_map.get(step["type"], "•")
        if step["type"] == "thinking":
            snippet = step["text"][:120].replace("<", "&lt;").replace(">", "&gt;")
            html = f'<p>{icon} <b>Thinking</b> (iter {step["iteration"]}): <em>{snippet}...</em></p>'
        elif step["type"] == "tool_call":
            inp = str(step["input"])[:80]
            html = f'<p>{icon} <b>Tool call</b>: <code>{step["tool"]}</code> — {inp}</p>'
        else:
            summary = step["result_summary"].replace("<", "&lt;").replace(">", "&gt;")
            html = f'<p>{icon} <b>Result</b>: {summary}</p>'
        all_steps_html.append(html)
        steps_log.markdown("\n".join(all_steps_html), unsafe_allow_html=True)
        n = len([s for s in all_steps_html if "tool_call" in s])
        progress_bar.progress(
            min(0.9, len(all_steps_html) / (max_iter * 3)),
            text=f"Running… {len(all_steps_html)} steps so far"
        )

    with st.spinner("Agent is researching…"):
        result = run_agent(
            topic=topic,
            api_key=api_key,
            model=model,
            max_iterations=max_iter,
            on_step=on_step,
        )

    elapsed = time.time() - start_time
    progress_bar.progress(1.0, text=f"Done in {elapsed:.1f}s")

    if result["error"]:
        st.warning(f"⚠️ {result['error']}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Tool calls", result["tool_calls"])
    col2.metric("Agent steps", len(result["steps"]))
    col3.metric("Time elapsed", f"{elapsed:.1f}s")

    st.divider()
    st.subheader("📄 Literature Review")
    st.markdown(result["report"])

    st.download_button(
        label="⬇️ Download report (.md)",
        data=result["report"],
        file_name=f"literature_review_{topic[:40].replace(' ', '_')}.md",
        mime="text/markdown",
    )
