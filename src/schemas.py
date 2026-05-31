from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from dataclasses import dataclass


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ReviewCategory(str, Enum):
    READABILITY = "readability"
    STRUCTURE = "structure"
    MAINTAINABILITY = "maintainability"
    SECURITY = "security"
    PERFORMANCE = "performance"
    TESTABILITY = "testability"


class Improvement(BaseModel):
    category: ReviewCategory
    severity: Severity
    line_range: List[int] = Field(description="[start_line, end_line]")
    issue: str
    suggestion: str
    code_before: str
    code_after: str


class CodeReviewOutput(BaseModel):
    overall_score: int = Field(ge=1, le=10)
    dimension_scores: dict = Field(default_factory=lambda: {
        "readability": 0,
        "structure": 0,
        "maintainability": 0,
        "security": 0,
        "performance": 0,
        "testability": 0,
    })
    positive_notes: List[str] = Field(default_factory=list)
    improvements: List[Improvement] = Field(default_factory=list)
    summary: str = ""


class DesignFlaw(BaseModel):
    type: str = Field(description="tight_coupling, god_object, race_condition, etc.")
    location: str
    risk: str
    fix: str


class TestProposal(BaseModel):
    test_type: str = Field(description="unit, integration, edge_case, regression")
    test_name: str
    test_code: str
    what_it_catches: str


class RefactoringStep(BaseModel):
    step: int
    action: str
    rationale: str


class ComplexityMetrics(BaseModel):
    cyclomatic_estimate: str = "medium"
    coupling_estimate: str = "medium"


class PairEngineerOutput(BaseModel):
    design_flaws: List[DesignFlaw] = Field(default_factory=list)
    test_proposals: List[TestProposal] = Field(default_factory=list)
    refactoring_plan: List[RefactoringStep] = Field(default_factory=list)
    complexity_metrics: ComplexityMetrics = Field(default_factory=ComplexityMetrics)
    positive_note: str = ""
    summary: str = ""


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
