import json
import logging
from typing import Optional
from datetime import datetime, timezone

from src.schemas import CodeReviewOutput, PairEngineerOutput, TokenUsage
from src.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class ReviewService:
    def __init__(self, provider: BaseProvider):
        self.provider = provider
        self.history: list[dict] = []
        self.total_usage = TokenUsage()

    def review_code(self, code: str, language: str) -> dict:
        result, usage = self.provider.review_code(code, language, two_pass=True)
        self.total_usage.prompt_tokens += usage.prompt_tokens
        self.total_usage.completion_tokens += usage.completion_tokens
        self.total_usage.total_tokens += usage.total_tokens
        self.total_usage.cost_usd += usage.cost_usd

        entry = {
            "type": "review",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "language": language,
            "code_snippet": code[:200],
            "overall_score": result.overall_score,
            "improvements_count": len(result.improvements),
            "usage": usage,
        }
        self.history.append(entry)

        return {
            "result": result,
            "usage": usage,
        }

    def pair_engineer(self, code: str, language: str, focus: str, context: str) -> dict:
        result, usage = self.provider.pair_engineer(code, language, focus, context)
        self.total_usage.prompt_tokens += usage.prompt_tokens
        self.total_usage.completion_tokens += usage.completion_tokens
        self.total_usage.total_tokens += usage.total_tokens
        self.total_usage.cost_usd += usage.cost_usd

        entry = {
            "type": "pair",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "language": language,
            "code_snippet": code[:200],
            "flaws_count": len(result.design_flaws),
            "tests_count": len(result.test_proposals),
            "usage": usage,
        }
        self.history.append(entry)

        return {
            "result": result,
            "usage": usage,
        }


def export_review_markdown(review: CodeReviewOutput, language: str, usage: Optional[TokenUsage] = None) -> str:
    lines = [
        f"# Code Review Report",
        f"",
        f"**Language:** {language}  ",
        f"**Overall Score:** {review.overall_score}/10  ",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"",
    ]

    if usage:
        lines += [
            f"**Tokens Used:** {usage.total_tokens:,} (prompt: {usage.prompt_tokens:,}, completion: {usage.completion_tokens:,})  ",
            f"**Estimated Cost:** ${usage.cost_usd:.4f}",
            f"",
        ]

    lines += [
        f"---",
        f"",
        f"## Dimension Scores",
        f"",
        f"| Dimension | Score |",
        f"|-----------|-------|",
    ]
    for dim, score in review.dimension_scores.items():
        bar = "█" * score + "░" * (10 - score)
        lines.append(f"| {dim.capitalize()} | {bar} {score}/10 |")
    lines.append("")

    lines += ["## Strengths", ""]
    for note in review.positive_notes:
        lines.append(f"- {note}")
    lines.append("")

    lines += ["## Suggested Improvements", ""]
    for i, imp in enumerate(review.improvements, 1):
        lines += [
            f"### {i}. [{imp.category.upper()}] {imp.severity.upper()} — {imp.issue}",
            f"",
            f"**Suggestion:** {imp.suggestion}",
            f"",
            f"**Before:**",
            f"```{language.lower()}",
            imp.code_before,
            f"```",
            f"",
            f"**After:**",
            f"```{language.lower()}",
            imp.code_after,
            f"```",
            f"",
        ]

    lines += ["---", "", "## Summary", "", review.summary, ""]

    return "\n".join(lines)


def export_pair_markdown(analysis: PairEngineerOutput, language: str, usage: Optional[TokenUsage] = None) -> str:
    lines = [
        f"# Pair Engineer Analysis",
        f"",
        f"**Language:** {language}  ",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"",
    ]

    if usage:
        lines += [
            f"**Tokens Used:** {usage.total_tokens:,}  ",
            f"**Estimated Cost:** ${usage.cost_usd:.4f}",
            f"",
        ]

    lines += [
        f"---",
        f"",
        f"## Complexity Estimates",
        f"",
        f"- **Cyclomatic Complexity:** {analysis.complexity_metrics.cyclomatic_estimate.upper()}",
        f"- **Coupling:** {analysis.complexity_metrics.coupling_estimate.upper()}",
        f"",
        f"## Strength",
        f"",
        f"{analysis.positive_note}",
        f"",
    ]

    if analysis.design_flaws:
        lines += ["## Design Flaws", ""]
        for flaw in analysis.design_flaws:
            lines += [
                f"### {flaw.type.replace('_', ' ').title()} — `{flaw.location}`",
                f"",
                f"**Risk:** {flaw.risk}",
                f"",
                f"**Fix:** {flaw.fix}",
                f"",
            ]

    if analysis.test_proposals:
        lines += ["## Test Proposals", ""]
        for test in analysis.test_proposals:
            lines += [
                f"### {test.test_type.upper()}: {test.test_name}",
                f"",
                f"**Catches:** {test.what_it_catches}",
                f"",
                f"```{language.lower()}",
                test.test_code,
                f"```",
                f"",
            ]

    if analysis.refactoring_plan:
        lines += ["## Refactoring Plan", ""]
        for step in analysis.refactoring_plan:
            lines += [f"**Step {step.step}:** {step.action}", f"", f"*{step.rationale}*", f""]

    lines += ["---", "", "## Summary", "", analysis.summary, ""]

    return "\n".join(lines)
