import streamlit as st
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

from config import settings
from src.schemas import CodeReviewOutput, PairEngineerOutput, TokenUsage
from src.providers.base import BaseProvider
from src.services import ReviewService, export_review_markdown, export_pair_markdown
from src.code_parser import detect_language, count_lines
from src.ui.components import (
    inject_css,
    render_hero,
    render_score_badge,
    render_radar_chart,
    render_dimension_bars,
    render_usage,
    render_review_results,
    render_pair_results,
)
from src.prompts import (
    get_review_system_prompt,
    get_review_user_prompt,
    get_pair_system_prompt,
    get_pair_user_prompt,
)
from examples.sample_code import SAMPLES

logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
logger = logging.getLogger(__name__)

st.set_page_config(page_title="AI Pair Engineer & Code Reviewer", page_icon=None, layout="wide")
inject_css()

# ── Session State ──────────────────────────────────────────────────
for key, default in {
    "review_result": None,
    "review_usage": None,
    "pair_result": None,
    "pair_usage": None,
    "service": None,
    "sample_code": "",
    "sample_lang": "Python",
    "sample_context": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## :material/settings: Configuration")

    st.markdown("### :material/key: API Provider")
    provider_choice = st.selectbox(
        "Provider",
        ["openai", "anthropic", "ollama"],
        index=0,
        help="Select which LLM provider to use. Configure keys in .env or enter below.",
    )

    if provider_choice == "openai":
        api_key = st.text_input(
            "OpenAI API Key",
            type="password",
            value=settings.openai_api_key if settings.openai_api_key else "",
            help="Overrides OPENAI_API_KEY from .env",
        )
        model = st.selectbox("Model", ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"], index=0, key="openai_model_select")
    elif provider_choice == "anthropic":
        api_key = st.text_input(
            "Anthropic API Key",
            type="password",
            value=settings.anthropic_api_key if settings.anthropic_api_key else "",
            help="Overrides ANTHROPIC_API_KEY from .env",
        )
        model = st.selectbox(
            "Model",
            ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022"],
            index=0,
            key="anthropic_model_select",
        )
    else:
        api_key = ""
        model = st.text_input("Ollama Model", value=settings.ollama_model, key="ollama_model_input")
        st.caption(f"Endpoint: {settings.ollama_base_url}")

    has_api_key = bool(api_key or (provider_choice == "openai" and settings.openai_api_key) or (provider_choice == "anthropic" and settings.anthropic_api_key))

    st.divider()

    st.markdown("### :material/description: Sample Code")
    sample_name = st.selectbox("Load a sample", ["— Choose or paste your own —"] + list(SAMPLES.keys()))

    st.divider()

    st.markdown("### :material/bar_chart: Session Stats")
    if st.session_state.get("service") and st.session_state.service.history:
        svc = st.session_state.service
        st.caption(f"Reviews: {len([h for h in svc.history if h['type'] == 'review'])} | Pairs: {len([h for h in svc.history if h['type'] == 'pair'])}")
        st.caption(f"Tokens: {svc.total_usage.total_tokens:,} | Cost: ${svc.total_usage.cost_usd:.4f}")

    st.divider()
    st.markdown(
        "<small>Built with Streamlit, OpenAI, Anthropic, Ollama</small>",
        unsafe_allow_html=True,
    )

# ── Load Sample ────────────────────────────────────────────────────
if sample_name != "— Choose or paste your own —":
    sample = SAMPLES[sample_name]
    st.session_state.sample_code = sample["code"]
    st.session_state.sample_lang = sample["language"]
    st.session_state.sample_context = sample.get("context", "")

# ── Provider Initialization ────────────────────────────────────────
def get_service():
    if st.session_state.service is not None:
        return st.session_state.service

    try:
        effective_key = api_key or (
            settings.openai_api_key if provider_choice == "openai"
            else settings.anthropic_api_key if provider_choice == "anthropic"
            else None
        )
        effective_model = model

        if provider_choice == "openai" and effective_key:
            from src.providers.openai_provider import OpenAIProvider
            provider = OpenAIProvider(api_key=effective_key, model=effective_model)
        elif provider_choice == "anthropic" and effective_key:
            from src.providers.anthropic_provider import AnthropicProvider
            provider = AnthropicProvider(api_key=effective_key, model=effective_model)
        elif provider_choice == "ollama":
            from src.providers.ollama_provider import OllamaProvider
            provider = OllamaProvider(base_url=settings.ollama_base_url, model=effective_model)
        else:
            return None

        svc = ReviewService(provider)
        st.session_state.service = svc
        return svc
    except Exception as e:
        st.error(f"Failed to initialize provider: {e}")
        return None


# ── Main UI ────────────────────────────────────────────────────────
render_hero()

tab_review, tab_pair, tab_dashboard, tab_prompts = st.tabs([
    "Code Review", "Pair Engineer", "Dashboard", "Prompt Lab"
])

# ═══════════════════════════════════════════════════════════════════
# TAB 1: Code Review
# ═══════════════════════════════════════════════════════════════════
with tab_review:
    col_left, col_right = st.columns([3, 1])

    with col_left:
        code = st.text_area(
            "Paste your code below, or upload a file",
            value=st.session_state.get("sample_code", ""),
            height=280,
            key="review_code",
            placeholder="def process(data): ...",
        )

        uploaded_file = st.file_uploader(
            "Or upload a source file",
            type=["py", "js", "ts", "tsx", "jsx", "java", "go", "rs", "rb", "php", "sql", "html", "css", "sh", "yaml", "json", "txt"],
            key="review_upload",
        )
        if uploaded_file is not None:
            code = uploaded_file.read().decode("utf-8", errors="replace")
            st.caption(f"Loaded: {uploaded_file.name} ({count_lines(code)} lines)")

    with col_right:
        detected_lang = detect_language(code) if code.strip() else "Python"
        language = st.text_input("Language", value=detected_lang, key="review_lang")
        st.metric("Lines", count_lines(code))
        streaming = st.checkbox("Stream response", value=settings.enable_streaming, key="review_stream")
        review_btn = st.button("Review Code", type="primary", use_container_width=True, key="btn_review")

    if review_btn:
        if not code.strip():
            st.warning("Paste some code first, or select a sample from the sidebar.")
        else:
            svc = get_service()

            if svc is None:
                st.info("**Demo mode** &mdash; enter an API key in the sidebar or configure `.env` for AI-powered reviews.", icon=":material/info:")
                from src.services import export_review_markdown

                review = CodeReviewOutput(
                    overall_score=7,
                    dimension_scores={"readability": 6, "structure": 5, "maintainability": 6, "security": 4, "performance": 7, "testability": 5},
                    positive_notes=[
                        "The code follows a clear logical flow with well-scoped function boundaries.",
                        "Variable names are generally descriptive and convey intent.",
                        "The error handling strategy (where present) follows a consistent pattern.",
                    ],
                    improvements=[
                        {
                            "category": "readability",
                            "severity": "medium",
                            "line_range": [1, 3],
                            "issue": "Missing function and module-level docstrings",
                            "suggestion": "Add docstrings describing parameters, return values, side effects, and module purpose. This helps onboard new developers and enables auto-generated documentation.",
                            "code_before": "def process(data):\n    results = []\n    for item in data:",
                            "code_after": "def process(data: list[dict]) -> list[dict]:\n    \"\"\"Transform input records by normalizing date fields and filtering invalid entries.\n\n    Args:\n        data: List of raw record dicts with expected keys: id, created_at, status.\n\n    Returns:\n        List of normalized record dicts with added 'processed_at' timestamp.\n    \"\"\"\n    results = []\n    for item in data:",
                        },
                        {
                            "category": "structure",
                            "severity": "high",
                            "line_range": [1, 30],
                            "issue": "Missing input validation and error handling at I/O boundaries",
                            "suggestion": "Add type validation at function boundaries. Wrap external calls (database, network, file I/O) in try/except blocks with specific exception types. Invalid input should fail fast with a clear error message.",
                            "code_before": "def load_all_configs(directory):\n    result = {}\n    for filename in os.listdir(directory):",
                            "code_after": 'def load_all_configs(directory: str) -> dict[str, dict]:\n    """Load all .cfg files from a directory into a nested dict.\n\n    Raises:\n        FileNotFoundError: If directory does not exist.\n        ValueError: If a config file has malformed syntax.\n    """\n    if not os.path.isdir(directory):\n        raise FileNotFoundError(f"Config directory not found: {directory}")\n    result = {}\n    for filename in os.listdir(directory):',
                        },
                        {
                            "category": "maintainability",
                            "severity": "medium",
                            "line_range": [1, 30],
                            "issue": "Magic values and hardcoded configuration",
                            "suggestion": "Extract magic numbers, file paths, and credentials into named constants or a configuration object. This makes the code environment-aware and reduces the blast radius of a single change.",
                            "code_before": 'server = smtplib.SMTP("smtp.company.com", 587)\nserver.login("orders@company.com", "pass123")',
                            "code_after": 'SMTP_HOST = os.getenv("SMTP_HOST", "smtp.company.com")\nSMTP_PORT = int(os.getenv("SMTP_PORT", "587"))\nSMTP_USER = os.getenv("SMTP_USER")\nSMTP_PASS = os.getenv("SMTP_PASS")\n\nserver = smtplib.SMTP(SMTP_HOST, SMTP_PORT)\nserver.login(SMTP_USER, SMTP_PASS)',
                        },
                    ],
                    summary="The code is well-structured at the function level but needs hardening for production. Start by adding docstrings and type hints for readability, then implement input validation and error handling to prevent silent failures. Finally, extract environment-specific configuration to make the code portable across dev/staging/prod.",
                )
                usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, cost_usd=0)

                st.session_state.review_result = review
                st.session_state.review_usage = usage
            else:
                with st.spinner("Analyzing code across 6 dimensions..."):
                    if streaming:
                        placeholder = st.empty()
                        full = ""
                        try:
                            for token in svc.provider.review_code_stream(code, language):
                                full += token
                                placeholder.markdown(f"```json\n{full[:1500]}\n```")
                            placeholder.empty()
                            result_dict = json.loads(full)
                            review = CodeReviewOutput(**result_dict)
                            usage = TokenUsage()
                        except Exception as e:
                            st.error(f"Streaming failed: {e}. Falling back to non-streaming.")
                            result = svc.review_code(code, language)
                            review = result["result"]
                            usage = result["usage"]
                    else:
                        result = svc.review_code(code, language)
                        review = result["result"]
                        usage = result["usage"]

                st.session_state.review_result = review
                st.session_state.review_usage = usage

            # Export button
            if st.session_state.review_result:
                md = export_review_markdown(st.session_state.review_result, language, st.session_state.review_usage)
                st.download_button(
                    "Export as Markdown",
                    md,
                    file_name=f"code-review-{datetime.now().strftime('%Y%m%d-%H%M')}.md",
                    mime="text/markdown",
                )

    # Show cached result
    if st.session_state.review_result:
        st.divider()
        render_review_results(st.session_state.review_result, language)
        if st.session_state.review_usage and st.session_state.review_usage.total_tokens > 0:
            with st.expander("Token Usage & Cost", expanded=False):
                render_usage(st.session_state.review_usage)


# ═══════════════════════════════════════════════════════════════════
# TAB 2: Pair Engineer
# ═══════════════════════════════════════════════════════════════════
with tab_pair:
    col_left, col_right = st.columns([3, 1])

    with col_left:
        pair_code = st.text_area(
            "Paste your code",
            value=st.session_state.get("sample_code", ""),
            height=240,
            key="pair_code",
            placeholder="class OrderProcessor: ...",
        )
        context = st.text_area(
            "Context (optional) — describe the system, constraints, or what you're trying to achieve",
            value=st.session_state.get("sample_context", ""),
            height=70,
            key="pair_context",
            placeholder="This is a legacy payment module handling 10k transactions/day...",
        )

        uploaded_pair = st.file_uploader(
            "Or upload a source file",
            type=["py", "js", "ts", "tsx", "jsx", "java", "go", "rs", "rb", "php", "sql", "html", "css", "sh", "yaml", "json", "txt"],
            key="pair_upload",
        )
        if uploaded_pair is not None:
            pair_code = uploaded_pair.read().decode("utf-8", errors="replace")
            st.caption(f"Loaded: {uploaded_pair.name} ({count_lines(pair_code)} lines)")

    with col_right:
        pair_lang = detect_language(pair_code) if pair_code.strip() else "Python"
        pair_language = st.text_input("Language", value=pair_lang, key="pair_language")
        focus = st.selectbox("Focus area", ["All", "Design Flaws", "Testing", "Refactoring", "Complexity"])
        st.metric("Lines", count_lines(pair_code))
        pair_streaming = st.checkbox("Stream response", value=settings.enable_streaming, key="pair_stream")
        pair_btn = st.button("Pair Review", type="primary", use_container_width=True, key="btn_pair")

    if pair_btn:
        if not pair_code.strip():
            st.warning("Paste some code first.")
        else:
            svc = get_service()

            if svc is None:
                st.info("**Demo mode** &mdash; enter an API key for AI-powered analysis.", icon=":material/info:")

                analysis = PairEngineerOutput(
                    design_flaws=[
                        {
                            "type": "tight_coupling",
                            "location": "main processing function",
                            "risk": "Database writes, email sending, and business logic share the same function. An email failure could roll back a valid database transaction in production.",
                            "fix": "Apply Single Responsibility Principle. Extract persistence, notification, and business logic into separate service classes behind interfaces. Use event-driven wiring.",
                        },
                        {
                            "type": "missing_error_handling",
                            "location": "I/O boundaries (file reads, network calls)",
                            "risk": "FileNotFoundError, socket.timeout, or malformed JSON will crash with an unhelpful traceback. In a scheduled job, failures go undetected until someone notices stale data.",
                            "fix": "Add try/except blocks around all I/O with specific exception types. Log with context. Either retry with exponential backoff or fail gracefully with an alert.",
                        },
                        {
                            "type": "mutable_global_state",
                            "location": "module-level settings/config object",
                            "risk": "Module-level mutable state creates hidden dependencies between functions. Tests interfere with each other. Concurrent access in a threaded server causes race conditions.",
                            "fix": "Convert to an immutable configuration object (dataclass with frozen=True) passed explicitly. Makes data flow explicit and eliminates shared mutable state.",
                        },
                    ],
                    test_proposals=[
                        {
                            "test_type": "unit",
                            "test_name": "test_process_handles_empty_input_gracefully",
                            "test_code": "def test_process_handles_empty_input():\n    \"\"\"Empty input should return empty output, not error.\"\"\"\n    result = process([])\n    assert result == []\n\n\ndef test_process_raises_on_missing_required_key():\n    \"\"\"Malformed input should raise a clear ValueError.\"\"\"\n    with pytest.raises(ValueError, match=\"Missing required key\"):\n        process([{\"id\": 1}])  # missing 'created_at'",
                            "what_it_catches": "Catches edge-case crashes when data has unexpected shape. Ensures clear error messages instead of cryptic KeyError tracebacks.",
                        },
                        {
                            "test_type": "integration",
                            "test_name": "test_end_to_end_persistence_with_test_database",
                            "test_code": "@pytest.fixture\ndef test_db():\n    conn = sqlite3.connect(\":memory:\")\n    conn.execute(\"CREATE TABLE orders (id TEXT, email TEXT, total REAL)\")\n    yield conn\n    conn.close()\n\n\ndef test_order_persists_correctly(test_db):\n    processor = OrderProcessor(test_db)\n    order = {\"id\": \"ord-1\", \"items\": [{\"sku\": \"A\", \"price\": 10.0, \"qty\": 2}]}\n    processor.process(order)\n    row = test_db.execute(\"SELECT * FROM orders WHERE id = ?\", [\"ord-1\"]).fetchone()\n    assert row[\"total\"] == 20.0",
                            "what_it_catches": "Verifies the full pipeline (validation → calculation → persistence) against a real database. Catches schema mismatches and calculation bugs.",
                        },
                    ],
                    refactoring_plan=[
                        {"step": 1, "action": "Extract a Config dataclass to hold all environment-specific values", "rationale": "Eliminates magic values and global mutable state. Makes the code environment-aware. Testing becomes trivial — just pass a different Config."},
                        {"step": 2, "action": "Split monolithic function into Validator → Transformer → Persister pipeline stages", "rationale": "Each stage becomes independently testable and replaceable. Follows SRP. Enables parallel processing if needed later."},
                        {"step": 3, "action": "Introduce an EventEmitter after successful persistence for side effects", "rationale": "Completely decouples core logic from notifications, inventory updates, analytics. A failed email no longer blocks an order."},
                        {"step": 4, "action": "Add structured logging with correlation IDs at each pipeline stage", "rationale": "Enables distributed tracing. When an order fails, you trace it through every stage without grepping through logs."},
                    ],
                    complexity_metrics={"cyclomatic_estimate": "medium", "coupling_estimate": "high"},
                    positive_note="The code has a clear pipeline structure — input → process → output — which is the correct mental model for data transformation. Function decomposition shows good intuition for separation of concerns.",
                    summary="The biggest production risk is tight coupling between business logic, I/O, and side effects. Start by extracting configuration to eliminate magic values, then split the pipeline into testable stages. This sets the foundation for proper error handling and observability without a full rewrite.",
                )
                usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, cost_usd=0)

                st.session_state.pair_result = analysis
                st.session_state.pair_usage = usage
            else:
                with st.spinner("Pair programming — analyzing architecture, risks, and test strategy..."):
                    if pair_streaming:
                        placeholder = st.empty()
                        full = ""
                        try:
                            for token in svc.provider.pair_engineer_stream(pair_code, pair_language, focus, context):
                                full += token
                                placeholder.markdown(f"```json\n{full[:1500]}\n```")
                            placeholder.empty()
                            result_dict = json.loads(full)
                            analysis = PairEngineerOutput(**result_dict)
                            usage = TokenUsage()
                        except Exception as e:
                            st.error(f"Streaming failed: {e}. Falling back to non-streaming.")
                            result = svc.pair_engineer(pair_code, pair_language, focus, context)
                            analysis = result["result"]
                            usage = result["usage"]
                    else:
                        result = svc.pair_engineer(pair_code, pair_language, focus, context)
                        analysis = result["result"]
                        usage = result["usage"]

                st.session_state.pair_result = analysis
                st.session_state.pair_usage = usage

            if st.session_state.pair_result:
                md = export_pair_markdown(st.session_state.pair_result, pair_language, st.session_state.pair_usage)
                st.download_button(
                    "Export as Markdown",
                    md,
                    file_name=f"pair-engineering-{datetime.now().strftime('%Y%m%d-%H%M')}.md",
                    mime="text/markdown",
                )

    if st.session_state.pair_result:
        st.divider()
        render_pair_results(st.session_state.pair_result, pair_language)
        if st.session_state.pair_usage and st.session_state.pair_usage.total_tokens > 0:
            with st.expander("Token Usage & Cost", expanded=False):
                render_usage(st.session_state.pair_usage)


