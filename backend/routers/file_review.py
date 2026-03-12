import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.diff_parser import parse_diff_to_chunks, detect_language
from services.prompt_engine import SYSTEM_PROMPT, build_prompt
from services.llm_client import LLMClient
from services.noise_filter import filter_comments

logger = logging.getLogger(__name__)
router = APIRouter()


class FileReviewRequest(BaseModel):
    file_path: str
    content: str
    language: Optional[str] = None
    context: Optional[str] = "code review"


@router.post("/review/file")
async def review_file(request: FileReviewRequest):
    try:
        language = request.language or detect_language(request.file_path)

        # Build a fake diff from raw file content
        lines = request.content.splitlines()
        patch_lines = [f"+{line}" for line in lines]
        fake_patch = "@@ -0,0 +1,{} @@\n".format(len(lines)) + "\n".join(patch_lines)

        fake_files = [{
            "filename": request.file_path,
            "status": "modified",
            "additions": len(lines),
            "deletions": 0,
            "patch": fake_patch,
        }]

        chunks = parse_diff_to_chunks(fake_files)

        if not chunks:
            return {
                "review_id": None,
                "comments": [],
                "summary": "No reviewable content found.",
                "model_used": "none",
                "tokens_used": 0
            }

        llm = LLMClient()
        all_comments = []
        summary = ""

        for chunk in chunks:
            prompt = build_prompt(chunk)
            result = await llm.review(SYSTEM_PROMPT, prompt)
            chunk_comments = result.get("comments", [])
            for c in chunk_comments:
                c["file_path"] = chunk.file_path
            all_comments.extend(chunk_comments)
            if result.get("summary"):
                summary = result["summary"]

        filtered = filter_comments(all_comments)

        return {
            "review_id": None,
            "comments": filtered,
            "summary": summary,
            "model_used": llm.get_model_name(),
            "tokens_used": sum(c.get("token_count", 0) for c in filtered)
        }

    except Exception as e:
        logger.error(f"File review failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))