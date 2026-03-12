from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    github_id: int = Field(unique=True, index=True)
    github_login: str
    email: Optional[str] = None
    access_token_enc: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Repository(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    github_repo_id: int = Field(unique=True, index=True)
    full_name: str
    owner: str
    name: str
    default_branch: str = 'main'
    webhook_active: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PullRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    repo_id: int = Field(foreign_key='repository.id', index=True)
    pr_number: int
    title: str
    author: str
    head_sha: str
    status: str = 'pending'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Review(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pr_id: int = Field(foreign_key='pullrequest.id', index=True)
    model_used: str
    tokens_used: int = 0
    duration_ms: int = 0
    summary: str = ''
    github_review_id: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReviewComment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    review_id: int = Field(foreign_key='review.id', index=True)
    file_path: str
    line: int
    body: str
    severity: str
    confidence: float
    category: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Feedback(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    comment_id: int = Field(foreign_key='reviewcomment.id', index=True)
    github_login: str
    rating: int
    created_at: datetime = Field(default_factory=datetime.utcnow)