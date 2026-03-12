from dataclasses import dataclass
from typing import Optional
import tiktoken
from github import Github

LANG_MAP = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
    '.jsx': 'javascript', '.tsx': 'typescript', '.go': 'go',
    '.rs': 'rust', '.java': 'java', '.cs': 'csharp',
    '.cpp': 'cpp', '.c': 'c', '.rb': 'ruby', '.php': 'php',
    '.swift': 'swift', '.kt': 'kotlin', '.sh': 'bash',
    '.yaml': 'yaml', '.yml': 'yaml', '.json': 'json',
    '.sql': 'sql', '.html': 'html', '.css': 'css',
}

SKIP_EXTENSIONS = {
    '.lock', '.sum', '.mod', '-lock.json', '.svg',
    '.png', '.jpg', '.gif', '.pdf', '.ico'
}

@dataclass
class Chunk:
    file_path: str
    language: str
    lines: str
    start_line: int
    end_line: int
    token_count: int


def detect_language(filename: str) -> str:
    import os
    _, ext = os.path.splitext(filename.lower())
    return LANG_MAP.get(ext, 'plaintext')


def should_skip_file(filename: str, status: str, additions: int) -> bool:
    if status == 'removed':
        return True
    if additions == 0:
        return True
    for ext in SKIP_EXTENSIONS:
        if filename.lower().endswith(ext):
            return True
    return False


def count_tokens(text: str) -> int:
    encoding = tiktoken.get_encoding('cl100k_base')
    return len(encoding.encode(text))


def split_patch_by_hunks(patch: str) -> list[str]:
    hunks = []
    current = []
    for line in patch.splitlines(keepends=True):
        if line.startswith('@@') and current:
            hunks.append(''.join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        hunks.append(''.join(current))
    return hunks


def fetch_pr_files(repo_full_name: str, pr_number: int, installation_token: str) -> list[dict]:
    g = Github(installation_token)
    repo = g.get_repo(repo_full_name)
    pr = repo.get_pull(pr_number)
    files = pr.get_files()

    result = []
    for f in files:
        result.append({
            'filename': f.filename,
            'status': f.status,
            'additions': f.additions,
            'deletions': f.deletions,
            'patch': getattr(f, 'patch', None) or '',
        })
    return result


def parse_diff_to_chunks(files: list[dict], max_tokens: int = 3000) -> list[Chunk]:
    encoding = tiktoken.get_encoding('cl100k_base')
    chunks = []

    for f in files:
        filename = f['filename']
        status = f['status']
        additions = f['additions']
        patch = f.get('patch', '') or ''

        if should_skip_file(filename, status, additions):
            continue

        if not patch:
            continue

        language = detect_language(filename)
        token_count = len(encoding.encode(patch))

        if token_count <= max_tokens:
            lines = patch.splitlines()
            chunks.append(Chunk(
                file_path=filename,
                language=language,
                lines=patch,
                start_line=1,
                end_line=len(lines),
                token_count=token_count,
            ))
        else:
            hunks = split_patch_by_hunks(patch)
            current_lines = []
            current_tokens = 0
            start_line = 1

            for hunk in hunks:
                hunk_tokens = len(encoding.encode(hunk))

                if current_tokens + hunk_tokens > max_tokens and current_lines:
                    combined = ''.join(current_lines)
                    line_count = len(combined.splitlines())
                    chunks.append(Chunk(
                        file_path=filename,
                        language=language,
                        lines=combined,
                        start_line=start_line,
                        end_line=start_line + line_count - 1,
                        token_count=current_tokens,
                    ))
                    start_line = start_line + line_count
                    current_lines = [hunk]
                    current_tokens = hunk_tokens
                else:
                    current_lines.append(hunk)
                    current_tokens += hunk_tokens

            if current_lines:
                combined = ''.join(current_lines)
                line_count = len(combined.splitlines())
                chunks.append(Chunk(
                    file_path=filename,
                    language=language,
                    lines=combined,
                    start_line=start_line,
                    end_line=start_line + line_count - 1,
                    token_count=current_tokens,
                ))

    return chunks