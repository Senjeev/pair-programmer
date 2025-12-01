import logging
from fastapi import APIRouter, HTTPException
from ..schemas import AutocompleteRequest, AutocompleteResponse
import re

router = APIRouter(prefix="/autocomplete", tags=["autocomplete"])
from ..constants import ALL_WORDS

logger = logging.getLogger(__name__)


@router.post("/", response_model=AutocompleteResponse)
def autocomplete(request: AutocompleteRequest):
    try:
        code = request.code or ""
        cursor = request.cursorPosition

        if cursor < 0 or cursor > len(code):
            return {"suggestion": ""}

        i = cursor - 1
        while i >= 0 and (code[i].isalnum() or code[i] == "_"):
            i -= 1

        prefix = code[i + 1 : cursor]

        if not prefix:
            return {"suggestion": ""}

        try:
            pattern = re.compile(rf"^{re.escape(prefix)}.*", re.IGNORECASE)
        except re.error:
            logger.exception("Regex compilation failed in autocomplete")
            return {"suggestion": ""}

        matches = [w for w in ALL_WORDS if pattern.match(w)]
        suggestion = matches[0] if matches else ""

        return {"suggestion": suggestion}

    except Exception:
        logger.exception("Unexpected error in autocomplete endpoint")
        raise HTTPException(500, "Unexpected server error")
