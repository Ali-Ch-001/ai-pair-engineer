# AI Pair Engineer & Code Reviewer

**[github.com/Ali-Ch-001/ai-pair-engineer](https://github.com/Ali-Ch-001/ai-pair-engineer)**

An interactive, production-grade Streamlit application that combines automated code review with pair-programming intelligence. Built as a demonstration of applied AI engineering, prompt architecture, and full-stack prototyping for the screening challenge.

---

## Overview

This tool performs two distinct but complementary functions:

**Code Review** &mdash; Evaluates source code across six quality dimensions (readability, structure, maintainability, security, performance, testability) and returns severity-ranked, actionable improvements with before/after code diffs.

**Pair Engineer** &mdash; Analyzes code as a collaborative co-pilot: detects design flaws (tight coupling, race conditions, missing error handling, SQL injection, N+1 queries, etc.), proposes executable pytest-level tests, and builds a dependency-ordered refactoring plan with cyclomatic and coupling complexity estimates.

Both functions are backed by a fully transparent prompt architecture visible in the Prompt Lab tab. The system supports three LLM providers (OpenAI, Anthropic, Ollama) behind a unified interface, with token-level cost tracking, streaming responses, and a demo mode that works without any API key.

---

## Architecture

### Design Philosophy

The codebase follows clean architecture principles: separation of concerns, dependency inversion via abstract base classes, and a service layer that orchestrates provider calls, history tracking, and export logic. The Streamlit UI layer is thin &mdash; all business logic lives in `src/`.

### Provider Abstraction

```
BaseProvider (ABC)
  |-- OpenAIProvider      (gpt-4o, gpt-4o-mini, gpt-4-turbo)
  |-- AnthropicProvider   (Claude Sonnet 4, Claude 3.5 Sonnet)
  |-- OllamaProvider      (codellama, any local model)
```

Each provider implements the same interface: `review_code()`, `review_code_stream()`, `pair_engineer()`, `pair_engineer_stream()`. The factory method `BaseProvider.create("openai")` returns the appropriate implementation. This makes adding new providers a single-file effort.

### Two-Pass Review System

The OpenAI and Anthropic providers implement a two-pass review strategy:
1. **Pass 1 (Quick Scan):** A lightweight prompt asks the model to identify only the top 3 issues. This costs ~200 tokens and runs in <1 second.
2. **Pass 2 (Deep Review):** The scan results are injected as context into the full review prompt, giving the model a "first look" at the code before producing the complete structured analysis.

This approach consistently produces more focused, higher-quality reviews than a single pass, at minimal additional cost.

### Prompt Architecture

All prompts follow a strict hierarchy:
- **Role Anchoring** &mdash; "Principal Software Engineer & Solutions Architect, 15+ years, Fortune 500"
- **Philosophy** &mdash; 5 principles governing tone and priorities
- **Evaluation Dimensions** &mdash; Scored 1-10 with domain-specific criteria
- **Output Schema** &mdash; Complete JSON schema enforced via `response_format`
- **Few-Shot Example** &mdash; One curated example demonstrating exact format expectations

The JSON output constraint (`response_format={"type": "json_object"}`) transforms probabilistic text into deterministic, programmatically consumable structured data &mdash; essentially a strongly-typed function signature for AI.

---

## Project Structure

```
ai-pair-engineer/
├── app.py                         # Streamlit entry point (thin UI orchestration)
├── config.py                      # Pydantic Settings from .env / environment
├── .env.example                   # Template with all configurable variables
├── .gitignore
├── Dockerfile                     # Production container with healthcheck
├── docker-compose.yml             # App + optional Ollama service
├── Makefile                       # run, install, test, lint, docker-*
├── requirements.txt
├── src/
│   ├── providers/
│   │   ├── base.py                # Abstract BaseProvider with factory method
│   │   ├── openai_provider.py     # Two-pass review, streaming, cost calc
│   │   ├── anthropic_provider.py  # Claude integration with message API
│   │   └── ollama_provider.py     # Local model via REST API
│   ├── schemas.py                 # Pydantic v2 models (7 output types)
│   ├── prompts.py                 # Production prompts with few-shot examples
│   ├── services.py                # ReviewService, Markdown export, history
│   ├── code_parser.py             # Heuristic + Pygments language detection
│   └── ui/
│       └── components.py          # CSS system, radar chart, result renderers
├── examples/
│   └── sample_code.py             # 4 curated code samples with known issues
└── tests/
    └── test_core.py               # 12 tests: schemas, parser, export, usage
```

---

## Key Features (Senior Architect Perspective)

### 1. Multi-Provider with Unified Interface
Switch between OpenAI, Anthropic, or local Ollama models with one dropdown. Each provider tracks its own pricing for accurate cost estimation. No code changes needed to add a fourth provider.

### 2. Two-Pass Deep Review
The quick-scan-first approach improves review quality by giving the model preliminary context before the full analysis. This is implemented transparently in the provider layer and costs < 10% extra tokens.

### 3. Six-Dimensional Quality Scoring
Every review produces scores for Readability, Structure, Maintainability, Security, Performance, and Testability. These feed directly into the interactive Plotly radar chart on the Dashboard.

### 4. Token-Level Cost Tracking
Every API call logs prompt tokens, completion tokens, and estimated cost in USD. Session-level aggregation appears in the sidebar and Dashboard. This is production thinking &mdash; you can't manage what you don't measure.

### 5. Full Prompt Transparency
The Prompt Lab tab exposes every word of every system prompt. It explains the prompt engineering techniques used (role anchoring, few-shot learning, CoT, instruction hierarchy) so reviewers understand exactly how the AI arrives at its output.

### 6. Demo Mode
The entire application works without any API key. Pre-crafted analysis demonstrates the output format, UI, and prompt architecture. Perfect for evaluation without sharing credentials.

### 7. Streaming Responses
Token-by-token streaming shows the AI's output building in real time, similar to ChatGPT. Toggleable for users who prefer instant results.

### 8. Production Infrastructure
Dockerfile with healthcheck, docker-compose with optional Ollama service, Makefile for common operations, and environment-based configuration via Pydantic Settings.

---

## Quick Start

```bash
# Clone and install
cd ai-pair-engineer
cp .env.example .env          # Edit with your API keys (optional)
pip install -r requirements.txt

# Run
make run                      # or: streamlit run app.py
```

Open `http://localhost:8501`. Select a sample from the sidebar to explore in demo mode, or enter an API key for live AI analysis.

### Docker

```bash
make docker-build
make docker-up
```

To include a local Ollama instance for entirely offline analysis:

```bash
docker compose --profile ollama up -d
docker exec -it $(docker ps -qf name=ollama) ollama pull codellama:13b
```

---

## Screenshot Guide for Submission

For the best visual impact, follow this sequence:

1. **Hero + Code Review Results** &mdash; Load "Tightly Coupled Order Processor" from the sidebar, click "Review Code", scroll to capture: gradient title, 6-dimension bars, radar chart, score badge, and 3+ improvements with before/after code columns.

2. **Pair Engineer Results** &mdash; Switch to the Pair Engineer tab, click "Pair Review", capture: complexity gauge cards, design flaw cards with risk/fix details, test proposals with executable code, and the 4-step refactoring plan.

3. **Dashboard** &mdash; After running both analyses, the Dashboard tab shows: 4 metric cards (analyses, tokens, cost, avg score), a side-by-side dimension breakdown with radar chart, and a session history timeline.

4. **Prompt Lab** &mdash; Expand the "System Prompt" section to show the full prompt architecture, then scroll to the "Techniques Used" section showing the 6 prompt engineering strategies.

5. **Sidebar** &mdash; Capture the provider selector, API key input, model picker, and sample selector to demonstrate the multi-provider architecture.

### Tips
- Use full-screen mode (F11) for clean captures
- The demo mode analysis is pre-crafted to be visually rich and detailed
- For live AI results, enter an OpenAI or Anthropic API key for real streaming output

---

## Prompt Engineering Techniques Demonstrated

| Technique | Implementation |
|-----------|---------------|
| **Role Anchoring** | "Principal Engineer & Solutions Architect, 15+ years, Fortune 500" |
| **Two-Pass Review** | Quick scan identifies top issues, deep review uses them as context |
| **Structured Output** | `response_format={"type": "json_object"}` with explicit JSON schema |
| **Few-Shot Learning** | One curated example demonstrates exact tone, format, and specificity |
| **Chain of Thought** | "Think step-by-step" instruction before structured output |
| **Instruction Hierarchy** | Philosophy -> Dimensions -> Format -> Example (layered) |
| **Blast-Radius Prioritization** | Severity driven by production impact, not line count |
| **Production Grounding** | Every design flaw requires a specific production failure scenario |
| **Dependency-Ordered Planning** | Refactoring steps sequenced to unlock each other |

---

## Technical Decisions & Rationale

**Why Streamlit?** Zero-config Python UI deployment. Free cloud hosting. Instant iteration during the 45-minute build window. Future-proof: Streamlit apps are just Python scripts that can be refactored into FastAPI backends.

**Why Pydantic Settings?** Type-safe configuration management. Environment variables, `.env` files, and secrets management in one pattern. Prevents runtime config errors.

**Why Abstract Base Provider?** Open/Closed Principle. Adding a new provider (Google Gemini, Cohere, Mistral) requires one new file implementing the interface. Zero changes to existing code.

**Why Two-Pass Review?** Single-pass LLM reviews tend to be generic. Giving the model a preliminary scan dramatically improves specificity because it has "seen" the code once before the deep analysis.

**Why 6 Dimensions?** Code quality is multidimensional. A single score is misleading. Breaking into readability/structure/maintainability/security/performance/testability gives the developer actionable targets and feeds the radar visualization.
