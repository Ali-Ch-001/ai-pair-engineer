import streamlit as st
import plotly.graph_objects as go
from src.schemas import CodeReviewOutput, PairEngineerOutput, TokenUsage

# ═══════════════════════════════════════════════════════════════════
# Modern CSS System
# ═══════════════════════════════════════════════════════════════════
CSS = """
<style>
/* ── Imports & Root ───────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --bg-deep: #0B0F19;
    --bg-surface: #111827;
    --bg-elevated: #1A2332;
    --bg-card: rgba(26, 35, 50, 0.6);
    --border-subtle: rgba(255,255,255,0.06);
    --border-default: rgba(255,255,255,0.1);
    --border-glow: rgba(124,58,237,0.3);
    --text-primary: #E2E8F0;
    --text-secondary: #94A3B8;
    --text-muted: #64748B;
    --accent: #8B5CF6;
    --accent-glow: rgba(139,92,246,0.25);
    --success: #10B981;
    --success-bg: rgba(16,185,129,0.12);
    --danger: #EF4444;
    --danger-bg: rgba(239,68,68,0.12);
    --warning: #F59E0B;
    --warning-bg: rgba(245,158,11,0.12);
    --info: #3B82F6;
    --info-bg: rgba(59,130,246,0.12);
    --radius-sm: 6px;
    --radius-md: 10px;
    --radius-lg: 16px;
    --radius-xl: 20px;
    --shadow-card: 0 1px 3px rgba(0,0,0,0.4), 0 4px 16px rgba(0,0,0,0.3);
    --shadow-glow: 0 0 30px var(--accent-glow);
    --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
}

/* ── Global Overrides ─────────────────────────────────────────── */
.stApp {
    font-family: var(--font-sans);
    background: var(--bg-deep);
    background-image:
        radial-gradient(ellipse 80% 60% at 50% -10%, rgba(124,58,237,0.08), transparent),
        radial-gradient(ellipse 60% 50% at 100% 100%, rgba(59,130,246,0.05), transparent);
    background-attachment: fixed;
}

/* Smooth scrolling */
html { scroll-behavior: smooth; }

/* Better selection color */
::selection { background: rgba(139,92,246,0.35); color: #fff; }

/* Custom scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

/* ── Typography ───────────────────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
    font-family: var(--font-sans);
    letter-spacing: -0.02em;
}
h1 {
    background: linear-gradient(135deg, #C084FC, #818CF8, #38BDF8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-weight: 800;
    font-size: 2.2rem;
}
h3 { font-weight: 600; font-size: 1.15rem; color: var(--text-primary); }

/* ── Hero Section ─────────────────────────────────────────────── */
.hero {
    position: relative;
    padding: 1.5rem 0 1rem 0;
    margin-bottom: 0.5rem;
}
.hero-badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 14px; border-radius: 99px;
    background: rgba(139,92,246,0.12); border: 1px solid rgba(139,92,246,0.2);
    font-size: 0.78rem; font-weight: 500; color: #A78BFA;
    margin-bottom: 0.8rem;
    animation: fadeInUp 0.6s ease;
}
.hero-badge .dot {
    width: 6px; height: 6px; border-radius: 50%; background: #A78BFA;
    animation: pulse-dot 2s infinite;
}
.hero-subtitle {
    font-size: 0.95rem; color: var(--text-secondary);
    max-width: 600px; line-height: 1.5;
    animation: fadeInUp 0.6s ease 0.15s both;
}
.hero-stats {
    display: flex; gap: 1.5rem; margin-top: 1rem;
    animation: fadeInUp 0.6s ease 0.3s both;
}
.hero-stat {
    display: flex; align-items: center; gap: 0.5rem;
    font-size: 0.85rem; color: var(--text-secondary);
}
.hero-stat strong { color: var(--text-primary); font-weight: 600; }
.hero-stat .icon { font-size: 1.1rem; }

/* ── Glass Card ───────────────────────────────────────────────── */
.glass-card {
    background: var(--bg-card);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-md);
    padding: 1.2rem;
    box-shadow: var(--shadow-card);
    transition: border-color 0.3s ease, box-shadow 0.3s ease;
}
.glass-card:hover {
    border-color: rgba(139,92,246,0.25);
    box-shadow: 0 1px 3px rgba(0,0,0,0.4), 0 8px 24px rgba(0,0,0,0.3);
}

/* ── Score Badges ─────────────────────────────────────────────── */
.score-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.4rem 1.2rem; border-radius: 99px;
    font-weight: 700; font-size: 1.05rem;
    letter-spacing: -0.01em;
}
.score-high {
    background: rgba(16,185,129,0.15);
    border: 1px solid rgba(16,185,129,0.3);
    color: #6EE7B7;
}
.score-mid {
    background: rgba(245,158,11,0.15);
    border: 1px solid rgba(245,158,11,0.3);
    color: #FCD34D;
}
.score-low {
    background: rgba(239,68,68,0.15);
    border: 1px solid rgba(239,68,68,0.3);
    color: #FCA5A5;
}

/* ── Severity Pills ───────────────────────────────────────────── */
.sev-badge {
    display: inline-block;
    padding: 2px 10px; border-radius: 99px;
    font-weight: 600; font-size: 0.68rem;
    text-transform: uppercase; letter-spacing: 0.04em;
}
.sev-high   { background: rgba(239,68,68,0.18); color: #FCA5A5; border: 1px solid rgba(239,68,68,0.3); }
.sev-medium { background: rgba(245,158,11,0.18); color: #FDE68A; border: 1px solid rgba(245,158,11,0.3); }
.sev-low    { background: rgba(16,185,129,0.18); color: #6EE7B7; border: 1px solid rgba(16,185,129,0.3); }

/* ── Dimension Bars ───────────────────────────────────────────── */
.dim-row {
    display: flex; align-items: center; gap: 0.6rem;
    padding: 0.35rem 0; font-size: 0.82rem;
}
.dim-label {
    width: 110px; font-weight: 500; color: var(--text-secondary);
    text-transform: capitalize; text-align: right;
}
.dim-bar-track {
    flex: 1; height: 6px; border-radius: 3px;
    background: rgba(255,255,255,0.06);
    overflow: hidden;
}
.dim-bar-fill {
    height: 100%; border-radius: 3px;
    transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
}
.dim-score { width: 28px; text-align: left; font-weight: 600; font-size: 0.8rem; }

/* ── Content Boxes ────────────────────────────────────────────── */
.content-box {
    padding: 0.9rem 1.1rem; border-radius: var(--radius-sm);
    margin: 0.4rem 0; font-size: 0.9rem; line-height: 1.55;
}
.box-positive { background: var(--success-bg); border-left: 3px solid var(--success); }
.box-flaw     { background: var(--danger-bg); border-left: 3px solid var(--danger); }
.box-refactor { background: rgba(139,92,246,0.08); border-left: 3px solid var(--accent); }
.box-info     { background: var(--info-bg); border-left: 3px solid var(--info); }
.box-summary  {
    background: linear-gradient(135deg, rgba(30,35,50,0.8), rgba(26,35,50,0.6));
    border: 1px solid var(--border-default); border-radius: var(--radius-md);
    padding: 1.1rem 1.2rem; margin-top: 0.6rem;
}

/* ── Metric Cards ─────────────────────────────────────────────── */
.metric-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.8rem; margin: 1rem 0; }
.metric-card {
    background: var(--bg-card);
    backdrop-filter: blur(8px);
    border: 1px solid var(--border-default);
    border-radius: var(--radius-md);
    padding: 1rem 0.8rem; text-align: center;
    transition: border-color 0.3s ease, transform 0.2s ease;
}
.metric-card:hover {
    border-color: rgba(139,92,246,0.2);
    transform: translateY(-2px);
}
.metric-value {
    font-size: 1.8rem; font-weight: 800;
    background: linear-gradient(135deg, #C084FC, #818CF8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.metric-value.mono {
    font-family: var(--font-mono); font-size: 1.3rem;
    background: none; -webkit-text-fill-color: var(--text-primary);
}
.metric-label {
    font-size: 0.72rem; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: 0.06em; margin-top: 2px;
}

/* ── History Timeline ──────────────────────────────────────────── */
.history-item {
    background: var(--bg-card); border: 1px solid var(--border-subtle);
    border-radius: var(--radius-sm); padding: 0.7rem 1rem; margin: 0.35rem 0;
    font-size: 0.83rem; transition: border-color 0.2s;
}
.history-item:hover { border-color: var(--border-default); }
.history-dot {
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    margin-right: 6px;
}
.history-dot.review { background: #818CF8; }
.history-dot.pair   { background: #34D399; }

/* ── Expandable Panels ─────────────────────────────────────────── */
.streamlit-expanderHeader {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-default) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.88rem !important;
    transition: border-color 0.3s !important;
}
.streamlit-expanderHeader:hover {
    border-color: rgba(139,92,246,0.3) !important;
}

/* ── Code Blocks ──────────────────────────────────────────────── */
.stCodeBlock {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border-default) !important;
}
.stCodeBlock code { font-family: var(--font-mono) !important; }

/* ── Tabs ─────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.4rem;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    padding: 0.5rem 1rem;
    border-radius: var(--radius-sm);
    font-weight: 500; font-size: 0.88rem;
    color: var(--text-secondary);
    transition: all 0.2s;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(255,255,255,0.04);
    color: var(--text-primary);
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: rgba(139,92,246,0.12);
    color: #A78BFA;
}

/* ── Buttons ──────────────────────────────────────────────────── */
.stButton > button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    transition: all 0.2s !important;
    letter-spacing: -0.01em;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #7C3AED, #6366F1) !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(124,58,237,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 4px 16px rgba(124,58,237,0.5) !important;
    transform: translateY(-1px);
}

/* ── Sidebar ──────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #0B0F19 100%);
    border-right: 1px solid var(--border-default);
}
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label {
    font-weight: 500; font-size: 0.8rem; color: var(--text-secondary);
}

/* ── File Uploader ────────────────────────────────────────────── */
[data-testid="stFileUploader"] {
    border-radius: var(--radius-sm) !important;
}
[data-testid="stFileUploader"] section {
    border: 1px dashed var(--border-default) !important;
    border-radius: var(--radius-sm) !important;
    background: rgba(255,255,255,0.02) !important;
    transition: border-color 0.3s !important;
}
[data-testid="stFileUploader"]:hover section {
    border-color: rgba(139,92,246,0.3) !important;
}

/* ── Animations ───────────────────────────────────────────────── */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%      { opacity: 0.5; transform: scale(1.3); }
}
@keyframes shimmer {
    0% { background-position: -200px 0; }
    100% { background-position: calc(200px + 100%) 0; }
}

/* ── Responsive ───────────────────────────────────────────────── */
@media (max-width: 768px) {
    .metric-grid { grid-template-columns: repeat(2, 1fr); }
    .hero-stats { flex-wrap: wrap; gap: 0.8rem; }
    .dim-label { width: 80px; font-size: 0.75rem; }
}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# Hero Section
# ═══════════════════════════════════════════════════════════════════
def render_hero():
    st.markdown("""
    <div class="hero">
        <div class="hero-badge">
            <span class="dot"></span> AI-Powered Code Intelligence
        </div>
        <div class="hero-subtitle">
            Senior Architect-grade code analysis across 6 quality dimensions.
            Multi-provider support — OpenAI, Anthropic, Ollama — with live token streaming and cost tracking.
        </div>
        <div class="hero-stats">
            <div class="hero-stat"><span class="icon">&#9670;</span> <strong>6</strong> quality dimensions</div>
            <div class="hero-stat"><span class="icon">&#9654;</span> <strong>3</strong> LLM providers</div>
            <div class="hero-stat"><span class="icon">&#9776;</span> <strong>2-Pass</strong> deep review</div>
            <div class="hero-stat"><span class="icon">&#9672;</span> <strong>Demo</strong> mode ready</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# Score + Severity