# ═══════════════════════════════════════════════════════════════════
# TAB 3: Dashboard
# ═══════════════════════════════════════════════════════════════════
with tab_dashboard:
    svc = st.session_state.get("service")

    if svc and svc.history:
        reviews = [h for h in svc.history if h["type"] == "review"]
        pairs = [h for h in svc.history if h["type"] == "pair"]
        total = len(reviews) + len(pairs)
        avg_score = sum(r["overall_score"] for r in reviews) / len(reviews) if reviews else 0

        st.markdown('<div class="metric-grid">', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><div class="metric-value">{total}</div><div class="metric-label">Analyses</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><div class="metric-value mono">{svc.total_usage.total_tokens:,}</div><div class="metric-label">Tokens Used</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><div class="metric-value mono">${svc.total_usage.cost_usd:.4f}</div><div class="metric-label">Est. Cost</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="metric-card"><div class="metric-value">{avg_score:.1f}</div><div class="metric-label">Avg. Score</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.review_result:
            col_left, col_right = st.columns([1, 1])
            with col_left:
                st.markdown("#### Dimension Breakdown")
                render_dimension_bars(st.session_state.review_result.dimension_scores)
            with col_right:
                st.markdown("#### Quality Radar")
                render_radar_chart(st.session_state.review_result.dimension_scores)

        st.markdown("#### Session History")
        for entry in reversed(svc.history[-20:]):
            ts = entry["timestamp"][:19].replace("T", " ")
            dot_cls = "review" if entry["type"] == "review" else "pair"
            lang = entry.get("language", "?")
            snippet = entry.get("code_snippet", "")[:80]
            if entry["type"] == "review":
                detail = f"Score: {entry['overall_score']}/10 &middot; {entry['improvements_count']} improvements"
            else:
                detail = f"{entry['flaws_count']} flaws &middot; {entry['tests_count']} tests"
            st.markdown(
                f'<div class="history-item"><span class="history-dot {dot_cls}"></span><strong>{ts}</strong> &middot; {lang} &middot; {detail}<br><small>{snippet}...</small></div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("Run a code review or pair engineer analysis to populate the dashboard.", icon=":material/dashboard:")
        st.markdown("#### Dimension Radar — Preview")
        col_p1, col_p2 = st.columns([1, 1])
        with col_p1:
            preview = {"readability": 5, "structure": 5, "maintainability": 5, "security": 5, "performance": 5, "testability": 5}
            render_dimension_bars(preview)
        with col_p2:
            render_radar_chart(preview)


# ═══════════════════════════════════════════════════════════════════
# TAB 4: Prompt Lab
# ═══════════════════════════════════════════════════════════════════
with tab_prompts:
    st.markdown("### :material/biotech: Prompt Lab")
    st.caption("Full transparency into the AI's instructions. See how few-shot examples, role anchoring, and structured output constraints drive consistent, actionable results.")

    prompt_tab = st.radio("Select prompt", ["Code Review", "Pair Engineer"], horizontal=True)

    if prompt_tab == "Code Review":
        st.markdown("#### System Prompt")
        st.caption("Establishes persona, evaluation dimensions (scored 1–10), output schema, and a curated few-shot example.")

        demo_code = "def calc(a,b,c):\n    x=a+b\n    if c: return x*c\n    return x"
        with st.expander("System Prompt", expanded=False):
            st.code(get_review_system_prompt(), language="markdown")

        st.markdown("#### Example User Message")
        with st.expander("User Message", expanded=False):
            st.code(get_review_user_prompt(demo_code, "Python"), language="markdown")

        st.markdown("#### Techniques Used")
        st.markdown("""
<div class="positive-box">
<strong>1. Role Anchoring</strong> — "Principal Engineer & Solutions Architect, 15+ years, Fortune 500" establishes credibility.<br/>
<strong>2. Two-Pass Review</strong> — Quick scan identifies top issues first, then deep review with full context (implemented in provider layer).<br/>
<strong>3. Six-Dimension Scoring</strong> — Readability, Structure, Maintainability, Security, Performance, Testability — feeds the radar chart.<br/>
<strong>4. Few-Shot Example</strong> — One curated example demonstrates exact tone, format, specificity, and before/after code expectations.<br/>
<strong>5. Instruction Hierarchy</strong> — Philosophy → Dimensions → Format → Example — each layer builds on the previous.<br/>
<strong>6. Blast-Radius Prioritization</strong> — Severity is driven by production impact, not line count.
</div>
""", unsafe_allow_html=True)

    else:
        st.markdown("#### System Prompt")
        st.caption("Collaborative co-pilot that surfaces risks, proposes tests, plans refactors, and estimates complexity.")

        demo_pair = "class OrderProcessor:\n    def __init__(self, db):\n        self.db = db\n    def process(self, order):\n        self.db.save(order)\n        self.send_email(order.email, 'Confirmed')\n        self.update_stock(order.items)"
        with st.expander("System Prompt", expanded=False):
            st.code(get_pair_system_prompt("All"), language="markdown")

        st.markdown("#### Example User Message")
        with st.expander("User Message", expanded=False):
            st.code(get_pair_user_prompt(demo_pair, "Python", "Legacy e-commerce backend"), language="markdown")

        st.markdown("#### Techniques Used")
        st.markdown("""
<div class="positive-box">
<strong>1. Co-Pilot Framing</strong> — "You are not a critic — you are a co-pilot" sets collaborative, constructive tone.<br/>
<strong>2. Production-Scenario Grounding</strong> — Every risk must include a specific production failure scenario, preventing vague advice.<br/>
<strong>3. Dependency-Ordered Refactoring</strong> — Steps are sequenced so Step 1 unlocks Step 2, not creates new blockers.<br/>
<strong>4. Domain Taxonomy</strong> — Enumerated flaw types (tight_coupling, god_object, race_condition, n_plus_one, etc.) guide precise terminology.<br/>
<strong>5. Context Injection</strong> — Optional developer context lets the model tailor advice to real constraints (legacy, scale, timeline).<br/>
<strong>6. Complexity Estimation</strong> — Cyclomatic and coupling estimates provide quick architectural health signals.
</div>
""", unsafe_allow_html=True)

    st.divider()
    st.caption("**Architecture Insight:** Prompt engineering is the API contract between developers and LLMs. Well-structured prompts with enforced output schemas transform probabilistic text generation into deterministic, programmatically consumable results &mdash; think of them as strongly-typed function signatures for AI.")
