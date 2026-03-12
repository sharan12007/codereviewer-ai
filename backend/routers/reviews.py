import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from database import get_session
from models import Review, ReviewComment, Feedback, PullRequest

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/reviews")
async def list_reviews(
    repo_id: int = Query(None),
    pr_number: int = Query(None),
    limit: int = Query(20, le=100),
    offset: int = Query(0),
    session: Session = Depends(get_session)
):
    query = select(Review)
    if repo_id or pr_number:
        pr_query = select(PullRequest)
        if repo_id:
            pr_query = pr_query.where(PullRequest.repo_id == repo_id)
        if pr_number:
            pr_query = pr_query.where(PullRequest.pr_number == pr_number)
        prs = session.exec(pr_query).all()
        pr_ids = [p.id for p in prs]
        if not pr_ids:
            return []
        query = query.where(Review.pr_id.in_(pr_ids))

    query = query.offset(offset).limit(limit)
    reviews = session.exec(query).all()
    return reviews


@router.get("/reviews/{review_id}")
async def get_review(review_id: int, session: Session = Depends(get_session)):
    review = session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    comments = session.exec(
        select(ReviewComment).where(ReviewComment.review_id == review_id)
    ).all()

    return {
        "review": review,
        "comments": comments
    }


@router.post("/feedback/{comment_id}")
async def post_feedback(
    comment_id: int,
    rating: int = Query(..., description="1 = helpful, -1 = not helpful"),
    github_login: str = Query(...),
    session: Session = Depends(get_session)
):
    comment = session.get(ReviewComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    if rating not in (1, -1):
        raise HTTPException(status_code=400, detail="Rating must be 1 or -1")

    feedback = Feedback(
        comment_id=comment_id,
        github_login=github_login,
        rating=rating,
    )
    session.add(feedback)
    session.commit()
    return {"status": "ok"}