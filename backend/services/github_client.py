import logging
from github import Github, GithubIntegration
from config import settings

logger = logging.getLogger(__name__)


def get_installation_token(installation_id: int) -> str:
    with open(settings.GITHUB_PRIVATE_KEY_PATH) as f:
        private_key = f.read()
    gi = GithubIntegration(settings.GITHUB_APP_ID, private_key)
    token = gi.get_access_token(installation_id)
    return token.token


def build_review_body(comments: list[dict], summary: str) -> str:
    """Build a markdown review body with all comments embedded."""
    lines = [f"## AI Code Review\n\n{summary}\n"]

    if comments:
        lines.append("\n---\n### Issues Found\n")
        for i, c in enumerate(comments, 1):
            severity = c.get("severity", "info").upper()
            category = c.get("category", "general")
            file_path = c.get("file_path", "unknown")
            position = c.get("position", "?")
            body = c.get("body", "")
            confidence = int(c.get("confidence", 0) * 100)

            emoji = {
                "CRITICAL": "🔴",
                "WARNING": "🟡",
                "SUGGESTION": "🔵",
                "INFO": "⚪"
            }.get(severity, "⚪")

            lines.append(
                f"{i}. {emoji} **[{severity}]** `{file_path}` line ~{position} "
                f"— _{category}_ ({confidence}% confidence)\n\n   {body}\n"
            )

    return "\n".join(lines)


def post_review(token: str, repo_full_name: str, pr_number: int,
                comments: list[dict], summary: str) -> int:
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)

    # Build inline comments with valid positions only
    gh_comments = [
        {
            'path': c['file_path'],
            'position': c['position'],
            'body': f"**[{c.get('severity','info').upper()}]** {c.get('body','')}"
        }
        for c in comments
        if c.get('position') and c.get('file_path')
    ]

    # Strategy 1: Try with inline comments
    if gh_comments:
        try:
            review = pr.create_review(
                body=summary,
                event='COMMENT',
                comments=gh_comments
            )
            logger.info(f"Posted review {review.id} with {len(gh_comments)} inline comments to PR #{pr_number}")
            return review.id
        except Exception as e:
            logger.warning(f"Inline comments failed ({e}), falling back to body-only review")

    # Strategy 2: Post everything in the review body (no inline comments)
    full_body = build_review_body(comments, summary)
    try:
        review = pr.create_review(
            body=full_body,
            event='COMMENT',
            comments=[]
        )
        logger.info(f"Posted body-only review {review.id} to PR #{pr_number}")
        return review.id
    except Exception as e:
        logger.error(f"Body-only review also failed: {e}")
        raise