import pytest
from src.schemas import CodeReviewOutput, PairEngineerOutput, TokenUsage, Improvement, Severity, ReviewCategory
from src.code_parser import detect_language, count_lines
from src.services import export_review_markdown, export_pair_markdown


class TestSchemas:
    def test_code_review_output_validates(self):
        review = CodeReviewOutput(
            overall_score=7,
            dimension_scores={"readability": 6, "structure": 5, "maintainability": 6, "security": 4, "performance": 7, "testability": 5},
            positive_notes=["Good structure"],
            improvements=[
                Improvement(
                    category=ReviewCategory.READABILITY,
                    severity=Severity.MEDIUM,
                    line_range=[1, 3],
                    issue="Missing docstring",
                    suggestion="Add a docstring",
                    code_before="def foo(): pass",
                    code_after='def foo():\n    """Does something."""\n    pass',
                )
            ],
            summary="Fix docstrings first.",
        )
        assert review.overall_score == 7
        assert len(review.improvements) == 1
        assert review.dimension_scores["readability"] == 6

    def test_pair_engineer_output_validates(self):
        analysis = PairEngineerOutput(
            design_flaws=[{"type": "tight_coupling", "location": "main()", "risk": "Hard to test", "fix": "Extract interface"}],
            test_proposals=[{"test_type": "unit", "test_name": "test_foo", "test_code": "def test_foo(): pass", "what_it_catches": "Bugs"}],
            refactoring_plan=[{"step": 1, "action": "Extract", "rationale": "SRP"}],
            complexity_metrics={"cyclomatic_estimate": "low", "coupling_estimate": "medium"},
            positive_note="Clean interface.",
            summary="Good start.",
        )
        assert len(analysis.design_flaws) == 1
        assert analysis.complexity_metrics.cyclomatic_estimate == "low"

    def test_overall_score_bounds(self):
        with pytest.raises(Exception):
            CodeReviewOutput(overall_score=0)
        with pytest.raises(Exception):
            CodeReviewOutput(overall_score=11)


class TestCodeParser:
    def test_detect_python(self):
        assert detect_language("def foo():\n    pass") == "Python"
        assert detect_language("import os\nfrom pathlib import Path") == "Python"

    def test_detect_javascript(self):
        assert detect_language("const fn = () => 42;") == "JavaScript"
        assert detect_language("function hello() { return 1; }") == "JavaScript"

    def test_detect_typescript(self):
        assert detect_language("const x: number = 1") == "TypeScript"
        assert detect_language("interface User { name: string }") == "TypeScript"

    def test_detect_sql(self):
        assert detect_language("SELECT * FROM users WHERE id = 1") == "SQL"

    def test_count_lines(self):
        assert count_lines("line1\nline2\nline3") == 3
        assert count_lines("") == 0


class TestExport:
    def test_export_review_markdown(self):
        review = CodeReviewOutput(
            overall_score=8,
            dimension_scores={"readability": 7, "structure": 8, "maintainability": 7, "security": 6, "performance": 8, "testability": 7},
            positive_notes=["Clean code"],
            improvements=[],
            summary="Looks good.",
        )
        md = export_review_markdown(review, "Python")
        assert "# Code Review Report" in md
        assert "**Overall Score:** 8/10" in md
        assert "Clean code" in md

    def test_export_pair_markdown(self):
        analysis = PairEngineerOutput(
            complexity_metrics={"cyclomatic_estimate": "medium", "coupling_estimate": "low"},
            positive_note="Solid architecture.",
            summary="Good work.",
        )
        md = export_pair_markdown(analysis, "TypeScript")
        assert "# Pair Engineer Analysis" in md
        assert "Solid architecture" in md


class TestTokenUsage:
    def test_token_usage_defaults(self):
        usage = TokenUsage()
        assert usage.prompt_tokens == 0
        assert usage.cost_usd == 0.0

    def test_token_usage_fields(self):
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150, cost_usd=0.002)
        assert usage.total_tokens == 150
        assert usage.cost_usd == 0.002
