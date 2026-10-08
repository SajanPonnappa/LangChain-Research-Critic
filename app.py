import html
import re
import time
from datetime import date

import streamlit as st

from src.agents.agents import build_search_agent, build_reader_agent, writer_chain, critic_chain

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="The Research Critic",
    page_icon="🖋️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles (colours live in .streamlit/config.toml) ──────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,700;0,9..144,800;1,9..144,400&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --ink: #1F1B16;
    --muted: #6B6155;
    --rule: #CFC4B0;
    --pen: #B4232A;
}

html, body, .stApp, .stMarkdown, button, input, textarea {
    font-family: 'IBM Plex Sans', sans-serif;
}
h1, h2, h3, h4 { font-family: 'Fraunces', serif !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { max-width: 1100px; padding-top: 2rem; }

/* ── Masthead ── */
.masthead { text-align: center; margin-bottom: 1.8rem; }
.masthead h1 {
    font-size: clamp(2.4rem, 5vw, 3.8rem);
    font-weight: 800;
    letter-spacing: -0.02em;
    color: var(--ink);
    margin: 0;
    padding: 0.2rem 0 0.4rem;
}
.dateline {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 0.5rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: var(--muted);
    border-top: 1px solid var(--ink);
    border-bottom: 3px double var(--ink);
    padding: 0.45rem 0.2rem;
}

/* ── Small caps label ── */
.kicker {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--pen);
    margin-bottom: 0.3rem;
}

/* ── Desk (how-it-works) cards ── */
.desk-num {
    font-family: 'Fraunces', serif;
    font-size: 2.2rem;
    font-weight: 800;
    color: var(--pen);
    line-height: 1;
}
.desk-role { font-family: 'Fraunces', serif; font-size: 1.15rem; font-weight: 700; margin: 0.3rem 0; }
.desk-desc { font-size: 0.85rem; color: var(--muted); }

/* ── Verdict banner ── */
.score-card {
    border: 2px solid var(--score);
    border-radius: 6px;
    text-align: center;
    padding: 0.9rem 0.5rem 0.7rem;
    background: #FFFDF8;
}
.score-num {
    font-family: 'Fraunces', serif;
    font-size: 3.6rem;
    font-weight: 800;
    line-height: 1;
    color: var(--score);
}
.score-num small { font-size: 1.2rem; color: var(--muted); font-weight: 400; }
.verdict {
    font-family: 'Fraunces', serif;
    font-style: italic;
    font-size: 1.45rem;
    line-height: 1.4;
    border-left: 4px solid var(--pen);
    padding: 0.2rem 0 0.2rem 1rem;
    margin-top: 0.4rem;
}
.topic-line { color: var(--muted); font-size: 0.9rem; margin-top: 0.6rem; }