# ═══════════════════════════════════════════════════════════════════
def render_score_badge(score: int):
    cls = "score-high" if score >= 8 else "score-mid" if score >= 4 else "score-low"
    st.markdown(f'<span class="score-badge {cls}">Score: {score}/10</span>', unsafe_allow_html=True)


def render_severity_badge(severity: str) -> str:
    cls = {"high": "sev-high", "medium": "sev-medium", "low": "sev-low"}.get(severity, "sev-medium")
    return f"<span class='sev-badge {cls}'>{severity}</span>"


# ═══════════════════════════════════════════════════════════════════
# Radar Chart — polished
# ═══════════════════════════════════════════════════════════════════
def render_radar_chart(dimension_scores: dict, title: str = "Code Quality Dimensions"):
    categories = list(dimension_scores.keys())
    values = list(dimension_scores.values())
    values.append(values[0])
    closed_cats = [c.capitalize() for c in categories] + [categories[0].capitalize()]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=closed_cats,
        fill="toself",
        fillcolor="rgba(139,92,246,0.2)",
        line=dict(color="#A78BFA", width=2.5, shape="spline"),
        marker=dict(size=5, color="#C084FC"),
        name=title,
        hovertemplate="<b>%{theta}</b><br>Score: %{r}/10<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True, range=[0, 10], tickvals=[2, 4, 6, 8, 10],
                tickfont=dict(color="#64748B", size=9),
                gridcolor="rgba(255,255,255,0.06)",
            ),
            angularaxis=dict(
                tickfont=dict(color="#94A3B8", size=10, family="Inter"),
                gridcolor="rgba(255,255,255,0.04)",
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=False,
        margin=dict(l=30, r=30, t=30, b=30),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=340,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ═══════════════════════════════════════════════════════════════════
# Dimension Bars (replaces plain text)
# ═══════════════════════════════════════════════════════════════════
def render_dimension_bars(dimension_scores: dict):
    colors = {
        "readability": "#34D399",
        "structure": "#818CF8",
        "maintainability": "#FBBF24",
        "security": "#F87171",
        "performance": "#38BDF8",
        "testability": "#A78BFA",
    }
    for dim, score in dimension_scores.items():
        color = colors.get(dim, "#94A3B8")
        pct = score * 10
        st.markdown(f"""
        <div class="dim-row">
            <span class="dim-label">{dim}</span>
            <div class="dim-bar-track">
                <div class="dim-bar-fill" style="width:{pct}%;background:{color};box-shadow:0 0 8px {color}40;"></div>
            </div>
            <span class="dim-score" style="color:{color}">{score}/10</span>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# Token Usage Display
# ═══════════════════════════════════════════════════════════════════
def render_usage(usage: TokenUsage):
    st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-card"><div class="metric-value mono">{usage.prompt_tokens:,}</div><div class="metric-label">Prompt Tokens</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-card"><div class="metric-value mono">{usage.completion_tokens:,}</div><div class="metric-label">Completion Tokens</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-card"><div class="metric-value mono">{usage.total_tokens:,}</div><div class="metric-label">Total Tokens</div></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="metric-card"><div class="metric-value mono">${usage.cost_usd:.4f}</div><div class="metric-label">Estimated Cost</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# Review Results — full render
# ═══════════════════════════════════════════════════════════════════
def render_review_results(review: CodeReviewOutput, language: str):
    render_score_badge(review.overall_score)

    col_dim, col_radar = st.columns([1, 1.1])
    with col_dim:
        st.markdown("#### Dimension Scores")
        render_dimension_bars(review.dimension_scores)
    with col_radar:
        render_radar_chart(review.dimension_scores)

    st.markdown("### &nbsp;")

    st.markdown("### Strengths")
    for note in review.positive_notes:
        st.markdown(f'<div class="content-box box-positive">{note}</div>', unsafe_allow_html=True)

    st.markdown("### Suggested Improvements")
    for i, imp in enumerate(review.improvements, 1):
        sev_html = render_severity_badge(imp.severity.value)
        with st.expander(f"#{i} &nbsp; [{imp.category.value.upper()}] &nbsp; {imp.issue[:72]}... &nbsp; {sev_html}", expanded=(i <= 2)):
            st.markdown(f"**Issue:** {imp.issue}")
            st.markdown(f"**Suggestion:** {imp.suggestion}")
            if imp.code_before and imp.code_after:
                col_a, col_b = st.columns(2)
                with col_a:
                    st.caption("Before")
                    st.code(imp.code_before, language=language.lower() if language else None)
                with col_b:
                    st.caption("After")
                    st.code(imp.code_after, language=language.lower() if language else None)

    st.markdown("### Summary")
    st.markdown(f'<div class="content-box box-summary">{review.summary}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# Pair Engineer Results — full render
# ═══════════════════════════════════════════════════════════════════
def render_pair_results(analysis: PairEngineerOutput, language: str):
    st.markdown("### What's Working")
    st.markdown(f'<div class="content-box box-positive">{analysis.positive_note}</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    cyc = analysis.complexity_metrics.cyclomatic_estimate
    cou = analysis.complexity_metrics.coupling_estimate
    cyc_dot = {"low": '<span style="color:#34D399;font-size:1.3rem;">&bull;</span>', "medium": '<span style="color:#FCD34D;font-size:1.3rem;">&bull;</span>', "high": '<span style="color:#F87171;font-size:1.3rem;">&bull;</span>'}.get(cyc, '<span style="color:#FCD34D;">&bull;</span>')
    cou_dot = {"low": '<span style="color:#34D399;font-size:1.3rem;">&bull;</span>', "medium": '<span style="color:#FCD34D;font-size:1.3rem;">&bull;</span>', "high": '<span style="color:#F87171;font-size:1.3rem;">&bull;</span>'}.get(cou, '<span style="color:#FCD34D;">&bull;</span>')
    c1.markdown(f'<div class="glass-card"><div class="metric-label">Cyclomatic</div><div style="font-size:1.5rem;font-weight:700;margin-top:4px;">{cyc_dot} {cyc.upper()}</div></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="glass-card"><div class="metric-label">Coupling</div><div style="font-size:1.5rem;font-weight:700;margin-top:4px;">{cou_dot} {cou.upper()}</div></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="glass-card"><div class="metric-label">Design Flaws</div><div style="font-size:1.5rem;font-weight:700;color:#F87171;margin-top:4px;">{len(analysis.design_flaws)}</div></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="glass-card"><div class="metric-label">Tests Proposed</div><div style="font-size:1.5rem;font-weight:700;color:#34D399;margin-top:4px;">{len(analysis.test_proposals)}</div></div>', unsafe_allow_html=True)

    if analysis.design_flaws:
        st.markdown("### Design Flaws")
        for flaw in analysis.design_flaws:
            st.markdown(f"""
<div class="content-box box-flaw">
<strong>{flaw.type.replace('_', ' ').title()}</strong> &nbsp;—&nbsp; <code>{flaw.location}</code><br>
<span style="color:#FCA5A5;">Risk:</span> {flaw.risk}<br>
<span style="color:#A78BFA;">Fix:</span> {flaw.fix}
</div>""", unsafe_allow_html=True)

    if analysis.test_proposals:
        st.markdown("### Test Proposals")
        for test in analysis.test_proposals:
            with st.expander(f"{test.test_type.upper()}: {test.test_name}"):
                st.markdown(f"<span style='color:#34D399;'>Catches:</span> {test.what_it_catches}", unsafe_allow_html=True)
                st.code(test.test_code, language="python")

    if analysis.refactoring_plan:
        st.markdown("### Refactoring Plan")
        for step in analysis.refactoring_plan:
            st.markdown(f"""
<div class="content-box box-refactor">
<strong>Step {step.step}</strong>: {step.action}<br>
<span style="color:#94A3B8;font-size:0.85rem;">{step.rationale}</span>
</div>""", unsafe_allow_html=True)

    st.markdown("### Summary")
    st.markdown(f'<div class="content-box box-summary">{analysis.summary}</div>', unsafe_allow_html=True)
