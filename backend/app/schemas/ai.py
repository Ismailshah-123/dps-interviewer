from pydantic import BaseModel, Field

class Evidence(BaseModel):
    segment_sequence: int | None = None
    start_seconds: float | None = None
    end_seconds: float | None = None
    quote: str | None = None

class StructuredSummary(BaseModel):
    interview_overview: str | None = None
    parent_guardian_statements: list[str] = Field(default_factory=list)
    student_statements: list[str] = Field(default_factory=list)
    educational_background: list[str] = Field(default_factory=list)
    interests_and_activities: list[str] = Field(default_factory=list)
    school_expectations: list[str] = Field(default_factory=list)
    interviewer_documented_observations: list[str] = Field(default_factory=list)
    important_topics: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    unclear_or_missing_information: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
