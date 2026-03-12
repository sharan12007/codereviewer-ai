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


def post_review(token: str, repo_full_name: str, pr_number: int,
                comments: list[dict], summary: str) -> int:
    g = Github(token)
    repo = g.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)

    gh_comments = [
        {
            'path': c['file_path'],
            'position': c['position'],
            'body': c['body']
        }
        for c in comments
        if c.get('position') and c.get('file_path')
    ]

    review = pr.create_review(
        body=summary,
        event='COMMENT',
        comments=gh_comments
    )
    logger.info(f"Posted review {review.id} to PR #{pr_number}")
    return review.id