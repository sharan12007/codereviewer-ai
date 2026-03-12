from services.diff_parser import Chunk

SYSTEM_PROMPT = '''You are a senior software engineer performing a code review.
Analyze the provided diff and return ONLY a JSON object with this exact structure:

{
  "summary": "One paragraph summary of the changes and key issues found.",
  "comments": [
    {
      "position": <integer --- diff position from the patch, starting at 1>,
      "body": "<clear explanation of the issue and how to fix it>",
      "severity": "<critical|warning|suggestion|info>",
      "category": "<bug|security|style|performance|logic|documentation>",
      "confidence": <float 0.0 to 1.0>
    }
  ]
}

Rules:
- Return ONLY the JSON object. No markdown. No explanation before or after.
- position must be an integer referencing the line position in the GitHub diff patch.
- If no issues found, return {"summary": "LGTM", "comments": []}
- Maximum 10 comments per chunk.
- confidence reflects how certain you are this is a real issue (not a false positive).
'''


def build_prompt(chunk: Chunk) -> str:
    return f'''Review this {chunk.language} code diff:

File: {chunk.file_path}
```diff
{chunk.lines}
```
'''