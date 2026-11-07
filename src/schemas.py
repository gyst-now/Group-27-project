from typing import Literal
from pydantic import BaseModel, Field, field_validator
from src.config import URLS

class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    catalog_year: Literal['2026-27'] = '2026-27'

    @field_validator('question')
    @classmethod
    def clean(cls, value):
        if not value.strip():
            raise ValueError('Enter a question')
        return value.strip()

class GroundedAnswer(BaseModel):
    supported: bool
    answer: str
    evidence_ids: list[str] = Field(default_factory=list)

class Citation(BaseModel):
    label: str
    title: str
    url: str
    course_code: str | None = None
    excerpt: str

class ChatResponse(BaseModel):
    answer: str
    status: Literal['answered', 'insufficient_evidence', 'error']
    citations: list[Citation] = Field(default_factory=list)
    request_id: str
    latency_ms: int
    retrieved_sources: list[dict] = Field(default_factory=list)
