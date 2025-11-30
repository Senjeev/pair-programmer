from fastapi import APIRouter
from ..schemas import AutocompleteRequest, AutocompleteResponse
import re
router = APIRouter(prefix="/autocomplete", tags=["autocomplete"])
from ..constants import ALL_WORDS



@router.post("/", response_model=AutocompleteResponse)
def autocomplete(request: AutocompleteRequest):
    code = request.code
    cursor = request.cursorPosition
    i = cursor - 1
    while i >= 0 and (code[i].isalnum() or code[i] == "_"):
        i -= 1
    prefix = code[i+1:cursor]

    if not prefix:
        return {"suggestion": ""}

    try:
        pattern = re.compile(rf"^{re.escape(prefix)}.*", re.IGNORECASE)
    except re.error:
        return {"suggestion": ""}

    matches = [w for w in ALL_WORDS if pattern.match(w)]
    suggestion = matches[0] if matches else ""
    return {"suggestion": suggestion}
