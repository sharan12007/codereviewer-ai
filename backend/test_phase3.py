import asyncio
from services.diff_parser import parse_diff_to_chunks
from services.prompt_engine import SYSTEM_PROMPT, build_prompt
from services.llm_client import LLMClient
from services.noise_filter import filter_comments

# ── TEST 1: diff_parser ──────────────────────────────────────────────
TEST_FILES = [
    {
        'filename': 'app/auth.py',
        'status': 'modified',
        'additions': 10,
        'deletions': 2,
        'patch': '''@@ -1,5 +1,10 @@
 import os
+import hashlib
 
 def login(username, password):
-    if password == "admin123":
+    query = f"SELECT * FROM users WHERE username = '{username}'"
+    hashed = hashlib.md5(password.encode()).hexdigest()
+    if hashed == get_hash(username):
         return True
+    return False
+
+def get_hash(username):
+    return "hardcoded_hash"
'''
    },
    {
        'filename': 'package-lock.json',
        'status': 'modified',
        'additions': 5,
        'deletions': 0,
        'patch': '@@ -1,3 +1,8 @@\n some lock content',
    },
    {
        'filename': 'utils/helper.py',
        'status': 'removed',
        'additions': 0,
        'deletions': 10,
        'patch': '',
    }
]

print("=" * 50)
print("TEST 1: diff_parser")
print("=" * 50)
chunks = parse_diff_to_chunks(TEST_FILES)
print(f"Total chunks: {len(chunks)}  (expected: 1 — package-lock.json and removed file skipped)")
for c in chunks:
    print(f"  file: {c.file_path} | lang: {c.language} | tokens: {c.token_count}")
assert len(chunks) == 1, "FAIL: expected 1 chunk"
assert chunks[0].file_path == 'app/auth.py', "FAIL: wrong file"
assert chunks[0].language == 'python', "FAIL: wrong language"
print("TEST 1 PASSED ✓\n")


# ── TEST 2: prompt_engine ────────────────────────────────────────────
print("=" * 50)
print("TEST 2: prompt_engine")
print("=" * 50)
prompt = build_prompt(chunks[0])
assert len(prompt) > 0, "FAIL: prompt is empty"
assert 'app/auth.py' in prompt, "FAIL: file path not in prompt"
assert 'python' in prompt, "FAIL: language not in prompt"
assert chunks[0].lines in prompt, "FAIL: diff not embedded in prompt"
print(f"Prompt length: {len(prompt)} chars")
print("TEST 2 PASSED ✓\n")


# ── TEST 3: llm_client ───────────────────────────────────────────────
print("=" * 50)
print("TEST 3: llm_client (real Gemini API call)")
print("=" * 50)

async def test_llm():
    llm = LLMClient()
    print(f"Provider: {llm.provider} | Model: {llm.get_model_name()}")

    # trivial test
    result = await llm.review(
        system='Return ONLY valid JSON. No markdown.',
        user='Return {"test": true}'
    )
    print(f"Trivial result: {result}")
    assert isinstance(result, dict), "FAIL: result is not a dict"
    print("Trivial call PASSED ✓")

    # real review test
    result2 = await llm.review(SYSTEM_PROMPT, build_prompt(chunks[0]))
    print(f"Review summary: {result2.get('summary', '')}")
    print(f"Comments found: {len(result2.get('comments', []))}")
    assert 'summary' in result2, "FAIL: no summary key"
    assert 'comments' in result2, "FAIL: no comments key"
    print("Real review call PASSED ✓")
    return result2

result = asyncio.run(test_llm())
print("TEST 3 PASSED ✓\n")


# ── TEST 4: noise_filter ─────────────────────────────────────────────
print("=" * 50)
print("TEST 4: noise_filter")
print("=" * 50)

mock_comments = []
severities = ['critical', 'warning', 'suggestion', 'info']
categories = ['bug', 'security', 'style', 'performance']

for i in range(25):
    mock_comments.append({
        'position': i % 10 + 1,
        'body': f'Issue {i}',
        'severity': severities[i % 4],
        'category': categories[i % 4],
        'confidence': round(0.4 + (i % 7) * 0.1, 1),
        'file_path': 'app/auth.py'
    })

filtered = filter_comments(mock_comments, max_total=20)
print(f"Input: 25 comments → Output: {len(filtered)} comments")
assert len(filtered) <= 20, "FAIL: more than 20 comments returned"
for c in filtered:
    assert c['confidence'] >= 0.6, f"FAIL: low confidence comment slipped through: {c['confidence']}"
print("All confidence >= 0.6 ✓")
print("Count <= 20 ✓")
print("TEST 4 PASSED ✓\n")

print("=" * 50)
print("ALL PHASE 3 TESTS PASSED ✓")
print("=" * 50)