.colophon {
    text-align: center;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.1em;
    color: var(--muted);
    border-top: 1px solid var(--rule);
    margin-top: 3rem;
    padding-top: 1rem;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────
DESK = [
    ("1", "Scout", "Searches the web for recent, reliable sources."),
    ("2", "Reader", "Picks the best source and reads it in depth."),
    ("3", "Writer", "Drafts a structured research report."),
    ("4", "Critic", "Scores the report and gives a verdict."),
]

EXAMPLES = [
    "Future of LLMs in the tech industry",
    "Latest AI agent frameworks in 2026",
    "Roadmap for AGI development in the next 5 years",
]


def use_example(text: str):
    st.session_state.topic = text


def parse_score(critique: str):
    m = re.search(r"score\s*:?\s*\**\s*(\d+(?:\.\d+)?)\s*/\s*10", critique, re.I)
    return float(m.group(1)) if m else None


def parse_verdict(critique: str):
    m = re.search(r"verdict\s*:?\s*\**\s*(.+)", critique, re.I)
    return m.group(1).strip(" *") if m else None


def score_colour(score):
    if score is None:
        return "#6B6155"
    if score >= 8:
        return "#2F7D4A"
    if score >= 5:
        return "#B7791F"
    return "#B4232A"


def run_pipeline(topic: str) -> dict:
    results = {"topic": topic}

    with st.status(f"Working on: {topic}", expanded=True) as status:
        st.write("**1 · Scout** is searching the web…")
        search_agent = build_search_agent()
        sr = search_agent.invoke({
            "messages": [("user", f"Find recent, reliable and detailed information about: {topic}")]
        })
        results["search"] = sr["messages"][-1].content

        st.write("**2 · Reader** is reading the best source…")
        reader_agent = build_reader_agent()
        rr = reader_agent.invoke({
            "messages": [(
                "user",
                f"Based on the following search results about '{topic}', "
                f"pick the most relevant URL and scrape it for deeper content.\n\n"
                f"Search Results:\n{results['search'][:800]}"
            )]
        })
        results["reader"] = rr["messages"][-1].content

        st.write("**3 · Writer** is drafting the report…")
        research_combined = (
            f"SEARCH RESULTS:\n{results['search']}\n\n"
            f"DETAILED SCRAPED CONTENT:\n{results['reader']}"
        )
        results["writer"] = writer_chain.invoke({"topic": topic, "research": research_combined})

        st.write("**4 · Critic** is reviewing the report…")
        results["critic"] = critic_chain.invoke({"report": results["writer"]})

        status.update(label="Review complete", state="complete", expanded=False)

    return results


# ── Sidebar: the assignment ──────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="kicker">The assignment</div>', unsafe_allow_html=True)
    st.markdown("### What should we investigate?")

    topic = st.text_area(
        "Research topic",
        key="topic",
        placeholder="e.g. How AI is changing healthcare diagnostics",
        height=110,
        label_visibility="collapsed",
    )
    run_clicked = st.button("🖋️ Commission report", type="primary", width="stretch")

    st.markdown('<div class="kicker" style="margin-top:1.5rem">Story ideas</div>', unsafe_allow_html=True)
    for ex in EXAMPLES:
        st.button(ex, on_click=use_example, args=(ex,), width="stretch")


# ── Masthead ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="masthead">
    <h1>The Research Critic</h1>
    <div class="dateline">
        <span>{date.today():%A, %d %B %Y}</span>
        <span>Four agents · One verdict</span>
        <span>LangChain edition</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Run ──────────────────────────────────────────────────────────────────────
if run_clicked:
    if not topic.strip():
        st.warning("Write a topic in the sidebar first.")
    else:
        try:
            st.session_state.results = run_pipeline(topic.strip())
        except Exception as e:
            st.error(f"The pipeline stopped: {e}")


# ── Results / empty state ────────────────────────────────────────────────────
r = st.session_state.get("results")

if not r:
    st.markdown('<div class="kicker">Meet the desk</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    for col, (num, role, desc) in zip(cols, DESK):
        with col, st.container(border=True):
            st.markdown(
                f'<div class="desk-num">{num}</div>'
                f'<div class="desk-role">{role}</div>'
                f'<div class="desk-desc">{desc}</div>',
                unsafe_allow_html=True,
            )
    st.info("Pick a story idea or write your own topic in the sidebar, then press **Commission report**.")

else:
    score = parse_score(r["critic"])
    verdict = parse_verdict(r["critic"]) or "See the critic's notes below."

    col_score, col_verdict = st.columns([1, 4], vertical_alignment="center")
    with col_score:
        score_text = f"{score:g}" if score is not None else "–"
        st.markdown(f"""
        <div class="score-card" style="--score:{score_colour(score)}">
            <div class="kicker" style="color:var(--muted)">Critic score</div>
            <div class="score-num">{score_text}<small>/10</small></div>
        </div>
        """, unsafe_allow_html=True)
    with col_verdict:
        st.markdown(f"""
        <div class="kicker">The verdict</div>
        <div class="verdict">“{html.escape(verdict)}”</div>
        <div class="topic-line">On: <b>{html.escape(r['topic'])}</b></div>
        """, unsafe_allow_html=True)

    st.write("")
    tab_report, tab_critic, tab_notes = st.tabs(["📰 Report", "🖋️ Critic's notes", "🔎 Research notes"])

    with tab_report:
        st.markdown(r["writer"])
        stamp = int(time.time())
        c1, c2 = st.columns(2)
        c1.download_button(
            "⬇ Download report (.md)",
            data=r["writer"],
            file_name=f"report_{stamp}.md",
            mime="text/markdown",
            width="stretch",
        )
        c2.download_button(
            "⬇ Download report + critique (.md)",
            data=f"{r['writer']}\n\n---\n\n# Critic's review\n\n{r['critic']}",
            file_name=f"report_with_critique_{stamp}.md",
            mime="text/markdown",
            width="stretch",
        )

    with tab_critic:
        st.markdown(r["critic"])

    with tab_notes:
        with st.expander("Scout — search results", expanded=True):
            st.markdown(r["search"])
        with st.expander("Reader — scraped content"):
            st.markdown(r["reader"])


# ── Colophon ─────────────────────────────────────────────────────────────────
st.markdown(
    '<div class="colophon">The Research Critic · LangChain agents on Groq · Built with Streamlit</div>',
    unsafe_allow_html=True,
)
